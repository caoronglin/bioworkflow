"""
BioWorkflow API

This module aggregates all API routes for the BioWorkflow platform.
"""

from fastapi import APIRouter

from backend.api.routes import auth, health, pipelines, workflows

# Create main API router
api_router = APIRouter()

# Include all sub-routers
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(pipelines.router, prefix="/pipelines", tags=["pipelines"])
api_router.include_router(workflows.router, prefix="/workflows", tags=["workflows"])

# Export main router
__all__ = ["api_router"]
