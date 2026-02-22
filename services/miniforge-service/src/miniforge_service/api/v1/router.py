"""API router for Miniforge Service v1."""

from fastapi import APIRouter

from miniforge_service.api.v1.endpoints import environments, packages, system

api_router = APIRouter()

# Include endpoint routers
api_router.include_router(
    environments.router,
    prefix="/environments",
    tags=["environments"],
)

api_router.include_router(
    packages.router,
    prefix="/packages",
    tags=["packages"],
)

api_router.include_router(
    system.router,
    prefix="/system",
    tags=["system"],
)
