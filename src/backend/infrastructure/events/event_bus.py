"""
事件总线实现

支持内存和 Redis 两种模式
"""

import asyncio
from typing import Any, Callable

from loguru import logger

from backend.core.interfaces import EventPublisher


class EventBusPublisher(EventPublisher):
    """内存事件总线实现"""

    def __init__(self):
        self._handlers: dict[str, list[Callable]] = {}
        self._lock = asyncio.Lock()

    def subscribe(
        self,
        event_type: str,
        handler: Callable[[dict[str, Any]], Any],
    ) -> None:
        """订阅事件"""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)
        logger.debug(f"Handler subscribed to {event_type}")

    def unsubscribe(
        self,
        event_type: str,
        handler: Callable[[dict[str, Any]], Any],
    ) -> None:
        """取消订阅"""
        if event_type in self._handlers:
            self._handlers[event_type].remove(handler)

    async def publish(self, event_type: str, payload: dict[str, Any]) -> None:
        """发布事件"""
        handlers = self._handlers.get(event_type, [])

        if not handlers:
            return

        # 并发执行所有处理器
        tasks = []
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    tasks.append(handler(payload))
                else:
                    handler(payload)
            except Exception as e:
                logger.error(f"Event handler error: {e}")

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

        logger.debug(f"Event published: {event_type}")


class RedisEventPublisher(EventPublisher):
    """Redis 发布/订阅实现（用于分布式场景）"""

    def __init__(self, redis_url: str):
        self._redis_url = redis_url
        self._handlers: dict[str, list[Callable]] = {}

    def subscribe(
        self,
        event_type: str,
        handler: Callable[[dict[str, Any]], Any],
    ) -> None:
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)

    async def publish(self, event_type: str, payload: dict[str, Any]) -> None:
        import json

        import redis.asyncio as redis

        r = redis.from_url(self._redis_url)
        try:
            await r.publish(event_type, json.dumps(payload))
        finally:
            await r.close()


# 兼容旧代码的 Event 类
class Event:
    """事件对象"""

    def __init__(self, event_type: str, payload: dict[str, Any]):
        self.event_type = event_type
        self.payload = payload


# 全局事件总线实例（向后兼容）
event_bus = EventBusPublisher()


# 兼容旧代码的发布方法
async def publish_event(event: Event) -> None:
    """发布事件（兼容旧代码）"""
    await event_bus.publish(event.event_type, event.payload)
