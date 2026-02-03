"""API 路由入口"""

from fastapi import APIRouter

from .routes.auth import router as auth_router
from .routes.conda import router as conda_router
from .routes.health import router as health_router
from .routes.knowledge import router as knowledge_router
from .routes.mcp import router as mcp_router
from .routes.pipelines import router as pipelines_router

router = APIRouter()


@router.get("/")
async def get_routes_info():
    """获取所有可用的 API 路由信息"""
    return {
        "routes": [
            {"path": "/api/health/status", "method": "GET", "description": "健康检查"},
            {"path": "/api/auth/login", "method": "POST", "description": "用户登录"},
            {"path": "/api/auth/register", "method": "POST", "description": "用户注册"},
            {"path": "/api/pipelines", "method": "GET", "description": "获取所有流水线"},
            {"path": "/api/pipelines", "method": "POST", "description": "创建新流水线"},
            {"path": "/api/pipelines/{id}", "method": "GET", "description": "获取流水线详情"},
            {"path": "/api/pipelines/{id}/execute", "method": "POST", "description": "执行流水线"},
            {"path": "/api/conda/envs", "method": "GET", "description": "列出所有 Conda 环境"},
            {"path": "/api/conda/packages", "method": "GET", "description": "搜索包"},
            {"path": "/api/knowledge/search", "method": "POST", "description": "知识库搜索"},
            {"path": "/api/mcp/register", "method": "POST", "description": "注册 MCP 服务"},
        ]
    }


# 包含各个路由
router.include_router(health_router, prefix="/health", tags=["Health"])
router.include_router(auth_router, prefix="/auth", tags=["Auth"])
router.include_router(pipelines_router, prefix="/pipelines", tags=["Pipelines"])
router.include_router(conda_router, prefix="/conda", tags=["Conda"])
router.include_router(knowledge_router, prefix="/knowledge", tags=["Knowledge"])
router.include_router(mcp_router, prefix="/mcp", tags=["MCP"])
