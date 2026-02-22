"""Environment management endpoints."""

from typing import List, Optional

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, status

from miniforge_service.core.dependencies import get_manager
from miniforge_service.core.manager import MiniforgeManager
from miniforge_service.core.models import (
    Environment,
    EnvironmentCreate,
    EnvironmentList,
    EnvironmentStatus,
    EnvironmentUpdate,
)

logger = structlog.get_logger(__name__)
router = APIRouter()


@router.get(
    "",
    response_model=EnvironmentList,
    summary="List all environments",
    description="Get a list of all Miniforge environments.",
)
async def list_environments(
    manager: MiniforgeManager = Depends(get_manager),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Page size"),
    status: Optional[EnvironmentStatus] = Query(None, description="Filter by status"),
    search: Optional[str] = Query(None, description="Search by name"),
) -> EnvironmentList:
    """List all environments with optional filtering."""
    logger.info(
        "listing_environments",
        page=page,
        page_size=page_size,
        status=status,
        search=search,
    )

    try:
        environments = await manager.list_environments()

        # Apply filters
        if status:
            environments = [e for e in environments if e.status == status]

        if search:
            search_lower = search.lower()
            environments = [
                e for e in environments
                if search_lower in e.name.lower()
            ]

        # Apply pagination
        total = len(environments)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated = environments[start_idx:end_idx]

        return EnvironmentList(
            environments=paginated,
            total=total,
            page=page,
            page_size=page_size,
        )

    except Exception as e:
        logger.error("failed_to_list_environments", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list environments: {str(e)}",
        )


@router.post(
    "",
    response_model=Environment,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new environment",
    description="Create a new Miniforge environment with specified packages.",
)
async def create_environment(
    request: EnvironmentCreate,
    manager: MiniforgeManager = Depends(get_manager),
) -> Environment:
    """Create a new environment."""
    logger.info(
        "creating_environment",
        name=request.name,
        python_version=request.python_version,
        package_count=len(request.packages),
    )

    try:
        environment = await manager.create_environment(request)

        logger.info(
            "environment_created",
            name=environment.name,
            id=environment.id,
        )

        return environment

    except ValueError as e:
        logger.warning("invalid_environment_request", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )
    except RuntimeError as e:
        logger.error("failed_to_create_environment", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create environment: {str(e)}",
        )


@router.get(
    "/{name}",
    response_model=Environment,
    summary="Get environment details",
    description="Get detailed information about a specific environment.",
)
async def get_environment(
    name: str,
    manager: MiniforgeManager = Depends(get_manager),
) -> Environment:
    """Get environment by name."""
    logger.info("getting_environment", name=name)

    try:
        environment = await manager.get_environment(name)
        return environment

    except ValueError as e:
        logger.warning("environment_not_found", name=name)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Environment '{name}' not found",
        )
    except RuntimeError as e:
        logger.error("failed_to_get_environment", name=name, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get environment: {str(e)}",
        )


@router.patch(
    "/{name}",
    response_model=Environment,
    summary="Update environment",
    description="Update environment packages and settings.",
)
async def update_environment(
    name: str,
    request: EnvironmentUpdate,
    manager: MiniforgeManager = Depends(get_manager),
) -> Environment:
    """Update an existing environment."""
    logger.info(
        "updating_environment",
        name=name,
        add_packages=[p.name for p in request.add_packages],
        remove_packages=request.remove_packages,
    )

    try:
        environment = await manager.update_environment(name, request)

        logger.info("environment_updated", name=name)
        return environment

    except ValueError as e:
        logger.warning("invalid_update_request", name=name, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )
    except RuntimeError as e:
        logger.error("failed_to_update_environment", name=name, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update environment: {str(e)}",
        )


@router.delete(
    "/{name}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete environment",
    description="Permanently delete an environment.",
)
async def delete_environment(
    name: str,
    force: bool = False,
    manager: MiniforgeManager = Depends(get_manager),
) -> None:
    """Delete an environment."""
    logger.info("deleting_environment", name=name, force=force)

    try:
        await manager.delete_environment(name, force=force)
        logger.info("environment_deleted", name=name)

    except ValueError as e:
        logger.warning("cannot_delete_environment", name=name, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )
    except RuntimeError as e:
        logger.error("failed_to_delete_environment", name=name, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete environment: {str(e)}",
        )


@router.post(
    "/{name}/clone",
    response_model=Environment,
    status_code=status.HTTP_201_CREATED,
    summary="Clone environment",
    description="Create a copy of an existing environment.",
)
async def clone_environment(
    name: str,
    new_name: str,
    manager: MiniforgeManager = Depends(get_manager),
) -> Environment:
    """Clone an environment."""
    logger.info("cloning_environment", source=name, target=new_name)

    try:
        # Export source environment
        source_env = await manager.get_environment(name)

        # Create new environment with same packages
        from miniforge_service.core.models import EnvironmentCreate, PackageInstall

        packages = [
            PackageInstall(
                name=pkg.name,
                version=pkg.version,
                channel=pkg.channel,
            )
            for pkg in source_env.packages
            if pkg.name != "python"  # Python handled separately
        ]

        create_request = EnvironmentCreate(
            name=new_name,
            description=f"Cloned from {name}",
            python_version=source_env.python_version,
            packages=packages,
            channels=source_env.channels,
        )

        new_env = await manager.create_environment(create_request)

        logger.info("environment_cloned", source=name, target=new_name)
        return new_env

    except ValueError as e:
        logger.warning("clone_validation_error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )
    except RuntimeError as e:
        logger.error("failed_to_clone_environment", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clone environment: {str(e)}",
        )
