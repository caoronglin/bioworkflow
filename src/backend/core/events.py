"""事件系统 - 实现模块解耦"""

import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Coroutine, TypeVar

from loguru import logger

T = TypeVar("T")


@dataclass
class Event:
    """基础事件类"""
    event_type: str
    payload: dict[str, Any]
    timestamp: datetime = None
    source: str = ""

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


# 事件处理器类型
EventHandler = Callable[[Event], Coroutine[Any, Any, None]]


class EventBus:
    """
    事件总线 - 实现发布-订阅模式，解耦模块间依赖

    使用示例:
    ```python
    # 订阅事件
    @event_bus.subscribe("pipeline.completed")
    async def on_pipeline_completed(event: Event):
        print(f"Pipeline {event.payload['pipeline_id']} completed!")

    # 发布事件
    await event_bus.publish(Event(
        event_type="pipeline.completed",
        payload={"pipeline_id": "123"}
    ))
    ```
    """

    def __init__(self):
        self._handlers: dict[str, list[EventHandler]] = {}
        self._wildcard_handlers: list[EventHandler] = []
        self._middlewares: list[Callable[[Event], Coroutine[Any, Any, Event | None]]] = []

    def subscribe(self, event_type: str) -> Callable[[EventHandler], EventHandler]:
        """
        订阅特定类型的事件

        Args:
            event_type: 事件类型，支持通配符如 "pipeline.*"
        """
        def decorator(handler: EventHandler) -> EventHandler:
            if "*" in event_type:
                # 通配符订阅
                self._wildcard_handlers.append((event_type, handler))
            else:
                if event_type not in self._handlers:
                    self._handlers[event_type] = []
                self._handlers[event_type].append(handler)
                logger.debug(f"Handler {handler.__name__} subscribed to {event_type}")
            return handler
        return decorator

    def add_middleware(self, middleware: Callable[[Event], Coroutine[Any, Any, Event | None]]):
        """添加中间件，可在事件处理前进行转换或过滤"""
        self._middlewares.append(middleware)

    async def publish(self, event: Event) -> None:
        """
        发布事件到所有订阅者

        Args:
            event: 要发布的事件
        """
        try:
            # 应用中间件
            processed_event = event
            for middleware in self._middlewares:
                processed_event = await middleware(processed_event)
                if processed_event is None:
                    # 中间件取消了事件
                    return

            # 收集所有匹配的处理器
            handlers: list[EventHandler] = []

            # 精确匹配
            if processed_event.event_type in self._handlers:
                handlers.extend(self._handlers[processed_event.event_type])

            # 通配符匹配
            for pattern, handler in self._wildcard_handlers:
                if self._match_wildcard(pattern, processed_event.event_type):
                    handlers.append(handler)

            # 并行执行所有处理器
            if handlers:
                await asyncio.gather(
                    *[self._safe_handle(handler, processed_event) for handler in handlers],
                    return_exceptions=True
                )

        except Exception as e:
            logger.error(f"Error publishing event {event.event_type}: {e}")

    async def _safe_handle(self, handler: EventHandler, event: Event) -> None:
        """安全地执行处理器，捕获异常"""
        try:
            await handler(event)
        except Exception as e:
            logger.error(f"Error in event handler {handler.__name__}: {e}")

    def _match_wildcard(self, pattern: str, event_type: str) -> bool:
        """检查事件类型是否匹配通配符模式"""
        # 简单实现，支持 * 匹配任意字符
        import fnmatch
        return fnmatch.fnmatch(event_type, pattern)


# 全局事件总线实例
event_bus = EventBus()


class EventLogger:
    """事件日志中间件"""

    @staticmethod
    async def log_events(event: Event) -> Event:
        """记录所有事件"""
        logger.info(f"Event: {event.event_type} from {event.source}")
        return event


# 注册中间件
event_bus.add_middleware(EventLogger.log_events)
