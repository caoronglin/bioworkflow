"""API 路由定义"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def get_routes_info():
    """获取所有可用的 API 路由信息"""
    return {
        "routes": [
            {"path": "/api/health", "method": "GET", "description": "健康检查"},
            {"path": "/api/auth/login", "method": "POST", "description": "用户登录"},
            {"path": "/api/auth/register", "method": "POST", "description": "用户注册"},
            {"path": "/api/pipelines", "method": "GET", "description": "获取所有流水线"},
            {"path": "/api/pipelines", "method": "POST", "description": "创建新流水线"},
            {"path": "/api/pipelines/{id}", "method": "GET", "description": "获取流水线详情"},
            {"path": "/api/pipelines/{id}/execute", "method": "POST", "description": "执行流水线"},
            {"path": "/api/conda/envs", "method": "GET", "description": "列出所有 Conda 环境"},
            {"path": "/api/conda/packages", "method": "GET", "description": "列出包"},
            {"path": "/api/knowledge/search", "method": "POST", "description": "知识库搜索"},
            {"path": "/api/mcp/register", "method": "POST", "description": "注册 MCP 服务"},
        ]
    }
