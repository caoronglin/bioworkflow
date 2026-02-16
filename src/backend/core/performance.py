"""
性能优化工具 - Python 3.14 优化版本

提供缓存、连接池、异步优化等功能
"""

import asyncio
import functools
import hashlib
import json
import time
from collections import deque
from contextlib import asynccontextmanager
from typing import Any, Callable, TypeVar

from loguru import logger

T = TypeVar("T")


class AsyncLRUCache:
    """
    异步 LRU 缓存

    支持 TTL 和最大容量限制
    """

    def __init__(self, maxsize: int = 128, ttl: int | None = None):
        self.maxsize = maxsize
        self.ttl = ttl
        self._cache: dict[str, tuple[Any, float]] = {}
        self._access_order: deque[str] = deque()
        self._lock = asyncio.Lock()

    def _make_key(self, args: tuple, kwargs: dict) -> str:
        """生成缓存键"""
        key_data = json.dumps({"args": args, "kwargs": kwargs}, sort_keys=True, default=str)
        return hashlib.md5(key_data.encode()).hexdigest()

    async def get(self, key: str) -> Any | None:
        """获取缓存值"""
        async with self._lock:
            if key not in self._cache:
                return None

            value, timestamp = self._cache[key]

            # 检查 TTL
            if self.ttl and time.time() - timestamp > self.ttl:
                del self._cache[key]
                self._access_order.remove(key)
                return None

            # 更新访问顺序
            self._access_order.remove(key)
            self._access_order.append(key)

            return value

    async def set(self, key: str, value: Any) -> None:
        """设置缓存值"""
        async with self._lock:
            # 如果已存在，更新访问顺序
            if key in self._cache:
                self._access_order.remove(key)

            # 检查容量
            while len(self._cache) >= self.maxsize:
                oldest_key = self._access_order.popleft()
                del self._cache[oldest_key]

            # 添加新值
            self._cache[key] = (value, time.time())
            self._access_order.append(key)

    async def delete(self, key: str) -> bool:
        """删除缓存"""
        async with self._lock:
            if key in self._cache:
                del self._cache[key]
                self._access_order.remove(key)
                return True
            return False

    async def clear(self) -> None:
        """清空缓存"""
        async with self._lock:
            self._cache.clear()
            self._access_order.clear()


def async_cache(maxsize: int = 128, ttl: int | None = None):
    """
    异步函数缓存装饰器

    Args:
        maxsize: 最大缓存条目数
        ttl: 缓存过期时间（秒）
    """
    cache = AsyncLRUCache(maxsize=maxsize, ttl=ttl)

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            # 生成缓存键（排除 self/cls）
            cache_args = args[1:] if args and hasattr(args[0], '__class__') else args
            key = cache._make_key(cache_args, kwargs)

            # 尝试获取缓存
            cached_value = await cache.get(key)
            if cached_value is not None:
                return cached_value

            # 执行函数
            result = await func(*args, **kwargs)

            # 缓存结果
            await cache.set(key, result)

            return result

        # 添加缓存管理方法
        wrapper.cache = cache
        wrapper.cache_clear = cache.clear
        wrapper.cache_info = lambda: {
            "size": len(cache._cache),
            "maxsize": maxsize,
            "ttl": ttl,
        }

        return wrapper

    return decorator


class ConnectionPool:
    """
    通用连接池

    管理可重用连接的池
    """

    def __init__(
        self,
        factory: Callable[[], Any],
        max_size: int = 10,
        max_idle: int = 5,
        idle_timeout: int = 300,
    ):
        self.factory = factory
        self.max_size = max_size
        self.max_idle = max_idle
        self.idle_timeout = idle_timeout

        self._pool: deque[tuple[Any, float]] = deque()
        self._in_use: set[Any] = set()
        self._lock = asyncio.Lock()
        self._semaphore = asyncio.Semaphore(max_size)

    async def acquire(self) -> Any:
        """获取连接"""
        async with self._semaphore:
            async with self._lock:
                # 尝试获取空闲连接
                while self._pool:
                    conn, timestamp = self._pool.popleft()
                    if time.time() - timestamp < self.idle_timeout:
                        self._in_use.add(conn)
                        return conn
                    # 连接过期，关闭它
                    await self._close_connection(conn)

            # 创建新连接
            conn = await self.factory()
            async with self._lock:
                self._in_use.add(conn)
            return conn

    async def release(self, conn: Any) -> None:
        """释放连接"""
        async with self._lock:
            if conn in self._in_use:
                self._in_use.remove(conn)

            # 如果空闲连接过多，直接关闭
            if len(self._pool) >= self.max_idle:
                await self._close_connection(conn)
            else:
                self._pool.append((conn, time.time()))

        self._semaphore.release()

    async def _close_connection(self, conn: Any) -> None:
        """关闭连接"""
        if hasattr(conn, 'close'):
            if asyncio.iscoroutinefunction(conn.close):
                await conn.close()
            else:
                conn.close()

    @asynccontextmanager
    async def connection(self):
        """连接上下文管理器"""
        conn = await self.acquire()
        try:
            yield conn
        finally:
            await self.release(conn)

    async def close_all(self) -> None:
        """关闭所有连接"""
        async with self._lock:
            for conn, _ in self._pool:
                await self._close_connection(conn)
            self._pool.clear()

            for conn in list(self._in_use):
                await self._close_connection(conn)
            self._in_use.clear()


