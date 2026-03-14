"""
插件钩子系统 - 基于事件总线扩展

提供标准化的钩子点定义和优先级支持，允许插件
在系统生命周期的关键点插入自定义逻辑。

标准钩子点:
    - workflow.execute.pre: 工作流执行前
    - workflow.execute.post: 工作流执行后
    - workflow.execute.error: 工作流执行出错
    - pipeline.created: 流水线创建后
    - pipeline.deleted: 流水线删除后
    - system.startup: 系统启动时
    - system.shutdown: 系统关闭时

使用示例:
    ```python
    from backend.core.plugin.hooks import HookRegistry, HookPriority

    # 获取钩子注册表
    hooks = HookRegistry.get_instance()

    # 注册钩子（带优先级）
    @hooks.register("workflow.execute.pre", priority=HookPriority.HIGH)
    async def on_workflow_pre(event: Event) -> None:
        print(f"Workflow about to execute: {event.payload['id']}")

    # 触发钩子
    await hooks.emit("workflow.execute.pre", {"id": "123"})

    # 移除钩子
    hooks.unregister("workflow.execute.pre", on_workflow_pre)
    ```
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from enum import IntEnum
from typing import Any, Callable, Coroutine

from loguru import logger

from backend.core.events import Event, EventBus, event_bus
from backend.core.plugin.exceptions import PluginHookError


class HookPriority(IntEnum):
    """
    钩子优先级枚举

    数值越小优先级越高，相同优先级按注册顺序执行。

    Attributes:
        CRITICAL: 关键优先级（100）- 系统级钩子
        HIGH: 高优先级（200）- 重要业务逻辑
        NORMAL: 普通优先级（300）- 默认优先级
        LOW: 低优先级（400）- 可选功能
    """

    CRITICAL = 100
    HIGH = 200
    NORMAL = 300
    LOW = 400


@dataclass
class HookRegistration:
    """
    钩子注册信息

    Attributes:
        hook_type: 钩子类型（事件类型）
        handler: 处理函数
        priority: 优先级
        plugin_id: 注册插件 ID
        created_at: 注册时间
        enabled: 是否启用
    """

    hook_type: str
    handler: Callable[[Event], Coroutine[Any, Any, None]]
    priority: int = HookPriority.NORMAL
    plugin_id: str | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    enabled: bool = True

    def __lt__(self, other: "HookRegistration") -> bool:
        """用于排序：优先级高的先执行"""
        if self.priority != other.priority:
            return self.priority < other.priority
        return self.created_at < other.created_at


class HookRegistry:
    """
    钩子注册表 - 管理所有钩子的注册和执行

    基于事件总线构建，提供：
    - 优先级支持：控制钩子执行顺序
    - 插件关联：跟踪钩子来源插件
    - 动态启用/禁用：运行时控制钩子
    - 错误隔离：单个钩子失败不影响其他钩子

    Example:
        ```python
        hooks = HookRegistry.get_instance()

        # 注册钩子
        @hooks.register("workflow.execute.pre")
        async def validate_workflow(event: Event) -> None:
            if not event.payload.get("valid"):
                raise ValueError("Invalid workflow")

        # 注册带优先级的钩子
        @hooks.register("workflow.execute.pre", priority=HookPriority.HIGH)
        async def log_workflow(event: Event) -> None:
            logger.info(f"Executing workflow: {event.payload['id']}")

        # 触发钩子
        try:
            await hooks.emit("workflow.execute.pre", {"id": "123", "valid": True})
        except PluginHookError as e:
            logger.error(f"Hook execution failed: {e}")

        # 禁用特定插件的所有钩子
        hooks.disable_plugin_hooks("my-plugin")
        ```
    """

    _instance: "HookRegistry | None" = None

    def __new__(cls) -> "HookRegistry":
        """单例模式实现"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        """初始化钩子注册表"""
        if self._initialized:
            return

        self._hooks: dict[str, list[HookRegistration]] = {}
        self._event_bus: EventBus = event_bus
        self._logger = logger.bind(module="hook_registry")
        self._initialized = True

    @classmethod
    def get_instance(cls) -> "HookRegistry":
        """
        获取钩子注册表单例

        Returns:
            HookRegistry: 单例实例
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """重置单例（用于测试）"""
        if cls._instance:
            cls._instance._hooks.clear()
        cls._instance = None

    def register(
        self,
        hook_type: str,
        priority: int | HookPriority = HookPriority.NORMAL,
        plugin_id: str | None = None,
    ) -> Callable[
        [Callable[[Event], Coroutine[Any, Any, None]]],
        Callable[[Event], Coroutine[Any, Any, None]],
    ]:
        """
        注册钩子处理器

        Args:
            hook_type: 钩子类型（事件类型）
            priority: 优先级，数值越小优先级越高
            plugin_id: 可选的插件 ID，用于跟踪来源

        Returns:
            装饰器函数

        Raises:
            ValueError: 钩子类型无效

        Example:
            ```python
            @hooks.register("workflow.execute.pre", priority=HookPriority.HIGH)
            async def on_workflow_pre(event: Event) -> None:
                logger.info(f"Workflow {event.payload['id']} starting")
            ```
        """
        if isinstance(priority, HookPriority):
            priority_value = priority.value
        else:
            priority_value = priority

        def decorator(
            handler: Callable[[Event], Coroutine[Any, Any, None]],
        ) -> Callable[[Event], Coroutine[Any, Any, None]]:
            registration = HookRegistration(
                hook_type=hook_type,
                handler=handler,
                priority=priority_value,
                plugin_id=plugin_id,
            )

            if hook_type not in self._hooks:
                self._hooks[hook_type] = []

            self._hooks[hook_type].append(registration)
            # 保持排序
            self._hooks[hook_type].sort()

            # 同时在事件总线注册（用于通配符订阅）
            self._event_bus.subscribe(hook_type)(handler)

            self._logger.debug(
                f"Hook registered: {hook_type} (priority={priority_value}, plugin={plugin_id})"
            )
            return handler

        return decorator

    def unregister(
        self, hook_type: str, handler: Callable[[Event], Coroutine[Any, Any, None]]
    ) -> bool:
        """
        注销钩子处理器

        Args:
            hook_type: 钩子类型
            handler: 处理函数

        Returns:
            bool: 是否成功注销
        """
        if hook_type not in self._hooks:
            return False

        original_count = len(self._hooks[hook_type])
        self._hooks[hook_type] = [
            reg for reg in self._hooks[hook_type] if reg.handler != handler
        ]

        if len(self._hooks[hook_type]) < original_count:
            self._logger.debug(f"Hook unregistered: {hook_type}")
            return True

        return False

    def unregister_all(self, hook_type: str) -> int:
        """
        注销某类型的所有钩子

        Args:
            hook_type: 钩子类型

        Returns:
            int: 注销的钩子数量
        """
        if hook_type not in self._hooks:
            return 0

        count = len(self._hooks[hook_type])
        del self._hooks[hook_type]
        self._logger.debug(f"All hooks unregistered: {hook_type} ({count} hooks)")
        return count

    async def emit(self, hook_type: str, payload: dict[str, Any]) -> None:
        """
        触发钩子

        按优先级顺序执行所有注册的处理器。
        支持短路：如果处理器抛出 HookInterrupt 异常，后续处理器不会执行。

        Args:
            hook_type: 钩子类型
            payload: 事件载荷

        Raises:
            PluginHookError: 钩子执行失败

        Example:
            ```python
            await hooks.emit("workflow.execute.pre", {
                "workflow_id": "123",
                "user": "admin"
            })
            ```
        """
        if hook_type not in self._hooks or not self._hooks[hook_type]:
            return

        event = Event(event_type=hook_type, payload=payload)
        handlers = [reg for reg in self._hooks[hook_type] if reg.enabled]

        if not handlers:
            self._logger.debug(f"No enabled handlers for hook: {hook_type}")
            return

        self._logger.debug(f"Emitting hook: {hook_type} ({len(handlers)} handlers)")

        errors = []
        for reg in handlers:
            try:
                await reg.handler(event)
            except HookInterrupt as e:
                # 短路：中断后续执行
                self._logger.info(f"Hook interrupted: {hook_type} by {e.reason}")
                return
            except Exception as e:
                # 记录错误但继续执行其他处理器
                error_msg = (
                    f"Error in hook {hook_type} "
                    f"(plugin={reg.plugin_id}, priority={reg.priority}): {e}"
                )
                self._logger.error(error_msg)
                errors.append((reg, e))

        if errors:
            raise PluginHookError(
                f"{len(errors)} hook handler(s) failed for {hook_type}"
            )

    async def emit_with_timeout(
        self, hook_type: str, payload: dict[str, Any], timeout: float = 5.0
    ) -> None:
        """
        带超时控制的钩子触发

        Args:
            hook_type: 钩子类型
            payload: 事件载荷
            timeout: 超时时间（秒）

        Raises:
            PluginHookError: 钩子执行失败或超时
        """
        try:
            await asyncio.wait_for(
                self.emit(hook_type, payload), timeout=timeout
            )
        except asyncio.TimeoutError:
            raise PluginHookError(
                f"Hook execution timed out after {timeout}s: {hook_type}"
            )

    def enable_hook(self, hook_type: str, handler: Callable) -> bool:
        """
        启用特定钩子

        Args:
            hook_type: 钩子类型
            handler: 处理函数

        Returns:
            bool: 是否成功启用
        """
        if hook_type not in self._hooks:
            return False

        for reg in self._hooks[hook_type]:
            if reg.handler == handler:
                reg.enabled = True
                self._logger.debug(f"Hook enabled: {hook_type}")
                return True

        return False

    def disable_hook(self, hook_type: str, handler: Callable) -> bool:
        """
        禁用特定钩子

        Args:
            hook_type: 钩子类型
            handler: 处理函数

        Returns:
            bool: 是否成功禁用
        """
        if hook_type not in self._hooks:
            return False

        for reg in self._hooks[hook_type]:
            if reg.handler == handler:
                reg.enabled = False
                self._logger.debug(f"Hook disabled: {hook_type}")
                return True

        return False

    def enable_plugin_hooks(self, plugin_id: str) -> int:
        """
        启用插件的所有钩子

        Args:
            plugin_id: 插件 ID

        Returns:
            int: 启用的钩子数量
        """
        count = 0
        for hook_type, registrations in self._hooks.items():
            for reg in registrations:
                if reg.plugin_id == plugin_id and not reg.enabled:
                    reg.enabled = True
                    count += 1

        self._logger.debug(f"Enabled {count} hooks for plugin: {plugin_id}")
        return count

    def disable_plugin_hooks(self, plugin_id: str) -> int:
        """
        禁用插件的所有钩子

        Args:
            plugin_id: 插件 ID

        Returns:
            int: 禁用的钩子数量
        """
        count = 0
        for hook_type, registrations in self._hooks.items():
            for reg in registrations:
                if reg.plugin_id == plugin_id and reg.enabled:
                    reg.enabled = False
                    count += 1

        self._logger.debug(f"Disabled {count} hooks for plugin: {plugin_id}")
        return count

    def get_hooks(self, hook_type: str) -> list[HookRegistration]:
        """
        获取某类型的所有钩子

        Args:
            hook_type: 钩子类型

        Returns:
            list[HookRegistration]: 钩子注册列表
        """
        return self._hooks.get(hook_type, []).copy()

    def list_all_hooks(self) -> dict[str, int]:
        """
        列出所有注册的钩子类型及其数量

        Returns:
            dict[str, int]: 钩子类型 -> 数量的映射
        """
        return {hook_type: len(regs) for hook_type, regs in self._hooks.items()}

    def list_plugin_hooks(self, plugin_id: str) -> list[HookRegistration]:
        """
        列出插件注册的所有钩子

        Args:
            plugin_id: 插件 ID

        Returns:
            list[HookRegistration]: 插件的钩子列表
        """
        result = []
        for registrations in self._hooks.values():
            for reg in registrations:
                if reg.plugin_id == plugin_id:
                    result.append(reg)
        return result


