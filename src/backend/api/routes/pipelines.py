"""流水线管理路由"""

from datetime import datetime, timezone
from typing import List, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.auth.jwt import get_current_user_id
from backend.core.database import get_db
from backend.models.pipeline import ExecutionStatus, Pipeline, PipelineExecution, PipelineStatus
from backend.services.pipeline.service import PipelineService

router = APIRouter()


class PipelineConfig(BaseModel):
    name: str
    description: Optional[str] = None
    snakefile_path: str
    conda_environment: Optional[str] = None
    parameters: Optional[dict] = None


class PipelineResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    status: str
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class ExecutionResultResponse(BaseModel):
    execution_id: str
    pipeline_id: str
    status: str
    start_time: str
    end_time: Optional[str] = None
    logs: Optional[str] = None


class ExecutionListResponse(BaseModel):
    executions: List[ExecutionResultResponse]
    total: int


# 依赖注入
async def get_pipeline_service() -> PipelineService:
    return PipelineService()


@router.get("/", response_model=List[PipelineResponse])
async def list_pipelines(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """
    获取所有流水线列表

    - **skip**: 跳过的记录数
    - **limit**: 返回的最大记录数
    - **status**: 按状态筛选
    """
    query = select(Pipeline).order_by(desc(Pipeline.created_at))

    if status:
        query = query.where(Pipeline.status == PipelineStatus(status))

    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    pipelines = result.scalars().all()

    return [
        PipelineResponse(
            id=p.id,
            name=p.name,
            description=p.description,
            status=p.status.value,
            created_at=p.created_at.isoformat() if p.created_at else "",
            updated_at=p.updated_at.isoformat() if p.updated_at else "",
        )
        for p in pipelines
    ]


@router.post("/", response_model=PipelineResponse)
async def create_pipeline(
    config: PipelineConfig,
    owner_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    创建新的流水线

    - **name**: 流水线名称
    - **snakefile_path**: Snakefile 文件路径
    - **conda_environment**: Conda 环境名称
    - **parameters**: 流水线参数
    """
    pipeline = Pipeline(
        id=str(uuid4()),
        name=config.name,
        description=config.description,
        snakefile_path=config.snakefile_path,
        conda_environment=config.conda_environment,
        parameters=config.parameters,
        owner_id=owner_id,
        status=PipelineStatus.DRAFT,
    )

    db.add(pipeline)
    await db.commit()
    await db.refresh(pipeline)

    return PipelineResponse(
        id=pipeline.id,
        name=pipeline.name,
        description=pipeline.description,
        status=pipeline.status.value,
        created_at=pipeline.created_at.isoformat() if pipeline.created_at else "",
        updated_at=pipeline.updated_at.isoformat() if pipeline.updated_at else "",
    )


@router.get("/{pipeline_id}", response_model=dict)
async def get_pipeline(
    pipeline_id: str,
    db: AsyncSession = Depends(get_db),
):
    """获取特定流水线的详细信息"""
    result = await db.execute(select(Pipeline).where(Pipeline.id == pipeline_id))
    pipeline = result.scalar_one_or_none()

    if not pipeline:
        raise HTTPException(status_code=404, detail="流水线不存在")

    return pipeline.to_dict()


@router.put("/{pipeline_id}")
async def update_pipeline(
    pipeline_id: str,
    config: PipelineConfig,
    db: AsyncSession = Depends(get_db),
):
    """更新流水线配置"""
    result = await db.execute(select(Pipeline).where(Pipeline.id == pipeline_id))
    pipeline = result.scalar_one_or_none()

    if not pipeline:
        raise HTTPException(status_code=404, detail="流水线不存在")

    pipeline.name = config.name
    pipeline.description = config.description
    pipeline.snakefile_path = config.snakefile_path
    pipeline.conda_environment = config.conda_environment
    pipeline.parameters = config.parameters
    pipeline.updated_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(pipeline)

    return {"message": "流水线已更新", "pipeline_id": pipeline_id}


@router.delete("/{pipeline_id}")
async def delete_pipeline(
    pipeline_id: str,
    db: AsyncSession = Depends(get_db),
):
    """删除流水线"""
    result = await db.execute(select(Pipeline).where(Pipeline.id == pipeline_id))
    pipeline = result.scalar_one_or_none()

    if not pipeline:
        raise HTTPException(status_code=404, detail="流水线不存在")

    await db.delete(pipeline)
    await db.commit()

    return {"message": "流水线已删除", "pipeline_id": pipeline_id}


@router.post("/{pipeline_id}/execute", response_model=ExecutionResultResponse)
async def execute_pipeline(
    pipeline_id: str,
    parameters: Optional[dict] = None,
    user_id: str = Depends(get_current_user_id),
    service: PipelineService = Depends(get_pipeline_service),
):
    """
    执行流水线

    - **pipeline_id**: 流水线 ID
    - **parameters**: 运行时参数覆盖
    """
    # 检查流水线是否存在
    try:
        await service.get_pipeline(pipeline_id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"流水线不存在: {e}")

    # 执行流水线
    try:
        result = await service.execute(
            pipeline_id=pipeline_id,
            triggered_by=user_id,
            parameters=parameters,
        )

        return ExecutionResultResponse(
            execution_id=result.execution_id,
            pipeline_id=pipeline_id,
            status=result.status.value,
            start_time=result.started_at.isoformat() if result.started_at else "",
            end_time=result.completed_at.isoformat() if result.completed_at else None,
            logs=None,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"执行失败: {e}")


@router.get("/{pipeline_id}/executions", response_model=ExecutionListResponse)
async def list_executions(
    pipeline_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """获取流水线的执行历史"""
    # 检查流水线是否存在
    result = await db.execute(select(Pipeline).where(Pipeline.id == pipeline_id))
    pipeline = result.scalar_one_or_none()

    if not pipeline:
        raise HTTPException(status_code=404, detail="流水线不存在")

    # 查询执行历史
    query = (
        select(PipelineExecution)
        .where(PipelineExecution.pipeline_id == pipeline_id)
        .order_by(desc(PipelineExecution.created_at))
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(query)
    executions = result.scalars().all()

    # 查询总数（使用 COUNT 而非加载全部记录）
    count_result = await db.execute(
        select(func.count()).select_from(PipelineExecution).where(PipelineExecution.pipeline_id == pipeline_id)
    )
    total = count_result.scalar() or 0

    return ExecutionListResponse(
        executions=[
            ExecutionResultResponse(
                execution_id=e.id,
                pipeline_id=e.pipeline_id,
                status=e.status.value,
                start_time=e.started_at.isoformat() if e.started_at else "",
                end_time=e.completed_at.isoformat() if e.completed_at else None,
                logs=None,
            )
            for e in executions
        ],
        total=total,
    )


@router.get("/executions/{execution_id}")
async def get_execution(
    execution_id: str,
    db: AsyncSession = Depends(get_db),
):
    """获取特定执行的详细信息和日志"""
    result = await db.execute(
        select(PipelineExecution).where(PipelineExecution.id == execution_id)
    )
    execution = result.scalar_one_or_none()

    if not execution:
        raise HTTPException(status_code=404, detail="执行记录不存在")

    return {
        "execution_id": execution.id,
        "pipeline_id": execution.pipeline_id,
        "status": execution.status.value,
        "parameters": execution.parameters,
        "started_at": execution.started_at.isoformat() if execution.started_at else None,
        "completed_at": execution.completed_at.isoformat() if execution.completed_at else None,
        "output_dir": execution.output_dir,
        "log_path": execution.log_path,
        "error_message": execution.error_message,
        "triggered_by": execution.triggered_by,
    }


@router.post("/{pipeline_id}/validate")
async def validate_pipeline(
    pipeline_id: str,
    db: AsyncSession = Depends(get_db),
):
    """验证流水线配置的有效性"""
    result = await db.execute(select(Pipeline).where(Pipeline.id == pipeline_id))
    pipeline = result.scalar_one_or_none()

    if not pipeline:
        raise HTTPException(status_code=404, detail="流水线不存在")

    # 基本验证
    errors = []

    if not pipeline.snakefile_path:
        errors.append("Snakefile 路径不能为空")

    # TODO: 添加更多验证逻辑，如检查文件是否存在、Snakefile 语法验证等

    if errors:
        return {"valid": False, "errors": errors}

    return {"valid": True, "message": "流水线配置有效"}
