"""FastAPI application for Miniforge Service."""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from prometheus_client import make_asgi_app

from miniforge_service.api.v1.router import api_router
from miniforge_service.core.config import Settings, get_settings
from miniforge_service.core.manager import MiniforgeManager

# Configure logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer(),
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)


class ApplicationState:
    """Application state container."""

    def __init__(self):
        self.settings: Settings = get_settings()
        self.manager: Optional[MiniforgeManager] = None
        self.started_at: Optional[datetime] = None


# Global state
app_state = ApplicationState()


def setup_opentelemetry(app: FastAPI, settings: Settings) -> None:
    """Configure OpenTelemetry tracing."""
    if not settings.otel_enabled:
        return

    resource = Resource.create(
        {
            "service.name": settings.service_name,
            "service.version": settings.service_version,
            "deployment.environment": settings.environment,
        }
    )

    provider = TracerProvider(resource=resource)

    # Configure OTLP exporter
    if settings.otel_endpoint:
        exporter = OTLPSpanExporter(endpoint=settings.otel_endpoint)
        processor = BatchSpanProcessor(exporter)
        provider.add_span_processor(processor)

    trace.set_tracer_provider(provider)

    # Instrument FastAPI
    FastAPIInstrumentor.instrument_app(app)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager."""
    from datetime import datetime

    # Startup
    logger.info(
        "starting_miniforge_service",
        version=app_state.settings.service_version,
        environment=app_state.settings.environment,
    )

    try:
        # Initialize manager
        app_state.manager = MiniforgeManager(
            root_prefix=app_state.settings.miniforge_root,
            envs_dir=app_state.settings.envs_dir,
        )

        # Test connection
        await app_state.manager.get_system_info()

        app_state.started_at = datetime.utcnow()

        logger.info(
            "miniforge_service_ready",
            root_prefix=str(app_state.manager._root_prefix),
        )

    except Exception as e:
        logger.error(
            "failed_to_start_miniforge_service",
            error=str(e),
        )
        raise

    yield

    # Shutdown
    logger.info("stopping_miniforge_service")

    # Cleanup if needed
    app_state.manager = None
    app_state.started_at = None

    logger.info("miniforge_service_stopped")


def create_application() -> FastAPI:
    """Create FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title=settings.service_name,
        description="Miniforge environment management microservice for BioWorkflow",
        version=settings.service_version,
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
        openapi_url="/openapi.json" if settings.debug else None,
        lifespan=lifespan,
    )

    # Add middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.add_middleware(GZipMiddleware, minimum_size=1000)

    # Add exception handlers
    @app.exception_handler(ValueError)
    async def value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
        logger.warning(
            "validation_error",
            error=str(exc),
            path=request.url.path,
        )
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"detail": str(exc)},
        )

    @app.exception_handler(RuntimeError)
    async def runtime_error_handler(request: Request, exc: RuntimeError) -> JSONResponse:
        logger.error(
            "runtime_error",
            error=str(exc),
            path=request.url.path,
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Internal server error"},
        )

    # Include routers
    app.include_router(api_router, prefix="/api")

    # Health check endpoint
    @app.get("/health", tags=["health"])
    async def health_check() -> Dict[str, Any]:
        """Health check endpoint."""
        from datetime import datetime, timezone

        health_status = {
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "version": settings.service_version,
        }

        if app_state.manager:
            try:
                # Try to get system info to verify manager is working
                await app_state.manager.get_system_info()
                health_status["miniforge"] = "connected"
            except Exception as e:
                health_status["status"] = "degraded"
                health_status["miniforge"] = f"error: {str(e)}"
        else:
            health_status["status"] = "starting"

        return health_status

    # Metrics endpoint (Prometheus)
    if settings.metrics_enabled:
        metrics_app = make_asgi_app()
        app.mount("/metrics", metrics_app)

    # Setup OpenTelemetry
    setup_opentelemetry(app, settings)

    return app


# Create application instance
app = create_application()


def main() -> None:
    """Entry point for the service."""
    import uvicorn

    settings = get_settings()

    uvicorn.run(
        "miniforge_service.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        workers=1 if settings.debug else settings.workers,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    main()
