"""MCP (Model Context Protocol) 接口路由"""

import asyncio
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.database import get_db
from backend.models.base import Base
from sqlalchemy import Column, String, Text, JSON

router = APIRouter()


# MCP 服务注册模型
class MCPServiceRegistration(BaseModel):
    """MCP 服务注册"""
    service_name: str
    service_type: str  # "ai-tool", "workflow-engine", "data-source"
    endpoint: str
    auth_token: Optional[str] = None
    capabilities: List[str]
    metadata: Optional[Dict[str, Any]] = None


class MCPWorkflowStep(BaseModel):
    """MCP 工作流步骤"""
    id: str
    type: str  # "transform", "filter", "aggregate", "call"
    config: Dict[str, Any]
    input_mapping: Optional[Dict[str, str]] = None
    output_mapping: Optional[Dict[str, str]] = None


class MCPWorkflowDefinition(BaseModel):
    """MCP 工作流定义"""
    name: str
    description: Optional[str] = None
    steps: List[MCPWorkflowStep]
    trigger: Optional[Dict[str, Any]] = None
    error_handling: Optional[Dict[str, Any]] = None


class MCPService(BaseModel):
    """已注册的 MCP 服务信息"""
    id: str
    service_name: str
    service_type: str
    endpoint: str
    status: str  # "active", "inactive", "error"
    registered_at: str
    last_heartbeat: Optional[str] = None


# MCP 服务模型（SQLAlchemy）
class MCPServiceModel(Base):
    """MCP 服务数据库模型"""
    __tablename__ = "mcp_services"

    service_name = Column(String(100), nullable=False, index=True)
    service_type = Column(String(50), nullable=False)
    endpoint = Column(String(500), nullable=False)
    auth_token = Column(String(500), nullable=True)
    capabilities = Column(JSON, default=list)
    service_metadata = Column(JSON, default=dict)
    status = Column(String(20), default="active")
    last_heartbeat = Column(String(50), nullable=True)


# MCP 工作流模型
class MCPWorkflowModel(Base):
    """MCP 工作流数据库模型"""
    __tablename__ = "mcp_workflows"

    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    steps = Column(JSON, default=list)
    trigger = Column(JSON, default=dict)
    error_handling = Column(JSON, default=dict)
    status = Column(String(20), default="created")
    created_by = Column(String(36), nullable=True)


# MCP 执行记录模型
class MCPExecutionModel(Base):
    """MCP 工作流执行记录"""
    __tablename__ = "mcp_executions"

    workflow_id = Column(String(36), nullable=False, index=True)
    status = Column(String(20), default="pending")
    input_data = Column(JSON, nullable=True)
    output_data = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    started_at = Column(String(50), nullable=True)
    completed_at = Column(String(50), nullable=True)


@router.post("/services/register", response_model=MCPService)
async def register_mcp_service(
    service: MCPServiceRegistration,
    db: AsyncSession = Depends(get_db),
):
    """
    注册 MCP 服务

    允许第三方 AI 工具或工作流引擎注册为 MCP 服务

    - **service_name**: 服务名称
    - **service_type**: 服务类型
    - **endpoint**: 服务端点 URL
    - **capabilities**: 服务能力列表
    """
    # 检查是否已存在同名服务
    result = await db.execute(
        select(MCPServiceModel).where(MCPServiceModel.service_name == service.service_name)
    )
    existing = result.scalar_one_or_none()

    now = datetime.now(timezone.utc).isoformat()

    if existing:
        # 更新现有服务
        existing.endpoint = service.endpoint
        existing.service_type = service.service_type
        existing.capabilities = service.capabilities
        existing.metadata = service.metadata or {}
        existing.status = "active"
        existing.last_heartbeat = now
        await db.commit()
        await db.refresh(existing)

        return MCPService(
            id=existing.id,
            service_name=existing.service_name,
            service_type=existing.service_type,
            endpoint=existing.endpoint,
            status=existing.status,
            registered_at=existing.created_at.isoformat() if existing.created_at else now,
            last_heartbeat=existing.last_heartbeat,
        )

    # 创建新服务
    new_service = MCPServiceModel(
        id=str(uuid4()),
        service_name=service.service_name,
        service_type=service.service_type,
        endpoint=service.endpoint,
        auth_token=service.auth_token,
        capabilities=service.capabilities,
        metadata=service.metadata or {},
        status="active",
        last_heartbeat=now,
    )

    db.add(new_service)
    await db.commit()
    await db.refresh(new_service)

    return MCPService(
        id=new_service.id,
        service_name=new_service.service_name,
        service_type=new_service.service_type,
        endpoint=new_service.endpoint,
        status=new_service.status,
        registered_at=new_service.created_at.isoformat() if new_service.created_at else now,
        last_heartbeat=new_service.last_heartbeat,
    )


