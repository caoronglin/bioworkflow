"""Workflow execution endpoints."""

from typing import List, Optional, Dict, Any
from uuid import UUID
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
)
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.dependencies import get_db_session, get_workflow_service
from ..core.service import WorkflowService
from ..types.execution import (
    Execution,
    ExecutionCreate,
    ExecutionUpdate,
    ExecutionList,
    ExecutionStatus,
)


router = APIRouter()


@router.post(
    "",
    response_model=Execution,
    status_code=201,
)
async def create_execution(
    execution_data: ExecutionCreate,
    db_session: AsyncSession = Depends(get_db_session),
):
    """Create execution for a workflow."""
    service = WorkflowService(db_session)
    try:
        return await service.create_execution(execution_data)
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=str(e),
        )


@router.get(
    "",
    response_model=ExecutionList,
)
async def get_executions(
    db_session: AsyncSession = Depends(get_db_session),
    workflow_id: Optional[UUID] = Query(None),
    status: Optional[ExecutionStatus] = Query(None),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
):
    """Get executions with optional filtering."""
    service = WorkflowService(db_session)
    executions = await service.get_executions(
        workflow_id,
        status,
        offset,
        limit,
    )

    return executions


@router.get(
    "/{execution_id}",
    response_model=Execution,
)
async def get_execution(
    execution_id: UUID,
    db_session: AsyncSession = Depends(get_db_session),
):
    """Get execution by ID."""
    service = WorkflowService(db_session)
    execution = await service.get_execution(execution_id)

    if not execution:
        raise HTTPException(
            status_code=404,
            detail="Execution not found",
        )

    return execution


@router.put(
    "/{execution_id}",
    response_model=Execution,
)
async def update_execution(
    execution_id: UUID,
    execution_data: ExecutionUpdate,
    db_session: AsyncSession = Depends(get_db_session),
):
    """Update execution status or config."""
    service = WorkflowService(db_session)
    try:
        updated = await service.update_execution(execution_id, execution_data)

        if not updated:
            raise HTTPException(
                status_code=404,
                detail="Execution not found",
            )

        return updated

    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=str(e),
        )


@router.post(
    "/{execution_id}/start",
    status_code=202,
)
async def start_execution(
    execution_id: UUID,
    db_session: AsyncSession = Depends(get_db_session),
):
    """Start execution if in pending state."""
    service = WorkflowService(db_session)
    execution = await service.get_execution(execution_id)

    if not execution:
        raise HTTPException(
            status_code=404,
            detail="Execution not found",
        )

    if execution.status == ExecutionStatus.running:
        raise HTTPException(
            status_code=400,
            detail="Execution is already running",
        )

    try:
        await service.start_execution(execution_id)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start execution: {str(e)}",
        )


@router.post(
    "/{execution_id}/cancel",
    status_code=202,
)
async def cancel_execution(
    execution_id: UUID,
    db_session: AsyncSession = Depends(get_db_session),
):
    """Cancel running execution."""
    service = WorkflowService(db_session)
    execution = await service.get_execution(execution_id)

    if not execution:
        raise HTTPException(
            status_code=404,
            detail="Execution not found",
        )

    if execution.status not in [ExecutionStatus.running, ExecutionStatus.pending]:
        raise HTTPException(
            status_code=400,
            detail=f"Execution is in '{execution.status}' state, cannot cancel",
        )

    try:
        await service.cancel_execution(execution_id)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to cancel execution: {str(e)}",
        )
