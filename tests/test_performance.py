"""
性能优化模块测试
"""

import asyncio
import time

import pytest

from backend.core.performance import (
    AsyncLRUCache,
    CircuitBreaker,
    CircuitBreakerOpen,
    ConnectionPool,
    RateLimiter,
    batch_process,
)


@pytest.mark.asyncio
async def test_async_lru_cache():
    """测试异步 LRU 缓存"""
    cache = AsyncLRUCache(maxsize=3, ttl=1)

    # 测试基本操作
    await cache.set("key1", "value1")
    assert await cache.get("key1") == "value1"

    # 测试不存在的键
    assert await cache.get("nonexistent") is None

    # 测试 LRU 淘汰
    await cache.set("key2", "value2")
    await cache.set("key3", "value3")
    await cache.set("key4", "value4")  # 应该淘汰 key1

    assert await cache.get("key1") is None
    assert await cache.get("key2") == "value2"

    # 测试 TTL
    await asyncio.sleep(1.1)
    assert await cache.get("key2") is None


@pytest.mark.asyncio
async def test_rate_limiter():
    """测试速率限制器"""
    limiter = RateLimiter(rate=2, capacity=2)  # 每秒 2 个令牌

    # 前两个请求应该立即通过
    wait1 = await limiter.acquire()
    wait2 = await limiter.acquire()
    assert wait1 == 0.0
    assert wait2 == 0.0

    # 第三个请求需要等待
    wait3 = await limiter.acquire()
    assert wait3 > 0.0


@pytest.mark.asyncio
async def test_circuit_breaker():
    """测试熔断器"""
    breaker = CircuitBreaker(
        failure_threshold=3,
        recovery_timeout=1,
    )

    call_count = 0

    async def failing_func():
        nonlocal call_count
        call_count += 1
        raise ValueError("Test error")

    # 触发熔断
    for _ in range(3):
        with pytest.raises(ValueError):
            await breaker.call(failing_func)

    # 熔断器应该打开
    with pytest.raises(CircuitBreakerOpen):
        await breaker.call(failing_func)

    assert call_count == 3


@pytest.mark.asyncio
async def test_batch_process():
    """测试批量处理"""
    processed = []

    async def processor(item: int) -> int:
        await asyncio.sleep(0.01)
        processed.append(item)
        return item * 2

    items = list(range(10))
    results = await batch_process(
        items,
        processor,
        batch_size=3,
        max_concurrency=2,
    )

    assert len(results) == 10
    assert all(r == i * 2 for i, r in enumerate(results))
    assert len(processed) == 10


@pytest.mark.asyncio
async def test_connection_pool():
    """测试连接池"""
    created = 0

    async def factory():
        nonlocal created
        created += 1
        return {"id": created}

    pool = ConnectionPool(
        factory=factory,
        max_size=3,
        max_idle=2,
    )

    # 获取连接
    conn1 = await pool.acquire()
    assert conn1["id"] == 1

    conn2 = await pool.acquire()
    assert conn2["id"] == 2

    # 释放连接
    await pool.release(conn1)

    # 再次获取应该重用
    conn3 = await pool.acquire()
    assert conn3["id"] == 1  # 重用 conn1

    await pool.release(conn2)
    await pool.release(conn3)
    await pool.close_all()
