"""Task management endpoints."""

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
from ..types.task import (
    Task,
    TaskCreate,
    TaskUpdate,
    TaskExecution,
    ResourceRequirements,
)


router = APIRouter()


@router.get(
    "",
    response_model=List[Task],
)
async def get_tasks(
    db_session: AsyncSession = Depends(get_db_session),
    workflow_id: Optional[UUID] = Query(None),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
):
    """Get tasks with optional filtering."""
    service = WorkflowService(db_session)

    if workflow_id:
        tasks = await service.get_workflow_tasks(workflow_id, offset, limit)
    else:
        tasks = await service.get_all_tasks(offset, limit)

    return tasks


@router.get(
    "/{task_id}",
    response_model=Task,
)
async def get_task(
    task_id: UUID,
    db_session: AsyncSession = Depends(get_db_session),
):
    """Get task by ID."""
    service = WorkflowService(db_session)
    task = await service.get_task(task_id)

    if not task:
        raise HTTPException(
            status_code=404,
            detail="Task not found",
        )

    return task


@router.put(
    "/{task_id}",
    response_model=Task,
)
async def update_task(
    task_id: UUID,
    task_data: TaskUpdate,
    db_session: AsyncSession = Depends(get_db_session),
):
    """Update task by ID."""
    service = WorkflowService(db_session)
    try:
        updated = await service.update_task(task_id, task_data)

        if not updated:
            raise HTTPException(
                status_code=404,
                detail="Task not found",
            )

        return updated

    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=str(e),
        )


@router.get(
    "/{task_id}/executions",
    response_model=List[TaskExecution],
)
async def get_task_executions(
    task_id: UUID,
    db_session: AsyncSession = Depends(get_db_session),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
):
    """Get task execution history."""
    service = WorkflowService(db_session)
    executions = await service.get_task_executions(task_id, offset, limit)
    return executions
