"""
系统管理路由

提供性能监控、健康检查和系统信息
"""

import platform
import time
from datetime import datetime
from typing import Any

import psutil
from fastapi import APIRouter, Depends

from backend.core.container import get_cache_service, get_metrics_collector
from backend.core.interfaces import CacheService, MetricsCollector
from backend.core.performance import performance_monitor
from backend.middleware.performance import query_optimizer

router = APIRouter()


@router.get("/health")
async def health_check() -> dict[str, Any]:
    """系统健康检查"""
    checks = {
        "api": True,
        "database": await _check_database(),
        "redis": await _check_redis(),
    }

    overall = all(checks.values())

    return {
        "status": "healthy" if overall else "degraded",
        "timestamp": datetime.utcnow().isoformat(),
        "checks": checks,
    }


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


async def _check_redis() -> bool:
    """检查 Redis 连接"""
    try:
        from backend.core.config import settings
        import redis.asyncio as redis

        r = redis.from_url(settings.REDIS_URL)
        await r.ping()
        await r.close()
        return True
    except Exception:
        return False


@router.get("/metrics")
async def get_metrics(
    metrics: MetricsCollector = Depends(get_metrics_collector),
) -> dict[str, Any]:
    """获取系统指标"""
    # 系统资源
    cpu_percent = psutil.cpu_percent(interval=0.1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage("/")

    # 性能指标
    perf_stats = await performance_monitor.get_all_stats()
    query_stats = query_optimizer.get_stats()

    return {
        "system": {
            "cpu_percent": cpu_percent,
            "memory": {
                "total": memory.total,
                "available": memory.available,
                "percent": memory.percent,
                "used": memory.used,
            },
            "disk": {
                "total": disk.total,
                "used": disk.used,
                "free": disk.free,
                "percent": (disk.used / disk.total) * 100,
            },
        },
        "performance": perf_stats,
        "database": query_stats,
    }


@router.get("/info")
async def system_info() -> dict[str, Any]:
    """获取系统信息"""
    return {
        "platform": {
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
        },
        "python": {
            "version": platform.python_version(),
            "implementation": platform.python_implementation(),
        },
        "timestamp": datetime.utcnow().isoformat(),
        "uptime": time.time() - psutil.boot_time(),
    }


@router.post("/cache/clear")
async def clear_cache(
    cache: CacheService = Depends(get_cache_service),
) -> dict[str, str]:
    """清除系统缓存"""
    await cache.clear()
    return {"message": "Cache cleared successfully"}


@router.get("/cache/stats")
async def cache_stats(
    cache: CacheService = Depends(get_cache_service),
) -> dict[str, Any]:
    """获取缓存统计"""
    # 这里需要根据具体缓存实现返回统计信息
    return {
        "status": "active",
        "type": cache.__class__.__name__,
    }
