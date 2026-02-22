"""Workflow Service application entry point."""

import logging
from typing import Dict, Any

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import get_settings, Settings
from .dependencies import get_workflow_service
from .service import WorkflowService


_app: FastAPI = None
_settings: Settings = None


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    global _app, _settings

    _settings = get_settings()

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    logger = logging.getLogger(__name__)

    app = FastAPI(
        title="Workflow Service",
        description="Workflow management and execution service.",
        version=_settings.SERVICE_VERSION,
        debug=_settings.LOG_LEVEL == "DEBUG",
    )

    # Enable CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Exception handler
    @app.exception_handler(Exception)
    async def exception_handler(request: Request, exc: Exception):
        logger.error(
            "Unhandled exception",
            exc_info=exc,
            extra={"path": request.url.path},
        )
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal Server Error"},
        )

    # Startup and shutdown events
    @app.on_event("startup")
    async def startup_event():
        logger.info("Workflow Service starting...")
        # Initialize dependencies
        logger.info(f"Service version: {_settings.SERVICE_VERSION}")
        logger.info(f"Log level: {_settings.LOG_LEVEL}")
        logger.info(f"Scheduling strategy: {_settings.SCHEDULING_STRATEGY}")

    @app.on_event("shutdown")
    async def shutdown_event():
        logger.info("Workflow Service shutting down...")

    # Initialize routes
    from ..api import router

    app.include_router(
        router,
        prefix="/api",
        tags=["workflows"],
    )

    # Include monitoring endpoints if enabled
    if _settings.MONITORING_ENABLED:
        from ..monitoring import get_metrics_app

        app.mount("/metrics", get_metrics_app())

    # Health endpoint
    @app.get("/health")
    async def health():
        """Health check endpoint."""
        service = get_workflow_service()
        return service.health_check()

    # Info endpoint
    @app.get("/info")
    async def info():
        """Service information endpoint."""
        return {
            "version": _settings.SERVICE_VERSION,
            "name": _settings.SERVICE_NAME,
            "scheduler": _settings.SCHEDULING_STRATEGY,
        }

    _app = app
    return app


def get_app() -> FastAPI:
    """Get existing application instance or create new one."""
    global _app
    if _app is None:
        _app = create_app()
    return _app


async def get_application() -> FastAPI:
    """Get application instance."""
    return get_app()
