"""
Workflow Execution API Routes

This module provides RESTful API endpoints for asynchronous Snakemake workflow execution.
Following async/await patterns for non-blocking workflow operations.
"""

from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query, WebSocket
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field

from backend.core.logging import get_logger
from backend.api.routes.auth import get_current_user
from backend.services.snakemake.workflow_engine import (
    WorkflowExecutionEngine,
    WorkflowProgress,
    WorkflowStatus,
    get_workflow_engine,
    shutdown_workflow_engine,
    run_workflow,
    get_status,
    cancel,
)

logger = get_logger(__name__)
router = APIRouter(prefix="/workflows", tags=["workflows"])


# ============================================================================
# Pydantic Models
# ============================================================================

class WorkflowSubmitRequest(BaseModel):
    """Request model for submitting a workflow."""
    workflow_path: str = Field(..., description="Path to the Snakefile")
    workdir: Optional[str] = Field(None, description="Working directory")
    targets: Optional[List[str]] = Field(None, description="Target rules/files")
    dry_run: bool = Field(False, description="Perform dry run")
    config: Optional[Dict[str, Any]] = Field(None, description="Configuration dict")
    config_files: Optional[List[str]] = Field(None, description="Config file paths")
    executor: Optional[str] = Field("local", description="Executor type")
    jobs: int = Field(1, description="Number of parallel jobs", ge=1)
    resources: Optional[Dict[str, Any]] = Field(None, description="Resource requirements")


class WorkflowResponse(BaseModel):
    """Response model for workflow operations."""
    workflow_id: str
    status: str
    message: str
    submitted_at: Optional[str] = None

    class Config:
        from_attributes = True


class WorkflowStatusResponse(BaseModel):
    """Response model for workflow status."""
    workflow_id: str
    status: str
    progress_percentage: float
    total_jobs: int
    completed_jobs: int
    failed_jobs: int
    duration_seconds: float
    messages: List[str]
    current_jobs: List[Dict[str, Any]]

    class Config:
        from_attributes = True


class WorkflowListResponse(BaseModel):
    """Response model for listing workflows."""
    workflows: List[WorkflowStatusResponse]
    total: int

    class Config:
        from_attributes = True


class WorkflowJobInfo(BaseModel):
    """Information about a workflow job."""
    job_id: str
    rule_name: str
    status: str
    start_time: Optional[float]
    end_time: Optional[float]
    log_file: Optional[str]
    error_message: Optional[str]

    class Config:
        from_attributes = True


class WorkflowCreateRequest(BaseModel):
    """Request to create a workflow dynamically."""
    rules: List[Dict[str, Any]]
    config: Optional[Dict[str, Any]] = None
    output_dir: str = Field(..., description="Directory to save the workflow")


class WorkflowCreateResponse(BaseModel):
    """Response for workflow creation."""
    workflow_path: str
    config_path: Optional[str]
    message: str


# ============================================================================
# Dependency Injection
# ============================================================================

async def get_engine() -> WorkflowExecutionEngine:
    """Dependency to get the workflow engine."""
    return await get_workflow_engine()


# ============================================================================
# API Endpoints
# ============================================================================

@router.post(
    "/submit",
    response_model=WorkflowResponse,
    summary="Submit a new workflow",
    description="Submit a Snakemake workflow for asynchronous execution.",
)
async def submit_workflow(
    request: WorkflowSubmitRequest,
    engine: WorkflowExecutionEngine = Depends(get_engine),
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> WorkflowResponse:
    """
    Submit a workflow for execution.

    This endpoint accepts workflow parameters and starts the execution
    asynchronously. It returns immediately with a workflow ID that can
    be used to track the execution status.
    """
    try:
        # Validate workflow path
        workflow_path = Path(request.workflow_path)
        if not workflow_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Workflow file not found: {request.workflow_path}"
            )

        # Submit workflow
        workflow_id = await engine.execute_workflow(
            workflow_path=request.workflow_path,
            workdir=request.workdir,
            targets=request.targets,
            dry_run=request.dry_run,
            config=request.config,
            config_files=request.config_files,
            executor=request.executor,
            jobs=request.jobs,
            resources=request.resources,
        )

        return WorkflowResponse(
            workflow_id=workflow_id,
            status="queued",
            message="Workflow submitted successfully",
            submitted_at=__import__('datetime').datetime.utcnow().isoformat(),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to submit workflow")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to submit workflow: {str(e)}"
        )


