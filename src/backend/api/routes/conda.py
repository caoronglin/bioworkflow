"""
Conda Environment Management API Routes (Async)

This module provides RESTful API endpoints for asynchronous Conda
environment management operations.
"""

from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field

from backend.core.logging import get_logger
from backend.services.conda.async_manager import (
    AsyncCondaManager,
    CondaEnvironment,
    CondaOperationProgress,
    CondaOperationStatus,
    CondaOperationType,
    get_conda_manager,
    create_environment as create_env,
    delete_environment as delete_env,
    list_environments as list_envs,
    install_packages as install_pkgs,
)

logger = get_logger(__name__)
router = APIRouter(prefix="/conda", tags=["conda"])


# ============================================================================
# Pydantic Models
# ============================================================================

class CreateEnvironmentRequest(BaseModel):
    """Request model for creating an environment."""
    name: str = Field(..., description="Environment name")
    python_version: Optional[str] = Field(None, description="Python version (e.g., '3.11')")
    packages: Optional[List[str]] = Field(None, description="Packages to install")
    channels: Optional[List[str]] = Field(None, description="Channels to use")


class DeleteEnvironmentRequest(BaseModel):
    """Request model for deleting an environment."""
    name: str = Field(..., description="Environment name")


class InstallPackagesRequest(BaseModel):
    """Request model for installing packages."""
    environment_name: str = Field(..., description="Target environment name")
    packages: List[str] = Field(..., description="Packages to install")
    channels: Optional[List[str]] = Field(None, description="Channels to use")


class EnvironmentResponse(BaseModel):
    """Response model for environment information."""
    name: str
    path: Optional[str] = None
    python_version: Optional[str] = None
    packages_count: int = 0

    class Config:
        from_attributes = True


class OperationResponse(BaseModel):
    """Response model for operation submission."""
    operation_id: str
    status: str
    message: str

    class Config:
        from_attributes = True


class OperationStatusResponse(BaseModel):
    """Response model for operation status."""
    operation_id: str
    operation_type: str
    status: str
    environment_name: Optional[str]
    progress_percentage: float
    current_step: str
    completed_steps: int
    total_steps: int
    duration_seconds: float
    messages: List[str]

    class Config:
        from_attributes = True


# ============================================================================
# Dependency Injection
# ============================================================================

async def get_conda_manager_dependency() -> AsyncCondaManager:
    """Dependency to get the Conda manager."""
    return await get_conda_manager()


# ============================================================================
# API Endpoints
# ============================================================================

@router.get("/environments", response_model=List[EnvironmentResponse])
async def list_environments(
    manager: AsyncCondaManager = Depends(get_conda_manager_dependency),
) -> List[EnvironmentResponse]:
    """
    List all Conda environments.

    Returns a list of all Conda environments on the system.
    """
    try:
        environments = await manager.list_environments()
        return [
            EnvironmentResponse(
                name=env.name,
                path=env.path,
                python_version=env.python_version,
                packages_count=len(env.packages),
            )
            for env in environments
        ]
    except Exception as e:
        logger.exception("Failed to list environments")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list environments: {str(e)}"
        )


@router.post("/environments", response_model=OperationResponse)
async def create_environment(
    request: CreateEnvironmentRequest,
    background_tasks: BackgroundTasks,
    manager: AsyncCondaManager = Depends(get_conda_manager_dependency),
) -> OperationResponse:
    """
    Create a new Conda environment asynchronously.

    This endpoint initiates an asynchronous environment creation operation.
    Use the returned operation_id to track progress.
    """
    try:
        operation_id = await manager.create_environment(
            name=request.name,
            python_version=request.python_version,
            packages=request.packages,
            channels=request.channels,
        )

        return OperationResponse(
            operation_id=operation_id,
            status="queued",
            message=f"Environment creation '{request.name}' queued successfully",
        )

    except Exception as e:
        logger.exception(f"Failed to queue environment creation: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create environment: {str(e)}"
        )


