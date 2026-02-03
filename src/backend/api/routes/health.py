"""健康检查路由"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/status")
async def health_status():
    """获取应用健康状态"""
    return {
        "status": "healthy",
        "message": "BioWorkflow 运行正常",
    }
