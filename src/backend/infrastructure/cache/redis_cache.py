"""
Redis 缓存服务实现

高性能分布式缓存
"""

import json
import pickle
from typing import Any

import redis.asyncio as redis
from loguru import logger

from backend.core.config import settings
from backend.core.interfaces import CacheService


class RedisCacheService(CacheService):
    """Redis 缓存服务实现"""

    def __init__(self):
        self._redis: redis.Redis | None = None
        self._default_ttl = 3600  # 1小时

    async def _get_redis(self) -> redis.Redis:
        """获取 Redis 连接（延迟初始化）"""
        if self._redis is None:
            self._redis = redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=False,
            )
        return self._redis

    async def get(self, key: str) -> Any | None:
        """获取缓存值"""
        try:
            r = await self._get_redis()
            data = await r.get(key)
            if data is None:
                return None
            return pickle.loads(data)
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl: int | None = None,
    ) -> None:
        """设置缓存值"""
        try:
            r = await self._get_redis()
            data = pickle.dumps(value)
            await r.setex(key, ttl or self._default_ttl, data)
        except Exception as e:
            logger.error(f"Cache set error: {e}")

    async def delete(self, key: str) -> bool:
        """删除缓存"""
        try:
            r = await self._get_redis()
            result = await r.delete(key)
            return result > 0
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            return False

    async def exists(self, key: str) -> bool:
        """检查缓存是否存在"""
        try:
            r = await self._get_redis()
            return await r.exists(key) > 0
        except Exception as e:
            logger.error(f"Cache exists error: {e}")
            return False

    async def clear(self) -> None:
        """清空缓存"""
        try:
            r = await self._get_redis()
            await r.flushdb()
        except Exception as e:
            logger.error(f"Cache clear error: {e}")

    async def close(self) -> None:
        """关闭连接"""
        if self._redis:
            await self._redis.close()
            self._redis = None


class MemoryCacheService(CacheService):
    """内存缓存服务（用于开发和测试）"""

    def __init__(self):
        self._cache: dict[str, tuple[Any, float | None]] = {}
        self._default_ttl = 3600

    async def get(self, key: str) -> Any | None:
        import time

        if key not in self._cache:
            return None

        value, expires_at = self._cache[key]
        if expires_at and time.time() > expires_at:
            del self._cache[key]
            return None

        return value

    async def set(
        self,
        key: str,
        value: Any,
        ttl: int | None = None,
    ) -> None:
        import time

        expires_at = time.time() + (ttl or self._default_ttl) if ttl != 0 else None
        self._cache[key] = (value, expires_at)

    async def delete(self, key: str) -> bool:
        if key in self._cache:
            del self._cache[key]
            return True
        return False

    async def exists(self, key: str) -> bool:
        result = await self.get(key)
        return result is not None

    async def clear(self) -> None:
        self._cache.clear()