class HookInterrupt(Exception):
    """
    钩子中断异常

    当钩子处理器抛出此异常时，会中断后续钩子的执行。
    用于实现短路逻辑，如验证失败时阻止后续操作。

    Attributes:
        reason: 中断原因
        data: 附加数据

    Example:
        ```python
        @hooks.register("workflow.execute.pre")
        async def validate(event: Event) -> None:
            if not event.payload.get("authorized"):
                raise HookInterrupt("Unauthorized access")
        ```
    """

    def __init__(self, reason: str, data: Any = None) -> None:
        self.reason = reason
        self.data = data
        super().__init__(reason)


# ========== 标准钩子点定义 ==========


class StandardHooks:
    """
    标准钩子点常量定义

    提供系统预定义的钩子点，插件可以在这些点插入逻辑。

    钩子点分类:
        1. 工作流生命周期
        2. 流水线管理
        3. 系统事件
        4. 用户操作
    """

    # 工作流执行钩子
    WORKFLOW_EXECUTE_PRE = "workflow.execute.pre"
    WORKFLOW_EXECUTE_POST = "workflow.execute.post"
    WORKFLOW_EXECUTE_ERROR = "workflow.execute.error"

    # 流水线管理钩子
    PIPELINE_CREATED = "pipeline.created"
    PIPELINE_UPDATED = "pipeline.updated"
    PIPELINE_DELETED = "pipeline.deleted"
    PIPELINE_STARTED = "pipeline.started"
    PIPELINE_COMPLETED = "pipeline.completed"
    PIPELINE_FAILED = "pipeline.failed"

    # 系统事件钩子
    SYSTEM_STARTUP = "system.startup"
    SYSTEM_SHUTDOWN = "system.shutdown"
    SYSTEM_CONFIG_CHANGED = "system.config.changed"

    # 用户操作钩子
    USER_LOGIN = "user.login"
    USER_LOGOUT = "user.logout"
    USER_CREATED = "user.created"
    USER_DELETED = "user.deleted"

    # 环境管理钩子
    ENVIRONMENT_CREATED = "environment.created"
    ENVIRONMENT_DELETED = "environment.deleted"
    PACKAGES_INSTALLED = "packages.installed"

    # 文件操作钩子
    FILE_UPLOADED = "file.uploaded"
    FILE_DELETED = "file.deleted"

    @classmethod
    def all(cls) -> list[str]:
        """获取所有标准钩子点"""
        return [
            getattr(cls, attr)
            for attr in dir(cls)
            if attr.isupper() and not attr.startswith("_")
        ]

    @classmethod
    def is_standard(cls, hook_type: str) -> bool:
        """检查是否为标准钩子点"""
        return hook_type in cls.all()


# ========== 初始化钩子中间件 ==========


async def hook_middleware(event: Event) -> Event | None:
    """
    事件总线中间件 - 触发钩子

    作为事件总线的中间件，在事件处理前触发相应的钩子。

    Args:
        event: 输入事件

    Returns:
        Event | None: 处理后的事件，None 表示取消事件
    """
    hooks = HookRegistry.get_instance()

    # 获取该事件类型的钩子
    if event.event_type in hooks._hooks:
        try:
            await hooks.emit(event.event_type, event.payload)
        except PluginHookError as e:
            logger.warning(f"Hook execution failed: {e}")
            # 不阻断事件处理，只记录警告

    return event


# 注册中间件到事件总线
event_bus.add_middleware(hook_middleware)