@router.delete("/environments/{name}", response_model=OperationResponse)
async def delete_environment(
    name: str,
    manager: AsyncCondaManager = Depends(get_conda_manager_dependency),
) -> OperationResponse:
    """
    Delete a Conda environment asynchronously.

    This endpoint initiates an asynchronous environment deletion operation.
    """
    try:
        operation_id = await manager.delete_environment(name=name)

        return OperationResponse(
            operation_id=operation_id,
            status="queued",
            message=f"Environment deletion '{name}' queued successfully",
        )

    except Exception as e:
        logger.exception(f"Failed to queue environment deletion: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete environment: {str(e)}"
        )


@router.post("/environments/{name}/packages", response_model=OperationResponse)
async def install_packages(
    name: str,
    request: InstallPackagesRequest,
    manager: AsyncCondaManager = Depends(get_conda_manager_dependency),
) -> OperationResponse:
    """
    Install packages into a Conda environment asynchronously.

    This endpoint initiates an asynchronous package installation operation.
    """
    try:
        operation_id = await manager.install_packages(
            environment_name=name,
            packages=request.packages,
            channels=request.channels,
        )

        return OperationResponse(
            operation_id=operation_id,
            status="queued",
            message=f"Package installation into '{name}' queued successfully",
        )

    except Exception as e:
        logger.exception(f"Failed to queue package installation: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to install packages: {str(e)}"
        )


@router.get("/operations/{operation_id}", response_model=OperationStatusResponse)
async def get_operation_status(
    operation_id: str,
    manager: AsyncCondaManager = Depends(get_conda_manager_dependency),
) -> OperationStatusResponse:
    """
    Get the status of an asynchronous operation.

    Use this endpoint to poll for operation progress.
    """
    try:
        progress = await manager.get_operation_status(operation_id)

        if not progress:
            raise HTTPException(
                status_code=404,
                detail=f"Operation {operation_id} not found"
            )

        return OperationStatusResponse(
            operation_id=progress.operation_id,
            operation_type=progress.operation_type.value,
            status=progress.status.value,
            environment_name=progress.environment_name,
            progress_percentage=progress.progress_percentage,
            current_step=progress.current_step,
            completed_steps=progress.completed_steps,
            total_steps=progress.total_steps,
            duration_seconds=progress.duration_seconds,
            messages=progress.messages,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to get operation status: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get operation status: {str(e)}"
        )


@router.get("/operations", response_model=List[OperationStatusResponse])
async def list_operations(
    status: Optional[str] = Query(None, description="Filter by status"),
    manager: AsyncCondaManager = Depends(get_conda_manager_dependency),
) -> List[OperationStatusResponse]:
    """
    List all asynchronous operations.

    Optionally filter by status (pending, running, completed, failed, cancelled).
    """
    try:
        target_status = None
        if status:
            try:
                target_status = CondaOperationStatus(status)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid status: {status}"
                )

        operations = await manager.list_operations(status=target_status)

        return [
            OperationStatusResponse(
                operation_id=op.operation_id,
                operation_type=op.operation_type.value,
                status=op.status.value,
                environment_name=op.environment_name,
                progress_percentage=op.progress_percentage,
                current_step=op.current_step,
                completed_steps=op.completed_steps,
                total_steps=op.total_steps,
                duration_seconds=op.duration_seconds,
                messages=op.messages,
            )
            for op in operations
        ]

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to list operations: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list operations: {str(e)}"
        )


@router.post("/operations/{operation_id}/cancel")
async def cancel_operation(
    operation_id: str,
    manager: AsyncCondaManager = Depends(get_conda_manager_dependency),
) -> Dict[str, Any]:
    """
    Cancel a running operation.
    """
    try:
        success = await manager.cancel_operation(operation_id)

        if not success:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot cancel operation {operation_id}. It may not exist or is already finished."
            )

        return {
            "operation_id": operation_id,
            "status": "cancelled",
            "message": "Operation cancellation requested",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to cancel operation: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to cancel operation: {str(e)}"
        )
