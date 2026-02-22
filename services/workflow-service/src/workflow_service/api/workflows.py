"""Workflow management endpoints."""

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
from ..types.workflow import (
    Workflow,
    WorkflowCreate,
    WorkflowUpdate,
    WorkflowList,
)


router = APIRouter()


@router.post(
    "",
    response_model=Workflow,
    status_code=201,
)
async def create_workflow(
    workflow_data: WorkflowCreate,
    db_session: AsyncSession = Depends(get_db_session),
):
    """Create a new workflow."""
    service = WorkflowService(db_session)
    try:
        return await service.create_workflow(workflow_data)
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=str(e),
        )


@router.get(
    "",
    response_model=WorkflowList,
)
async def get_workflows(
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db_session: AsyncSession = Depends(get_db_session),
):
    """Get all workflows with pagination."""
    service = WorkflowService(db_session)
    workflows = await service.get_workflows(offset, limit)
    total = await service.get_workflow_count()
    return WorkflowList(
        items=workflows,
        total=total,
        offset=offset,
        limit=limit,
    )


@router.get(
    "/{workflow_id}",
    response_model=Workflow,
)
async def get_workflow(
    workflow_id: UUID,
    db_session: AsyncSession = Depends(get_db_session),
):
    """Get workflow by ID."""
    service = WorkflowService(db_session)
    workflow = await service.get_workflow(workflow_id)

    if not workflow:
        raise HTTPException(
            status_code=404,
            detail="Workflow not found",
        )

    return workflow


@router.put(
    "/{workflow_id}",
    response_model=Workflow,
)
async def update_workflow(
    workflow_id: UUID,
    workflow_data: WorkflowUpdate,
    db_session: AsyncSession = Depends(get_db_session),
):
    """Update workflow by ID."""
    service = WorkflowService(db_session)
    try:
        updated = await service.update_workflow(workflow_id, workflow_data)

        if not updated:
            raise HTTPException(
                status_code=404,
                detail="Workflow not found",
            )

        return updated

    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=str(e),
        )


@router.delete(
    "/{workflow_id}",
    status_code=204,
)
async def delete_workflow(
    workflow_id: UUID,
    db_session: AsyncSession = Depends(get_db_session),
):
    """Delete workflow by ID."""
    service = WorkflowService(db_session)
    deleted = await service.delete_workflow(workflow_id)

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Workflow not found",
        )


@router.get(
    "/{workflow_id}/dag",
    responses={
        200: {"description": "DAG visualization in requested format"},
        404: {"description": "Workflow not found"},
    },
)
async def get_workflow_dag(
    workflow_id: UUID,
    format: str = Query("mermaid"),
    db_session: AsyncSession = Depends(get_db_session),
):
    """Get DAG representation of workflow."""
    service = WorkflowService(db_session)
    workflow = await service.get_workflow(workflow_id)

    if not workflow:
        raise HTTPException(
            status_code=404,
            detail="Workflow not found",
        )

    try:
        dag = await service.generate_dag(workflow_id)

        if format == "mermaid":
            return JSONResponse(
                content={"graph": dag},
                media_type="application/json",
            )
        elif format == "dot":
            return JSONResponse(
                content={"dot": GraphVisualizer.to_dot(dag)},
                media_type="application/json",
            )
        elif format == "png":
            return JSONResponse(
                content={"png": GraphVisualizer.to_png(dag)},
                media_type="application/json",
            )
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported format: '{format}'",
            )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate DAG: {str(e)}",
        )
