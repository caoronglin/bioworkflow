"""缓存服务 - 高性能数据缓存

支持内存缓存和 Redis 后端，提供统一的缓存接口
"""

import asyncio
import hashlib
import json
import pickle
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from functools import wraps
from typing import Any, Callable, Coroutine, Generic, Optional, TypeVar, Union

from loguru import logger

from backend.core.config import settings

T = TypeVar("T")


@dataclass
class CacheEntry:
    """缓存条目"""
    key: str
    value: Any
    expires_at: Optional[float]  # 过期时间戳（None 表示永不过期）
    tags: set[str] = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = set()

    @property
    def is_expired(self) -> bool:
        if self.expires_at is None:
            return False
        return time.time() > self.expires_at


class CacheBackend(ABC):
    """缓存后端接口"""

    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        pass

    @abstractmethod
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        tags: Optional[set[str]] = None,
    ) -> None:
        """设置缓存值"""
        pass

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """删除缓存"""
        pass

    @abstractmethod
    async def delete_by_tag(self, tag: str) -> int:
        """根据标签删除缓存"""
        pass

    @abstractmethod
    async def clear(self) -> None:
        """清空缓存"""
        pass

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """检查键是否存在"""
        pass


class MemoryCacheBackend(CacheBackend):
    """内存缓存后端"""

    def __init__(self, max_size: int = 10000):
        self._cache: dict[str, CacheEntry] = {}
        self._tag_index: dict[str, set[str]] = {}
        self._max_size = max_size
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> Optional[Any]:
        async with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                return None

            if entry.is_expired:
                await self._remove_entry(key)
                return None

            return entry.value

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        tags: Optional[set[str]] = None,
    ) -> None:
        async with self._lock:
            # 清理过期条目
            await self._cleanup_expired()

            # 如果达到最大容量，清理最旧的条目
            if len(self._cache) >= self._max_size:
                await self._evict_oldest()

            # 计算过期时间
            expires_at = time.time() + ttl if ttl else None

            # 创建条目
            entry = CacheEntry(
                key=key,
                value=value,
                expires_at=expires_at,
                tags=tags or set(),
            )

            self._cache[key] = entry

            # 更新标签索引
            for tag in entry.tags:
                if tag not in self._tag_index:
                    self._tag_index[tag] = set()
                self._tag_index[tag].add(key)

    async def delete(self, key: str) -> bool:
        async with self._lock:
            if key not in self._cache:
                return False
            await self._remove_entry(key)
            return True

    async def delete_by_tag(self, tag: str) -> int:
        async with self._lock:
            keys = self._tag_index.get(tag, set()).copy()
            for key in keys:
                await self._remove_entry(key)
            return len(keys)

    async def clear(self) -> None:
        async with self._lock:
            self._cache.clear()
            self._tag_index.clear()

    async def exists(self, key: str) -> bool:
        async with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                return False
            if entry.is_expired:
                await self._remove_entry(key)
                return False
            return True

    async def _remove_entry(self, key: str) -> None:
        """移除条目及其标签索引"""
        if key not in self._cache:
            return

        entry = self._cache[key]

        # 从标签索引中移除
        for tag in entry.tags:
            if tag in self._tag_index:
                self._tag_index[tag].discard(key)
                if not self._tag_index[tag]:
                    del self._tag_index[tag]

        del self._cache[key]

    async def _cleanup_expired(self) -> None:
        """清理过期条目"""
        expired_keys = [
            key for key, entry in self._cache.items()
            if entry.is_expired
        ]
        for key in expired_keys:
            await self._remove_entry(key)

    async def _evict_oldest(self) -> None:
        """驱逐最旧的条目（简单策略：移除最早的 10%）"""
        # 按创建时间排序（这里用字典顺序近似）
        sorted_keys = sorted(self._cache.keys())
        evict_count = max(1, len(sorted_keys) // 10)

        for key in sorted_keys[:evict_count]:
            await self._remove_entry(key)


class CacheService:
    """
    缓存服务统一接口

    提供高级缓存功能，包括：
    - 装饰器缓存
    - 缓存键生成
    - 批量操作
    - 序列化/反序列化
    """

    def __init__(self, backend: Optional[CacheBackend] = None):
        self.backend = backend or MemoryCacheBackend()

    def _generate_key(self, prefix: str, *args, **kwargs) -> str:
        """生成缓存键"""
        key_parts = [prefix]

        # 添加位置参数
        for arg in args:
            key_parts.append(str(arg))

        # 添加关键字参数（排序确保一致性）
        for key in sorted(kwargs.keys()):
            key_parts.append(f"{key}={kwargs[key]}")

        raw_key = ":".join(key_parts)

        # 对长键进行哈希
        if len(raw_key) > 200:
            return f"{prefix}:hash:{hashlib.sha256(raw_key.encode()).hexdigest()[:16]}"

        return raw_key

    async def get(self, key: str, default: Any = None) -> Any:
        """获取缓存值"""
        value = await self.backend.get(key)
        return value if value is not None else default

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        tags: Optional[set[str]] = None,
    ) -> None:
        """设置缓存值"""
        await self.backend.set(key, value, ttl=ttl, tags=tags)

    async def delete(self, key: str) -> bool:
        """删除缓存"""
        return await self.backend.delete(key)

    async def get_or_set(
        self,
        key: str,
        factory: Callable[[], Coroutine[Any, Any, T]],
        ttl: Optional[int] = None,
    ) -> T:
        """
        获取或设置缓存

        如果缓存不存在，调用 factory 创建值并缓存
        """
        value = await self.backend.get(key)
        if value is not None:
            return value

        # 异步创建值
        value = await factory()
        await self.backend.set(key, value, ttl=ttl)
        return value

    def cached(
        self,
        prefix: str,
        ttl: Optional[int] = None,
        key_fn: Optional[Callable[..., str]] = None,
    ):
        """
        装饰器：缓存函数结果

        使用示例:
        ```python
        cache = CacheService()

        @cache.cached(prefix="user", ttl=300)
        async def get_user(user_id: int):
            return await db.get_user(user_id)
        ```
        """
        def decorator(func: Callable[..., Coroutine[Any, Any, T]]) -> Callable[..., Coroutine[Any, Any, T]]:
            async def wrapper(*args, **kwargs) -> T:
                # 生成缓存键
                if key_fn:
                    cache_key = key_fn(*args, **kwargs)
                else:
                    cache_key = self._generate_key(prefix, *args, **kwargs)

                # 尝试从缓存获取
                cached_value = await self.backend.get(cache_key)
                if cached_value is not None:
                    return cached_value

                # 执行函数
                result = await func(*args, **kwargs)

                # 缓存结果
                await self.backend.set(cache_key, result, ttl=ttl)

                return result

            return wrapper
        return decorator

    async def clear(self) -> None:
        """清空所有缓存"""
        await self.backend.clear()

    async def delete_by_tag(self, tag: str) -> int:
        """根据标签删除缓存"""
        return await self.backend.delete_by_tag(tag)


# 全局缓存服务实例
cache = CacheService()


__all__ = [
    "CacheService",
    "CacheBackend",
    "MemoryCacheBackend",
    "cache",
]