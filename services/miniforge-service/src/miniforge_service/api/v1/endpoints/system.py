"""System information endpoints."""

import structlog
from fastapi import APIRouter, Depends, HTTPException, status

from miniforge_service.core.dependencies import get_manager
from miniforge_service.core.manager import MiniforgeManager
from miniforge_service.core.models import SystemInfo

logger = structlog.get_logger(__name__)
router = APIRouter()


@router.get(
    "/info",
    response_model=SystemInfo,
    summary="Get system information",
    description="Get Miniforge/Mamba system information and configuration.",
)
async def get_system_info(
    manager: MiniforgeManager = Depends(get_manager),
) -> SystemInfo:
    """Get system information."""
    logger.info("getting_system_info")

    try:
        info = await manager.get_system_info()
        return info

    except Exception as e:
        logger.error("failed_to_get_system_info", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get system info: {str(e)}",
        )


@router.get(
    "/channels",
    response_model=list[str],
    summary="Get default channels",
    description="Get the list of default Conda channels.",
)
async def get_default_channels() -> list[str]:
    """Get default channels."""
    from miniforge_service.core.models import PackageChannel

    return [
        PackageChannel.CONDA_FORGE.value,
        PackageChannel.BIOCUNDA.value,
    ]


@router.get(
    "/health",
    summary="Health check",
    description="Check if the service and Miniforge are healthy.",
)
async def health_check(
    manager: MiniforgeManager = Depends(get_manager),
) -> dict:
    """Health check endpoint."""
    try:
        # Try to get system info to verify connection
        await manager.get_system_info()

        return {
            "status": "healthy",
            "miniforge": "connected",
        }

    except Exception as e:
        logger.warning("health_check_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "status": "unhealthy",
                "miniforge": f"error: {str(e)}",
            },
        )
