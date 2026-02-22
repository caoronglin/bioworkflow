"""FastAPI dependencies for Miniforge Service."""

from fastapi import Depends, HTTPException, status

from miniforge_service.core.manager import MiniforgeManager
from miniforge_service.main import app_state


async def get_manager() -> MiniforgeManager:
    """Get MiniforgeManager instance.

    Raises:
        HTTPException: If manager is not initialized
    """
    if app_state.manager is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service is not fully initialized yet",
        )
    return app_state.manager