class RateLimiter:
    """
    异步速率限制器

    基于令牌桶算法
    """

    def __init__(self, rate: int, capacity: int | None = None):
        """
        Args:
            rate: 每秒生成的令牌数
            capacity: 桶容量（默认为 rate）
        """
        self.rate = rate
        self.capacity = capacity or rate
        self._tokens = self.capacity
        self._last_update = time.monotonic()
        self._lock = asyncio.Lock()

    async def acquire(self, tokens: int = 1) -> float:
        """
        获取令牌

        Returns:
            等待时间
        """
        async with self._lock:
            now = time.monotonic()
            elapsed = now - self._last_update
            self._tokens = min(self.capacity, self._tokens + elapsed * self.rate)
            self._last_update = now

            if self._tokens >= tokens:
                self._tokens -= tokens
                return 0.0

            # 计算等待时间
            wait_time = (tokens - self._tokens) / self.rate
            self._tokens = 0
            return wait_time

    async def __aenter__(self):
        wait_time = await self.acquire()
        if wait_time > 0:
            await asyncio.sleep(wait_time)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


class CircuitBreaker:
    """
    熔断器模式

    防止级联故障
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: type[Exception] = Exception,
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception

        self._failures = 0
        self._last_failure_time: float | None = None
        self._state = "closed"  # closed, open, half-open
        self._lock = asyncio.Lock()

    async def call(self, func: Callable[..., T], *args, **kwargs) -> T:
        """调用受保护的函数"""
        async with self._lock:
            if self._state == "open":
                if self._last_failure_time and time.time() - self._last_failure_time > self.recovery_timeout:
                    self._state = "half-open"
                    self._failures = 0
                else:
                    raise CircuitBreakerOpen("Circuit breaker is open")

        try:
            result = await func(*args, **kwargs)

            async with self._lock:
                if self._state == "half-open":
                    self._state = "closed"
                    self._failures = 0

            return result

        except self.expected_exception as e:
            async with self._lock:
                self._failures += 1
                self._last_failure_time = time.time()

                if self._failures >= self.failure_threshold:
                    self._state = "open"
                    logger.warning(f"Circuit breaker opened after {self._failures} failures")

            raise


class CircuitBreakerOpen(Exception):
    """熔断器打开异常"""
    pass


class PerformanceMonitor:
    """
    性能监控器

    收集和报告性能指标
    """

    def __init__(self, window_size: int = 100):
        self.window_size = window_size
        self._metrics: dict[str, deque[float]] = {}
        self._counts: dict[str, int] = {}
        self._lock = asyncio.Lock()

    async def record(self, name: str, value: float) -> None:
        """记录指标"""
        async with self._lock:
            if name not in self._metrics:
                self._metrics[name] = deque(maxlen=self.window_size)
                self._counts[name] = 0

            self._metrics[name].append(value)
            self._counts[name] += 1

    async def get_stats(self, name: str) -> dict[str, float]:
        """获取统计信息"""
        async with self._lock:
            if name not in self._metrics or not self._metrics[name]:
                return {"count": 0, "avg": 0, "min": 0, "max": 0, "p95": 0}

            values = list(self._metrics[name])
            sorted_values = sorted(values)

            return {
                "count": self._counts[name],
                "avg": sum(values) / len(values),
                "min": min(values),
                "max": max(values),
                "p95": sorted_values[int(len(sorted_values) * 0.95)],
            }

    async def get_all_stats(self) -> dict[str, dict[str, float]]:
        """获取所有统计信息"""
        async with self._lock:
            result = {}
            for name in self._metrics:
                result[name] = await self.get_stats(name)
            return result


# 全局性能监控器
performance_monitor = PerformanceMonitor()


def measure_performance(name: str | None = None):
    """
    性能测量装饰器

    测量函数执行时间并记录
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        metric_name = name or func.__name__

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> T:
            start = time.perf_counter()
            try:
                return await func(*args, **kwargs)
            finally:
                elapsed = time.perf_counter() - start
                await performance_monitor.record(metric_name, elapsed)

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs) -> T:
            start = time.perf_counter()
            try:
                return func(*args, **kwargs)
            finally:
                elapsed = time.perf_counter() - start
                # 同步函数使用 asyncio.run_coroutine_threadsafe 或忽略
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        asyncio.create_task(performance_monitor.record(metric_name, elapsed))
                except RuntimeError:
                    pass

        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

    return decorator


# 批量处理工具
async def batch_process(
    items: list[T],
    processor: Callable[[T], Any],
    batch_size: int = 100,
    max_concurrency: int = 10,
) -> list[Any]:
    """
    批量处理项目

    Args:
        items: 要处理的项目列表
        processor: 处理函数
        batch_size: 每批大小
        max_concurrency: 最大并发数

    Returns:
        处理结果列表
    """
    semaphore = asyncio.Semaphore(max_concurrency)
    results = []

    async def process_with_limit(item: T) -> Any:
        async with semaphore:
            return await processor(item)

    # 分批处理
    for i in range(0, len(items), batch_size):
        batch = items[i:i + batch_size]
        batch_results = await asyncio.gather(
            *[process_with_limit(item) for item in batch],
            return_exceptions=True,
        )
        results.extend(batch_results)

    return results
