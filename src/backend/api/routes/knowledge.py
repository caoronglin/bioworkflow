"""知识库管理路由"""

import os
import shutil
from datetime import datetime, timezone
from typing import List, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from pydantic import BaseModel
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.database import get_db
from backend.models.knowledge import Document, DocumentCategory, DocumentStatus, SearchQuery

router = APIRouter()

# 上传文件存储目录
UPLOAD_DIR = "uploads/documents"
os.makedirs(UPLOAD_DIR, exist_ok=True)


class DocumentCreate(BaseModel):
    title: str
    content: str
    category: Optional[str] = None
    tags: List[str] = []


class DocumentUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None


class DocumentResponse(BaseModel):
    id: str
    title: str
    content: str
    category: Optional[str]
    tags: List[str]
    status: str
    view_count: int
    download_count: int
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class SearchResult(BaseModel):
    document_id: str
    title: str
    content: str
    score: float
    relevance: float


class AIQuery(BaseModel):
    question: str
    use_context: bool = True
    max_results: int = 5


@router.get("/documents", response_model=List[DocumentResponse])
async def list_documents(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    category: Optional[str] = None,
    status: Optional[str] = None,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """
    获取知识库中的文档列表

    - **skip**: 跳过的记录数
    - **limit**: 返回的最大记录数
    - **category**: 按分类筛选
    - **status**: 按状态筛选
    - **search**: 搜索关键词（标题和内容）
    """
    query = select(Document).order_by(desc(Document.created_at))

    if category:
        query = query.where(Document.category == category)

    if status:
        query = query.where(Document.status == DocumentStatus(status))

    if search:
        # 简单的文本搜索，使用 LIKE
        search_pattern = f"%{search}%"
        query = query.where(
            (Document.title.ilike(search_pattern)) |
            (Document.content.ilike(search_pattern))
        )

    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    documents = result.scalars().all()

    return [
        DocumentResponse(
            id=d.id,
            title=d.title,
            content=d.content[:500] + "..." if len(d.content) > 500 else d.content,
            category=d.category,
            tags=d.tags or [],
            status=d.status.value,
            view_count=d.view_count,
            download_count=d.download_count,
            created_at=d.created_at.isoformat() if d.created_at else "",
            updated_at=d.updated_at.isoformat() if d.updated_at else "",
        )
        for d in documents
    ]


@router.post("/documents", response_model=DocumentResponse)
async def create_document(
    doc: DocumentCreate,
    created_by: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """
    创建新的知识库文档

    - **title**: 文档标题
    - **content**: 文档内容
    - **category**: 分类
    - **tags**: 标签
    """
    document = Document(
        id=str(uuid4()),
        title=doc.title,
        content=doc.content,
        category=doc.category,
        tags=doc.tags,
        status=DocumentStatus.PENDING,
        created_by=created_by,
        view_count=0,
        download_count=0,
    )

    db.add(document)
    await db.commit()
    await db.refresh(document)

    return DocumentResponse(
        id=document.id,
        title=document.title,
        content=document.content,
        category=document.category,
        tags=document.tags or [],
        status=document.status.value,
        view_count=document.view_count,
        download_count=document.download_count,
        created_at=document.created_at.isoformat() if document.created_at else "",
        updated_at=document.updated_at.isoformat() if document.updated_at else "",
    )


@router.get("/documents/{doc_id}", response_model=dict)
async def get_document(
    doc_id: str,
    db: AsyncSession = Depends(get_db),
):
    """获取特定文档的详细内容"""
    result = await db.execute(select(Document).where(Document.id == doc_id))
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(status_code=404, detail="文档不存在")

    # 增加查看次数
    document.view_count += 1
    await db.commit()

    return document.to_dict()


@router.put("/documents/{doc_id}")
async def update_document(
    doc_id: str,
    doc: DocumentUpdate,
    db: AsyncSession = Depends(get_db),
):
    """更新文档内容"""
    result = await db.execute(select(Document).where(Document.id == doc_id))
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(status_code=404, detail="文档不存在")

    # 更新字段
    if doc.title is not None:
        document.title = doc.title
    if doc.content is not None:
        document.content = doc.content
    if doc.category is not None:
        document.category = doc.category
    if doc.tags is not None:
        document.tags = doc.tags

    document.updated_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(document)

    return {"message": "文档已更新", "doc_id": doc_id}


@router.delete("/documents/{doc_id}")
async def delete_document(
    doc_id: str,
    db: AsyncSession = Depends(get_db),
):
    """删除文档"""
    result = await db.execute(select(Document).where(Document.id == doc_id))
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(status_code=404, detail="文档不存在")

    # 如果有文件，删除文件
    if document.file_path and os.path.exists(document.file_path):
        os.remove(document.file_path)

    await db.delete(document)
    await db.commit()

    return {"message": "文档已删除", "doc_id": doc_id}


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    category: Optional[str] = None,
    created_by: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """
    上传文档文件

    支持 markdown、txt、pdf 等格式
    """
    # 检查文件类型
    allowed_extensions = {".md", ".txt", ".pdf", ".doc", ".docx", ".json", ".yaml", ".yml"}
    file_ext = os.path.splitext(file.filename)[1].lower()

    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件类型: {file_ext}。支持的类型: {', '.join(allowed_extensions)}"
        )

    # 保存文件
    file_id = str(uuid4())
    safe_filename = f"{file_id}{file_ext}"
    file_path = os.path.join(UPLOAD_DIR, safe_filename)

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件保存失败: {e}")
    finally:
        file.file.close()

    # 读取文件内容（文本文件）
    content = ""
    if file_ext in {".md", ".txt", ".json", ".yaml", ".yml"}:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception:
            pass

    # 创建文档记录
    document = Document(
        id=file_id,
        title=file.filename,
        content=content,
        category=category,
        file_path=file_path,
        file_type=file_ext[1:] if file_ext else None,
        file_size=os.path.getsize(file_path),
        status=DocumentStatus.PENDING,
        created_by=created_by,
        view_count=0,
        download_count=0,
    )

    db.add(document)
    await db.commit()
    await db.refresh(document)

    return {
        "message": "文件已上传",
        "document_id": file_id,
        "filename": file.filename,
        "size": document.file_size,
    }


@router.post("/search", response_model=List[SearchResult])
async def search_knowledge_base(
    query: str,
    category: Optional[str] = None,
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    """
    搜索知识库

    - **query**: 搜索关键词
    - **category**: 按分类筛选
    - **limit**: 返回的最大结果数
    """
    # 记录搜索查询
    search_query = SearchQuery(
        id=str(uuid4()),
        query=query,
        filters={"category": category} if category else None,
    )
    db.add(search_query)

    # 构建搜索查询
    sql_query = select(Document).where(Document.status == DocumentStatus.INDEXED)

    if category:
        sql_query = sql_query.where(Document.category == category)

    # 简单的文本搜索
    search_pattern = f"%{query}%"
    sql_query = sql_query.where(
        (Document.title.ilike(search_pattern)) |
        (Document.content.ilike(search_pattern))
    )

    sql_query = sql_query.limit(limit)
    result = await db.execute(sql_query)
    documents = result.scalars().all()

    # 更新搜索结果计数
    search_query.results_count = len(documents)
    await db.commit()

    # 计算相关度分数（简单的基于匹配次数）
    results = []
    for doc in documents:
        title_matches = doc.title.lower().count(query.lower())
        content_matches = doc.content.lower().count(query.lower())
        score = title_matches * 2 + content_matches * 0.5
        relevance = min(score / 10, 1.0)  # 归一化到 0-1

        results.append(SearchResult(
            document_id=doc.id,
            title=doc.title,
            content=doc.content[:300] + "..." if len(doc.content) > 300 else doc.content,
            score=score,
            relevance=relevance,
        ))

    # 按相关度排序
    results.sort(key=lambda x: x.relevance, reverse=True)

    return results


@router.post("/ai-query", response_model=dict)
async def query_with_ai(
    request: AIQuery,
    db: AsyncSession = Depends(get_db),
):
    """
    使用 AI 查询知识库

    根据自然语言问题在知识库中搜索相关内容并提供答案

    - **question**: 用户问题
    - **use_context**: 是否使用检索上下文
    - **max_results**: 最多返回的相关文档数
    """
    # 记录查询
    search_query = SearchQuery(
        id=str(uuid4()),
        query=request.question,
        used_ai=True,
    )
    db.add(search_query)
    await db.commit()

    # 搜索相关文档
    search_pattern = f"%{request.question}%"
    query = (
        select(Document)
        .where(Document.status == DocumentStatus.INDEXED)
        .where(
            (Document.title.ilike(search_pattern)) |
            (Document.content.ilike(search_pattern))
        )
        .limit(request.max_results)
    )
    result = await db.execute(query)
    documents = result.scalars().all()

    # 构建上下文
    sources = []
    context_parts = []
    for doc in documents:
        sources.append({
            "id": doc.id,
            "title": doc.title,
            "category": doc.category,
        })
        context_parts.append(f"【{doc.title}】\n{doc.content[:500]}")

    context = "\n\n".join(context_parts)

    # TODO: 调用 AI 服务生成答案
    # 这里使用模拟答案
    answer = f"基于知识库中的 {len(sources)} 篇文档，我为您总结如下：\n\n"
    if sources:
        answer += f"相关内容涉及以下主题：{', '.join([s['title'] for s in sources[:3]])}等。\n\n"
        answer += "建议您查看具体文档以获取更详细的信息。"
    else:
        answer += "抱歉，在知识库中没有找到与您问题直接相关的内容。"

    # 更新查询记录
    search_query.results_count = len(sources)
    search_query.ai_response = answer
    await db.commit()

    return {
        "question": request.question,
        "answer": answer,
        "sources": sources,
        "confidence": 0.85 if sources else 0.3,
        "context_used": request.use_context,
    }


@router.get("/categories")
async def list_categories(
    db: AsyncSession = Depends(get_db),
):
    """获取所有可用的文档分类"""
    result = await db.execute(
        select(DocumentCategory).order_by(DocumentCategory.name)
    )
    categories = result.scalars().all()

    return {
        "categories": [
            {
                "id": c.id,
                "name": c.name,
                "description": c.description,
                "parent_id": c.parent_id,
            }
            for c in categories
        ]
    }


@router.get("/stats")
async def get_knowledge_base_stats(
    db: AsyncSession = Depends(get_db),
):
    """获取知识库统计信息"""
    # 文档总数
    doc_count_result = await db.execute(select(func.count(Document.id)))
    total_documents = doc_count_result.scalar() or 0

    # 按状态统计
    status_result = await db.execute(
        select(Document.status, func.count(Document.id))
        .group_by(Document.status)
    )
    status_counts = {str(status): count for status, count in status_result.all()}

    # 分类统计
    category_result = await db.execute(
        select(Document.category, func.count(Document.id))
        .group_by(Document.category)
    )
    category_counts = {cat or "未分类": count for cat, count in category_result.all()}

    # 最近更新时间
    last_update_result = await db.execute(
        select(Document).order_by(desc(Document.updated_at)).limit(1)
    )
    last_doc = last_update_result.scalar_one_or_none()

    return {
        "total_documents": total_documents,
        "status_distribution": status_counts,
        "category_distribution": category_counts,
        "last_updated": last_doc.updated_at.isoformat() if last_doc else None,
        "indexed": bool(status_counts.get("indexed", 0)),
    }