@router.get("/services", response_model=List[MCPService])
async def list_mcp_services(
    db: AsyncSession = Depends(get_db),
):
    """获取所有已注册的 MCP 服务"""
    result = await db.execute(
        select(MCPServiceModel).order_by(desc(MCPServiceModel.created_at))
    )
    services = result.scalars().all()

    return [
        MCPService(
            id=s.id,
            service_name=s.service_name,
            service_type=s.service_type,
            endpoint=s.endpoint,
            status=s.status,
            registered_at=s.created_at.isoformat() if s.created_at else "",
            last_heartbeat=s.last_heartbeat,
        )
        for s in services
    ]


@router.get("/services/{service_id}")
async def get_mcp_service(
    service_id: str,
    db: AsyncSession = Depends(get_db),
):
    """获取特定 MCP 服务的详细信息"""
    result = await db.execute(
        select(MCPServiceModel).where(MCPServiceModel.id == service_id)
    )
    service = result.scalar_one_or_none()

    if not service:
        raise HTTPException(status_code=404, detail="服务不存在")

    return {
        "id": service.id,
        "service_name": service.service_name,
        "service_type": service.service_type,
        "endpoint": service.endpoint,
        "status": service.status,
        "capabilities": service.capabilities,
        "metadata": service.metadata,
        "registered_at": service.created_at.isoformat() if service.created_at else None,
        "last_heartbeat": service.last_heartbeat,
    }


@router.delete("/services/{service_id}")
async def unregister_mcp_service(
    service_id: str,
    db: AsyncSession = Depends(get_db),
):
    """注销 MCP 服务"""
    result = await db.execute(
        select(MCPServiceModel).where(MCPServiceModel.id == service_id)
    )
    service = result.scalar_one_or_none()

    if not service:
        raise HTTPException(status_code=404, detail="服务不存在")

    await db.delete(service)
    await db.commit()

    return {"message": "服务已注销", "service_id": service_id}


