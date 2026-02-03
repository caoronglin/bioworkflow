"""
BioWorkflow - 生物信息学工作流管理平台
主应用入口和配置
"""

from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from loguru import logger

from .api import router as api_router
from .core.config import settings
from .core.logging import setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理 - 高性能初始化"""
    from backend.core.database import init_db, close_db
    from backend.core.events import event_bus

    # 启动事件
    setup_logging()

    # 初始化数据库
    try:
        await init_db()
        logger.info("✅ 数据库初始化完成")
    except Exception as e:
        logger.error(f"❌ 数据库初始化失败: {e}")
        raise

    logger.info(f"🚀 BioWorkflow 应用启动 - 版本: {settings.VERSION}")

    # 发布启动事件
    await event_bus.publish(event_bus.Event(
        event_type="app.started",
        payload={"version": settings.VERSION, "timestamp": str(datetime.utcnow())},
    ))

    yield

    # 关闭事件
    logger.info("👋 BioWorkflow 应用关闭中...")

    # 关闭数据库
    await close_db()

    # 发布关闭事件
    await event_bus.publish(event_bus.Event(
        event_type="app.shutdown",
        payload={"timestamp": str(datetime.utcnow())},
    ))

    logger.info("✅ 应用已安全关闭")


def create_app() -> FastAPI:
    """创建 FastAPI 应用 - 高性能配置"""
    app = FastAPI(
        title="BioWorkflow API",
        description="生物信息学工作流管理平台 API - 高性能、模块化、易扩展",
        version=settings.VERSION,
        lifespan=lifespan,
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
        openapi_url="/openapi.json" if settings.DEBUG else None,
    )

    # 全局异常处理中间件
    @app.middleware("http")
    async def exception_middleware(request: Request, call_next):
        try:
            return await call_next(request)
        except Exception as exc:
            logger.exception(f"Unhandled exception: {exc}")
            return JSONResponse(
                status_code=500,
                content={"detail": "Internal server error"},
            )

    # 请求日志中间件
    @app.middleware("http")
    async def logging_middleware(request: Request, call_next):
        start_time = datetime.utcnow()
        response = await call_next(request)
        duration = (datetime.utcnow() - start_time).total_seconds()
        logger.info(
            f"{request.method} {request.url.path} - {response.status_code} - {duration:.3f}s"
        )
        return response

    # Gzip 压缩中间件
    app.add_middleware(GZipMiddleware, minimum_size=1000)

    # CORS 配置
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 包含 API 路由
    app.include_router(api_router, prefix="/api")

    # 根路径健康检查端点
    @app.get("/health")
    async def health_check():
        return {
            "status": "healthy",
            "version": settings.VERSION,
            "timestamp": datetime.utcnow().isoformat(),
        }

    # 详细健康检查端点
    @app.get("/health/detailed")
    async def detailed_health_check():
        checks = {
            "api": True,
            "database": False,
        }

        # 检查数据库
        try:
            from backend.core.database import engine
            async with engine.connect() as conn:
                await conn.execute("SELECT 1")
            checks["database"] = True
        except Exception as e:
            logger.warning(f"Database health check failed: {e}")

        overall = all(checks.values())

        return {
            "status": "healthy" if overall else "degraded",
            "version": settings.VERSION,
            "timestamp": datetime.utcnow().isoformat(),
            "checks": checks,
        }

    return app


app = create_app()
