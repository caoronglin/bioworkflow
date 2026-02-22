"""Package management endpoints."""

from typing import List, Optional

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, status

from miniforge_service.core.dependencies import get_manager
from miniforge_service.core.manager import MiniforgeManager
from miniforge_service.core.models import (
    Package,
    PackageChannel,
    PackageInstall,
    PackageSearchResult,
)

logger = structlog.get_logger(__name__)
router = APIRouter()


@router.get(
    "/search",
    response_model=PackageSearchResult,
    summary="Search packages",
    description="Search for packages in configured channels.",
)
async def search_packages(
    query: str = Query(..., min_length=1, description="Search query"),
    channel: Optional[PackageChannel] = Query(
        None,
        description="Channel to search (default: all)"
    ),
    limit: int = Query(50, ge=1, le=100, description="Maximum results"),
    manager: MiniforgeManager = Depends(get_manager),
) -> PackageSearchResult:
    """Search for packages."""
    logger.info(
        "searching_packages",
        query=query,
        channel=channel,
        limit=limit,
    )

    try:
        packages = await manager.search_packages(
            query=query,
            channel=channel,
            limit=limit,
        )

        return PackageSearchResult(
            packages=packages,
            total=len(packages),
            query=query,
            channel=channel,
        )

    except Exception as e:
        logger.error("failed_to_search_packages", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search packages: {str(e)}",
        )


@router.get(
    "/{env_name}/packages",
    response_model=List[Package],
    summary="List installed packages",
    description="Get a list of packages installed in an environment.",
)
async def list_installed_packages(
    env_name: str,
    manager: MiniforgeManager = Depends(get_manager),
) -> List[Package]:
    """List installed packages in an environment."""
    logger.info("listing_installed_packages", env_name=env_name)

    try:
        environment = await manager.get_environment(env_name)
        return environment.packages

    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Environment '{env_name}' not found",
        )
    except Exception as e:
        logger.error("failed_to_list_packages", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list packages: {str(e)}",
        )


@router.post(
    "/{env_name}/packages",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Install packages",
    description="Install one or more packages in an environment.",
)
async def install_packages(
    env_name: str,
    packages: List[PackageInstall],
    manager: MiniforgeManager = Depends(get_manager),
) -> None:
    """Install packages in an environment."""
    if not packages:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No packages specified",
        )

    logger.info(
        "installing_packages",
        env_name=env_name,
        packages=[p.name for p in packages],
    )

    try:
        await manager.install_packages(env_name, packages)

        logger.info("packages_installed", env_name=env_name)

    except ValueError as e:
        logger.warning("invalid_install_request", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )
    except RuntimeError as e:
        logger.error("failed_to_install_packages", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to install packages: {str(e)}",
        )


@router.delete(
    "/{env_name}/packages/{package_name}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove a package",
    description="Remove a package from an environment.",
)
async def remove_package(
    env_name: str,
    package_name: str,
    manager: MiniforgeManager = Depends(get_manager),
) -> None:
    """Remove a package from an environment."""
    logger.info(
        "removing_package",
        env_name=env_name,
        package=package_name,
    )

    try:
        await manager.remove_packages(env_name, [package_name])

        logger.info("package_removed", env_name=env_name, package=package_name)

    except ValueError as e:
        logger.warning("invalid_remove_request", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )
    except RuntimeError as e:
        logger.error("failed_to_remove_package", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to remove package: {str(e)}",
        )


@router.post(
    "/{env_name}/packages/update",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Update packages",
    description="Update one or all packages in an environment.",
)
async def update_packages(
    env_name: str,
    package_names: Optional[List[str]] = None,
    manager: MiniforgeManager = Depends(get_manager),
) -> None:
    """Update packages in an environment."""
    logger.info(
        "updating_packages",
        env_name=env_name,
        packages=package_names or "all",
    )

    try:
        await manager.update_packages(env_name, package_names)

        logger.info("packages_updated", env_name=env_name)

    except ValueError as e:
        logger.warning("invalid_update_request", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )
    except RuntimeError as e:
        logger.error("failed_to_update_packages", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update packages: {str(e)}",
        )