@router.post("/workflows")
async def create_mcp_workflow(
    workflow: MCPWorkflowDefinition,
    created_by: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """
    创建 MCP 工作流

    类似于 n8n 的工作流定义，支持多步骤、条件分支等
    """
    new_workflow = MCPWorkflowModel(
        id=str(uuid4()),
        name=workflow.name,
        description=workflow.description,
        steps=[step.dict() for step in workflow.steps],
        trigger=workflow.trigger or {},
        error_handling=workflow.error_handling or {},
        status="created",
        created_by=created_by,
    )

    db.add(new_workflow)
    await db.commit()
    await db.refresh(new_workflow)

    return {
        "workflow_id": new_workflow.id,
        "name": new_workflow.name,
        "status": new_workflow.status,
        "created_at": new_workflow.created_at.isoformat() if new_workflow.created_at else None,
    }


@router.get("/workflows/{workflow_id}")
async def get_mcp_workflow(
    workflow_id: str,
    db: AsyncSession = Depends(get_db),
):
    """获取 MCP 工作流定义"""
    result = await db.execute(
        select(MCPWorkflowModel).where(MCPWorkflowModel.id == workflow_id)
    )
    workflow = result.scalar_one_or_none()

    if not workflow:
        raise HTTPException(status_code=404, detail="工作流不存在")

    return {
        "workflow_id": workflow.id,
        "name": workflow.name,
        "description": workflow.description,
        "steps": workflow.steps,
        "trigger": workflow.trigger,
        "error_handling": workflow.error_handling,
        "status": workflow.status,
        "created_at": workflow.created_at.isoformat() if workflow.created_at else None,
        "updated_at": workflow.updated_at.isoformat() if workflow.updated_at else None,
    }


@router.post("/workflows/{workflow_id}/execute")
async def execute_mcp_workflow(
    workflow_id: str,
    input_data: Optional[Dict[str, Any]] = None,
    db: AsyncSession = Depends(get_db),
):
    """
    执行 MCP 工作流

    - **workflow_id**: 工作流 ID
    - **input_data**: 工作流输入数据
    """
    # 检查工作流是否存在
    result = await db.execute(
        select(MCPWorkflowModel).where(MCPWorkflowModel.id == workflow_id)
    )
    workflow = result.scalar_one_or_none()

    if not workflow:
        raise HTTPException(status_code=404, detail="工作流不存在")

    # 创建工作流执行记录
    execution = MCPExecutionModel(
        id=str(uuid4()),
        workflow_id=workflow_id,
        status="pending",
        input_data=input_data,
        started_at=datetime.now(timezone.utc).isoformat(),
    )

    db.add(execution)
    await db.commit()
    await db.refresh(execution)

    # TODO: 实际执行工作流逻辑
    # 这里只是模拟执行
    await asyncio.sleep(0.5)  # 模拟执行时间

    # 更新执行状态为完成
    execution.status = "completed"
    execution.completed_at = datetime.now(timezone.utc).isoformat()
    execution.output_data = {
        "result": "工作流执行成功",
        "steps_executed": len(workflow.steps),
        "input": input_data,
    }

    await db.commit()

    return {
        "execution_id": execution.id,
        "workflow_id": workflow_id,
        "status": execution.status,
        "started_at": execution.started_at,
        "completed_at": execution.completed_at,
        "output": execution.output_data,
    }


@router.get("/workflows/{workflow_id}/executions")
async def get_workflow_executions(
    workflow_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """获取工作流的执行历史"""
    # 检查工作流是否存在
    result = await db.execute(
        select(MCPWorkflowModel).where(MCPWorkflowModel.id == workflow_id)
    )
    workflow = result.scalar_one_or_none()

    if not workflow:
        raise HTTPException(status_code=404, detail="工作流不存在")

    # 查询执行历史
    query = (
        select(MCPExecutionModel)
        .where(MCPExecutionModel.workflow_id == workflow_id)
        .order_by(desc(MCPExecutionModel.started_at))
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(query)
    executions = result.scalars().all()

    # 查询总数
    count_result = await db.execute(
        select(MCPExecutionModel).where(MCPExecutionModel.workflow_id == workflow_id)
    )
    total = len(count_result.scalars().all())

    return {
        "executions": [
            {
                "execution_id": e.id,
                "workflow_id": e.workflow_id,
                "status": e.status,
                "started_at": e.started_at,
                "completed_at": e.completed_at,
                "output": e.output_data,
                "error": e.error_message,
            }
            for e in executions
        ],
        "total": total,
    }


@router.post("/call-service")
async def call_mcp_service(
    service_id: str,
    method: str,
    params: Optional[Dict[str, Any]] = None,
    db: AsyncSession = Depends(get_db),
):
    """
    通过 MCP 接口调用服务

    - **service_id**: 服务 ID
    - **method**: 调用的方法
    - **params**: 方法参数
    """
    # 查找服务
    result = await db.execute(
        select(MCPServiceModel).where(MCPServiceModel.id == service_id)
    )
    service = result.scalar_one_or_none()

    if not service:
        raise HTTPException(status_code=404, detail="服务不存在")

    if service.status != "active":
        raise HTTPException(status_code=400, detail=f"服务当前不可用，状态: {service.status}")

    # TODO: 实际调用服务
    # 这里只是模拟调用
    return {
        "service_id": service_id,
        "service_name": service.service_name,
        "method": method,
        "params": params,
        "result": {
            "status": "success",
            "message": f"方法 '{method}' 调用成功",
            "data": {},
        },
    }


@router.post("/healthcheck/{service_id}")
async def healthcheck_mcp_service(
    service_id: str,
    db: AsyncSession = Depends(get_db),
):
    """检查 MCP 服务的健康状态"""
    import time

    start_time = time.time()

    # 查找服务
    result = await db.execute(
        select(MCPServiceModel).where(MCPServiceModel.id == service_id)
    )
    service = result.scalar_one_or_none()

    if not service:
        raise HTTPException(status_code=404, detail="服务不存在")

    # TODO: 实际检查服务健康状态
    # 这里只是模拟检查
    latency_ms = int((time.time() - start_time) * 1000)

    # 更新心跳时间
    service.last_heartbeat = datetime.now(timezone.utc).isoformat()
    await db.commit()

    return {
        "service_id": service_id,
        "service_name": service.service_name,
        "status": service.status,
        "latency_ms": latency_ms,
        "last_heartbeat": service.last_heartbeat,
    }