@router.get(
    "/{workflow_id}/status",
    response_model=WorkflowStatusResponse,
    summary="Get workflow status",
    description="Get the current status and progress of a workflow execution.",
)
async def get_workflow_status(
    workflow_id: str,
    engine: WorkflowExecutionEngine = Depends(get_engine),
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> WorkflowStatusResponse:
    """Get the status of a workflow execution."""
    progress = await engine.get_workflow_status(workflow_id)

    if not progress:
        raise HTTPException(
            status_code=404,
            detail=f"Workflow not found: {workflow_id}"
        )

    return WorkflowStatusResponse(
        workflow_id=progress.workflow_id,
        status=progress.status.value,
        progress_percentage=progress.progress_percentage,
        total_jobs=progress.total_jobs,
        completed_jobs=progress.completed_jobs,
        failed_jobs=progress.failed_jobs,
        duration_seconds=progress.duration_seconds,
        messages=progress.messages[-20:],  # Last 20 messages
        current_jobs=[
            {
                "job_id": j.job_id,
                "rule_name": j.rule_name,
                "status": j.status.value,
            }
            for j in progress.current_jobs
        ],
    )


@router.get(
    "/list",
    response_model=WorkflowListResponse,
    summary="List workflows",
    description="List all workflow executions, optionally filtered by status.",
)
async def list_workflows(
    status: Optional[str] = Query(None, description="Filter by status"),
    engine: WorkflowExecutionEngine = Depends(get_engine),
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> WorkflowListResponse:
    """List all workflows."""
    workflow_status = WorkflowStatus(status) if status else None
    workflows = await engine.list_workflows(status=workflow_status)

    workflow_responses = [
        WorkflowStatusResponse(
            workflow_id=w.workflow_id,
            status=w.status.value,
            progress_percentage=w.progress_percentage,
            total_jobs=w.total_jobs,
            completed_jobs=w.completed_jobs,
            failed_jobs=w.failed_jobs,
            duration_seconds=w.duration_seconds,
            messages=w.messages[-10:],
            current_jobs=[],
        )
        for w in workflows
    ]

    return WorkflowListResponse(
        workflows=workflow_responses,
        total=len(workflow_responses),
    )


@router.post(
    "/{workflow_id}/cancel",
    response_model=WorkflowResponse,
    summary="Cancel workflow",
    description="Cancel a running or queued workflow.",
)
async def cancel_workflow(
    workflow_id: str,
    engine: WorkflowExecutionEngine = Depends(get_engine),
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> WorkflowResponse:
    """Cancel a workflow."""
    success = await engine.cancel_workflow(workflow_id)

    if not success:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot cancel workflow {workflow_id}. It may not exist or is already finished."
        )

    return WorkflowResponse(
        workflow_id=workflow_id,
        status="cancelled",
        message="Workflow cancellation requested",
    )


@router.post(
    "/{workflow_id}/pause",
    response_model=WorkflowResponse,
    summary="Pause workflow",
    description="Pause a running workflow.",
)
async def pause_workflow(
    workflow_id: str,
    engine: WorkflowExecutionEngine = Depends(get_engine),
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> WorkflowResponse:
    """Pause a workflow."""
    success = await engine.pause_workflow(workflow_id)

    if not success:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot pause workflow {workflow_id}. It may not be running."
        )

    return WorkflowResponse(
        workflow_id=workflow_id,
        status="paused",
        message="Workflow paused",
    )


@router.post(
    "/{workflow_id}/resume",
    response_model=WorkflowResponse,
    summary="Resume workflow",
    description="Resume a paused workflow.",
)
async def resume_workflow(
    workflow_id: str,
    engine: WorkflowExecutionEngine = Depends(get_engine),
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> WorkflowResponse:
    """Resume a workflow."""
    success = await engine.resume_workflow(workflow_id)

    if not success:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot resume workflow {workflow_id}. It may not be paused."
        )

    return WorkflowResponse(
        workflow_id=workflow_id,
        status="resumed",
        message="Workflow resumed",
    )


@router.websocket("/{workflow_id}/logs")
async def workflow_logs_websocket(
    websocket: WebSocket,
    workflow_id: str,
    engine: WorkflowExecutionEngine = Depends(get_engine),
):
    """
    WebSocket endpoint for real-time workflow logs.

    Connect to this endpoint to receive log messages in real-time
    as the workflow executes.
    """
    await websocket.accept()

    try:
        progress = await engine.get_workflow_status(workflow_id)
        if not progress:
            await websocket.send_text(f"Error: Workflow {workflow_id} not found")
            await websocket.close()
            return

        # Send existing messages
        for message in progress.messages:
            await websocket.send_text(message)

        # Subscribe to new messages
        last_count = len(progress.messages)
        while progress.status in (WorkflowStatus.RUNNING, WorkflowStatus.PAUSED, WorkflowStatus.QUEUED):
            # Check for new messages
            current_progress = await engine.get_workflow_status(workflow_id)
            if current_progress and len(current_progress.messages) > last_count:
                for i in range(last_count, len(current_progress.messages)):
                    await websocket.send_text(current_progress.messages[i])
                last_count = len(current_progress.messages)

            # Check for client messages (e.g., cancel command)
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=0.5)
                if data.lower() == "cancel":
                    await engine.cancel_workflow(workflow_id)
                    await websocket.send_text("Cancellation requested")
            except asyncio.TimeoutError:
                pass
            except Exception:
                break

            await asyncio.sleep(0.1)

        # Send final status
        final_progress = await engine.get_workflow_status(workflow_id)
        if final_progress:
            await websocket.send_text(f"\n=== Workflow {final_progress.status.value.upper()} ===")
            await websocket.send_text(f"Duration: {final_progress.duration_seconds:.2f}s")
            await websocket.send_text(f"Jobs: {final_progress.completed_jobs}/{final_progress.total_jobs} completed")

        await websocket.close()

    except Exception as e:
        logger.exception("WebSocket error")
        try:
            await websocket.send_text(f"Error: {str(e)}")
            await websocket.close()
        except:
            pass


@router.post(
    "/create",
    response_model=WorkflowCreateResponse,
    summary="Create workflow from rules",
    description="Dynamically create a Snakefile from rule definitions.",
)
async def create_workflow(
    request: WorkflowCreateRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> WorkflowCreateResponse:
    """Create a workflow dynamically from rules."""
    from backend.services.snakemake.workflow_engine import create_snakefile

    try:
        output_dir = Path(request.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        snakefile_path = output_dir / "Snakefile"

        create_snakefile(
            rules=request.rules,
            output_path=snakefile_path,
            config=request.config,
        )

        config_path = None
        if request.config:
            config_path = str(output_dir / "config.json")

        return WorkflowCreateResponse(
            workflow_path=str(snakefile_path),
            config_path=config_path,
            message=f"Workflow created at {snakefile_path}",
        )

    except Exception as e:
        logger.exception("Failed to create workflow")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create workflow: {str(e)}"
        )


@router.get(
    "/{workflow_id}/stream",
    summary="Stream workflow logs",
    description="Server-sent events endpoint for real-time workflow log streaming.",
)
async def stream_workflow_logs(
    workflow_id: str,
    engine: WorkflowExecutionEngine = Depends(get_engine),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Stream workflow logs using Server-Sent Events (SSE).

    This provides a unidirectional stream of log messages from the workflow.
    """
    from fastapi.responses import StreamingResponse
    import json

    async def event_generator():
        progress = await engine.get_workflow_status(workflow_id)
        if not progress:
            yield f"event: error\\ndata: {json.dumps({'error': 'Workflow not found'})}\\n\\n"
            return

        # Send existing messages
        for message in progress.messages:
            yield f"event: log\\ndata: {json.dumps({'message': message})}\\n\\n"

        # Subscribe to new messages
        last_count = len(progress.messages)
        while progress.status in (WorkflowStatus.RUNNING, WorkflowStatus.PAUSED, WorkflowStatus.QUEUED):
            await asyncio.sleep(0.5)

            current_progress = await engine.get_workflow_status(workflow_id)
            if not current_progress:
                break

            if len(current_progress.messages) > last_count:
                for i in range(last_count, len(current_progress.messages)):
                    yield f"event: log\\ndata: {json.dumps({'message': current_progress.messages[i]})}\\n\\n"
                last_count = len(current_progress.messages)

            progress = current_progress

        # Send final status
        final_progress = await engine.get_workflow_status(workflow_id)
        if final_progress:
            yield f"event: complete\\ndata: {json.dumps({{
                'status': final_progress.status.value,
                'duration': final_progress.duration_seconds,
                'completed_jobs': final_progress.completed_jobs,
                'total_jobs': final_progress.total_jobs,
            }})}\\n\\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        },
    )


# ============================================================================
# Lifecycle Management
# ============================================================================

async def startup_workflow_engine():
    """Initialize workflow engine on application startup."""
    logger.info("Initializing workflow engine...")
    await get_workflow_engine()
    logger.info("Workflow engine initialized")


async def shutdown_workflow_engine_cleanup():
    """Cleanup workflow engine on application shutdown."""
    logger.info("Shutting down workflow engine...")
    await shutdown_workflow_engine()
    logger.info("Workflow engine shutdown complete")
