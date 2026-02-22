"""API endpoints for workflow service."""

from fastapi import APIRouter

from .workflows import router as workflows_router
from .tasks import router as tasks_router
from .executions import router as executions_router


router = APIRouter()
router.include_router(
    workflows_router,
    prefix="/workflows",
    tags=["workflows"],
)
router.include_router(
    tasks_router,
    prefix="/tasks",
    tags=["tasks"],
)
router.include_router(
    executions_router,
    prefix="/executions",
    tags=["executions"],
)
