"""知识库模型"""

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import JSON, DateTime, Enum as SQLEnum, ForeignKey, String, Text, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .user import User


class DocumentStatus(str, Enum):
    """文档状态"""
    PENDING = "pending"
    PROCESSING = "processing"
    INDEXED = "indexed"
    FAILED = "failed"
    ARCHIVED = "archived"


class DocumentCategory(Base):
    """文档分类"""

    __tablename__ = "document_categories"

    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    parent_id: Mapped[str | None] = mapped_column(ForeignKey("document_categories.id"), nullable=True)

    # 关系
    parent: Mapped["DocumentCategory | None"] = relationship("DocumentCategory", remote_side="DocumentCategory.id", backref="children")
    documents: Mapped[list["Document"]] = relationship("Document", back_populates="category_obj")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "parent_id": self.parent_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Document(Base):
    """知识库文档"""

    __tablename__ = "documents"

    title: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    # 文件信息
    file_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    file_type: Mapped[str | None] = mapped_column(String(50), nullable=True)  # markdown, pdf, txt, etc.
    file_size: Mapped[int | None] = mapped_column(Integer, nullable=True)  # bytes

    # 状态和分类
    status: Mapped[DocumentStatus] = mapped_column(
        SQLEnum(DocumentStatus),
        default=DocumentStatus.PENDING,
        nullable=False,
    )
    category: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    category_id: Mapped[str | None] = mapped_column(ForeignKey("document_categories.id"), nullable=True)

    # 元数据
    tags: Mapped[list[str]] = mapped_column(JSON, default=list)
    metadata: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # 统计
    view_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    download_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # 索引信息
    indexed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    elasticsearch_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)

    # 所有权
    created_by: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    updated_by: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True)

    # 关系
    category_obj: Mapped["DocumentCategory | None"] = relationship("DocumentCategory", back_populates="documents")
    creator: Mapped["User | None"] = relationship("User", foreign_keys=[created_by], backref="created_documents")
    updater: Mapped["User | None"] = relationship("User", foreign_keys=[updated_by], backref="updated_documents")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content[:500] + "..." if len(self.content) > 500 else self.content,
            "summary": self.summary,
            "file_path": self.file_path,
            "file_type": self.file_type,
            "file_size": self.file_size,
            "status": self.status.value,
            "category": self.category,
            "category_id": self.category_id,
            "tags": self.tags,
            "metadata": self.metadata,
            "view_count": self.view_count,
            "download_count": self.download_count,
            "indexed_at": self.indexed_at.isoformat() if self.indexed_at else None,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class SearchQuery(Base):
    """搜索查询记录（用于优化搜索和分析）"""

    __tablename__ = "search_queries"

    query: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    filters: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    results_count: Mapped[int] = mapped_column(default=0, nullable=False)
    execution_time_ms: Mapped[float | None] = mapped_column(nullable=True)

    # 用户和会话
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    session_id: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # AI 相关
    used_ai: Mapped[bool] = mapped_column(default=False, nullable=False)
    ai_response: Mapped[str | None] = mapped_column(Text, nullable=True)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "query": self.query,
            "filters": self.filters,
            "results_count": self.results_count,
            "execution_time_ms": self.execution_time_ms,
            "used_ai": self.used_ai,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
