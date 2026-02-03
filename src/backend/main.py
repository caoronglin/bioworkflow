"""
BioWorkflow - 生物信息学工作流管理平台
主应用入口和配置
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api import router as api_router
from .core.config import settings
from .core.logging import setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动事件
    setup_logging()
    print(f"🚀 BioWorkflow 应用启动 - 版本: {settings.VERSION}")
    yield
    # 关闭事件
    print("👋 BioWorkflow 应用关闭")


def create_app() -> FastAPI:
    """创建 FastAPI 应用"""
    app = FastAPI(
        title="BioWorkflow API",
        description="生物信息学工作流管理平台 API",
        version=settings.VERSION,
        lifespan=lifespan,
    )

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
        return {"status": "healthy", "version": settings.VERSION}

    return app


app = create_app()
