"""
BioWorkflow - 生物信息学工作流管理平台
主应用入口和配置 - Python 3.14 优化版本
"""

from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from loguru import logger

from backend.api import api_router
from backend.core.config import settings
from backend.core.logging import setup_logging
from backend.middleware import PerformanceMiddleware
from backend.middleware import RateLimitMiddleware
from backend.middleware import SecurityHeadersMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理 - 高性能初始化"""
    from backend.core.database import init_db, close_db
    from backend.infrastructure.events.event_bus import event_bus

    # 启动事件
    setup_logging()

    # 初始化数据库
    try:
        await init_db()
        logger.info("✅ Database initialized")
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        raise

    # 初始化 Redis（用于速率限制等）
    redis_client = None
    try:
        from redis.asyncio import from_url as redis_from_url

        redis_client = redis_from_url(
            settings.REDIS_URL,
            decode_responses=True,
            socket_connect_timeout=3,
        )
        await redis_client.ping()
        app.state.redis_client = redis_client
        logger.info("✅ Redis connected")
    except Exception as e:
        logger.warning(f"⚠️  Redis unavailable, using local fallback: {e}")
        app.state.redis_client = None
        redis_client = None

    logger.info(f"🚀 BioWorkflow v{settings.VERSION} started in {settings.ENVIRONMENT} mode")

    # 发布启动事件
    await event_bus.publish(
        "app.started",
        {"version": settings.VERSION, "timestamp": datetime.utcnow().isoformat()},
    )

    yield

    # 关闭事件
    logger.info("👋 BioWorkflow shutting down...")

    # 关闭 Redis
    if redis_client:
        await redis_client.aclose()
        logger.info("✅ Redis connection closed")

    # 关闭数据库
    await close_db()

    # 发布关闭事件
    await event_bus.publish(
        "app.shutdown",
        {"timestamp": datetime.utcnow().isoformat()},
    )

    logger.info("✅ Application shutdown complete")


def create_app() -> FastAPI:
    """创建 FastAPI 应用 - 高性能配置"""
    app = FastAPI(
        title="BioWorkflow API",
        description="现代生物信息学工作流管理平台 API - Python 3.14 优化",
        version=settings.VERSION,
        lifespan=lifespan,
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
        openapi_url="/openapi.json" if settings.DEBUG else None,
    )

    # 安全响应头中间件（最先添加，确保在所有响应中添加安全头）
    app.add_middleware(
        SecurityHeadersMiddleware,
        # HSTS配置（仅生产环境启用）
        hsts_max_age=31536000 if settings.ENVIRONMENT == "production" else 0,
        hsts_include_subdomains=True,
        # CSP报告模式（初期可以只报告不阻止，调优后再启用）
        csp_report_only=settings.ENVIRONMENT != "production",
    )

    # 性能监控中间件
    app.add_middleware(
        PerformanceMiddleware,
        slow_request_threshold=1.0,
    )

    # Gzip 压缩中间件
    app.add_middleware(GZipMiddleware, minimum_size=1000)

    # 速率限制中间件（Redis 在 lifespan 中注入到 app.state）
    app.add_middleware(
        RateLimitMiddleware,
        whitelist=["127.0.0.1", "::1"],  # 本地开发环境白名单
    )

    # CORS 配置
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
        allow_methods=settings.CORS_ALLOW_METHODS,
        allow_headers=settings.CORS_ALLOW_HEADERS,
    )

    # 全局异常处理
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.exception(f"Unhandled exception: {exc}")
        return JSONResponse(
            status_code=500,
            content={
                "detail": "Internal server error",
                "request_id": getattr(request.state, "request_id", None),
            },
        )

    # 包含 API 路由
    app.include_router(api_router, prefix="/api")

    # 根路径健康检查
    @app.get("/health")
    async def health_check():
        return {
            "status": "healthy",
            "version": settings.VERSION,
            "environment": settings.ENVIRONMENT,
            "timestamp": datetime.utcnow().isoformat(),
        }

    # 就绪检查
    @app.get("/ready")
    async def readiness_check():
        checks = {
            "api": True,
            "database": await _check_database(),
        }

        overall = all(checks.values())

        return {
            "status": "ready" if overall else "not_ready",
            "checks": checks,
        }

    return app


async def _check_database() -> bool:
    """检查数据库连接"""
    try:
        from backend.core.database import engine
        from sqlalchemy import text

        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


app = create_app()
