"""
插件抽象基类 - 定义插件的基本结构和生命周期

参考 Obsidian 插件系统架构，提供：
- 插件生命周期管理
- 元数据定义
- 扩展点注册
- 资源自动清理

使用示例:
    ```python
    from backend.core.plugin.base import Plugin, PluginManifest

    class MyPlugin(Plugin):
        manifest = PluginManifest(
            id="my-plugin",
            name="My Plugin",
            version="1.0.0",
            description="A sample plugin",
            author="Your Name"
        )

        async def on_load(self) -> None:
            # 插件加载时初始化
            self.register_command("my-cmd", self.execute)

        async def execute(self, args: dict) -> dict:
            return {"status": "success"}
    ```
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Coroutine

from loguru import logger


class PluginState(Enum):
    """
    插件状态枚举

    Attributes:
        UNLOADED: 未加载
        LOADED: 已加载
        ENABLED: 已启用
        DISABLED: 已禁用
        ERROR: 错误状态
    """

    UNLOADED = "unloaded"
    LOADED = "loaded"
    ENABLED = "enabled"
    DISABLED = "disabled"
    ERROR = "error"


@dataclass
class PluginManifest:
    """
    插件元数据定义

    包含插件的所有描述信息，用于插件发现、依赖解析和 UI 展示。

    Attributes:
        id: 插件唯一标识符（推荐格式：author-plugin-name）
        name: 插件显示名称
        version: 语义化版本号（遵循 SemVer）
        description: 插件描述
        author: 作者信息
        min_version: 要求的最小系统版本
        max_version: 要求的最大系统版本
        dependencies: 依赖的插件 ID 列表
        tags: 插件标签用于分类
        homepage: 项目主页 URL
        repository: 代码仓库 URL
        license: 许可证类型
        icon: 图标名称或 URL
    """

    id: str
    name: str
    version: str
    description: str = ""
    author: str = ""
    min_version: str | None = None
    max_version: str | None = None
    dependencies: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    homepage: str | None = None
    repository: str | None = None
    license: str | None = None
    icon: str | None = None

    def __post_init__(self) -> None:
        """验证元数据"""
        if not self.id or not isinstance(self.id, str):
            raise ValueError("Plugin ID must be a non-empty string")
        if not self.name or not isinstance(self.name, str):
            raise ValueError("Plugin name must be a non-empty string")
        if not self.version or not isinstance(self.version, str):
            raise ValueError("Plugin version must be a non-empty string")

    def to_dict(self) -> dict[str, Any]:
        """转换为字典格式"""
        return {
            "id": self.id,
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "author": self.author,
            "min_version": self.min_version,
            "max_version": self.max_version,
            "dependencies": self.dependencies,
            "tags": self.tags,
            "homepage": self.homepage,
            "repository": self.repository,
            "license": self.license,
            "icon": self.icon,
        }


@dataclass
class PluginCommand:
    """
    插件命令定义

    用于注册插件提供的命令到系统命令注册表。

    Attributes:
        id: 命令唯一标识符
        name: 命令显示名称
        description: 命令描述
        callback: 命令执行回调函数
        shortcut: 快捷键绑定（可选）
        icon: 命令图标（可选）
    """

    id: str
    name: str
    description: str
    callback: Callable[[dict[str, Any]], Coroutine[Any, Any, Any]]
    shortcut: str | None = None
    icon: str | None = None


@dataclass
class PluginSetting:
    """
    插件配置项定义

    用于注册插件的配置选项到系统设置面板。

    Attributes:
        key: 配置键
        label: 显示标签
        type: 配置类型（text, number, boolean, select, etc.）
        default: 默认值
        description: 配置说明
        options: 选项列表（用于 select 类型）
        min: 最小值（用于 number 类型）
        max: 最大值（用于 number 类型）
    """

    key: str
    label: str
    type: str = "text"
    default: Any = None
    description: str = ""
    options: list[Any] | None = None
    min: int | float | None = None
    max: int | float | None = None


class Plugin(ABC):
    """
    插件抽象基类

    所有插件必须继承此类并实现相应的生命周期方法。
    提供插件生命周期管理、扩展点注册和资源清理功能。

    生命周期流程:
        1. on_load(): 插件加载时调用，初始化资源
        2. on_enable(): 插件启用时调用，激活功能
        3. on_disable(): 插件禁用时调用，清理资源
        4. on_unload(): 插件卸载时调用，彻底清理

    使用示例:
        ```python
        class MyPlugin(Plugin):
            manifest = PluginManifest(
                id="my-plugin",
                name="My Plugin",
                version="1.0.0",
                description="Example plugin"
            )

            async def on_load(self) -> None:
                # 注册命令
                self.add_command(PluginCommand(
                    id="greet",
                    name="Greet",
                    description="Say hello",
                    callback=self.greet
                ))

                # 注册设置
                self.add_setting(PluginSetting(
                    key="greeting_message",
                    label="Greeting Message",
                    type="text",
                    default="Hello"
                ))

                # 订阅事件
                self.add_event_handler("workflow.started", self.on_workflow_started)

            async def greet(self, args: dict) -> dict:
                return {"message": "Hello!"}

            async def on_workflow_started(self, event: Event) -> None:
                print(f"Workflow {event.payload['id']} started!")
        ```
    """

    # 子类必须定义 manifest
    manifest: PluginManifest | None = None

    def __init__(self) -> None:
        """初始化插件实例"""
        self._state: PluginState = PluginState.UNLOADED
        self._commands: dict[str, PluginCommand] = {}
        self._settings: dict[str, PluginSetting] = {}
        self._event_handlers: dict[str, Callable] = {}
        self._loaded_at: datetime | None = None
        self._logger = logger.bind(plugin=self.__class__.__name__)

    @property
    def state(self) -> PluginState:
        """获取插件当前状态"""
        return self._state

    @property
    def manifest(self) -> PluginManifest | None:
        """获取插件元数据"""
        # 允许子类覆盖
        return getattr(self.__class__, "manifest", None)

    @property
    def id(self) -> str:
        """获取插件 ID"""
        if self.manifest is None:
            raise ValueError("Plugin manifest is not defined")
        return self.manifest.id

    @property
    def name(self) -> str:
        """获取插件名称"""
        if self.manifest is None:
            raise ValueError("Plugin manifest is not defined")
        return self.manifest.name

    @property
    def version(self) -> str:
        """获取插件版本"""
        if self.manifest is None:
            raise ValueError("Plugin manifest is not defined")
        return self.manifest.version

    @property
    def logger(self):
        """获取插件日志器"""
        return self._logger

    def _set_state(self, state: PluginState) -> None:
        """设置插件状态"""
        old_state = self._state
        self._state = state
        self._logger.debug(f"State changed: {old_state.value} -> {state.value}")

    # ========== 生命周期方法 ==========

    async def on_load(self) -> None:
        """
        插件加载时调用

        在此方法中初始化插件资源、注册命令和设置、订阅事件等。
        此方法在插件系统启动时调用，插件此时还未激活。

        注意:
            - 此方法应该快速返回，避免阻塞
            - 不应在此方法中执行长时间运行的任务
            - 如果抛出异常，插件将进入 ERROR 状态
        """
        pass

    async def on_enable(self) -> None:
        """
        插件启用时调用

        在此方法中激活插件功能，如启动后台任务、连接外部服务等。
        插件从 DISABLED 或 LOADED 状态转换到 ENABLED 状态时调用。

        注意:
            - 可以在此方法中启动异步任务
            - 应该确保资源可以被 on_disable 清理
        """
        pass

    async def on_disable(self) -> None:
        """
        插件禁用时调用

        在此方法中暂停插件功能、停止后台任务、断开连接等。
        插件从 ENABLED 状态转换到 DISABLED 状态时调用。

        注意:
            - 必须确保清理所有在 on_enable 中分配的资源
            - 不应在此方法中抛出异常
        """
        pass

    async def on_unload(self) -> None:
        """
        插件卸载时调用

        在此方法中彻底清理插件资源，释放内存。
        插件从 LOADED 或 DISABLED 状态转换到 UNLOADED 状态时调用。

        注意:
            - 必须清理所有注册的资源
            - 必须取消所有待处理的任务
            - 此后插件实例不应再被使用
        """
        pass

    # ========== 扩展点注册方法 ==========

    def add_command(self, command: PluginCommand) -> None:
        """
        注册插件命令

        Args:
            command: 命令定义对象

        Raises:
            ValueError: 命令 ID 已存在

        Example:
            ```python
            self.add_command(PluginCommand(
                id="export-data",
                name="Export Data",
                description="Export workflow data",
                callback=self.export_data,
                shortcut="Ctrl+E"
            ))
            ```
        """
        if command.id in self._commands:
            raise ValueError(f"Command '{command.id}' already registered")
        self._commands[command.id] = command
        self._logger.debug(f"Command registered: {command.id}")

    def add_setting(self, setting: PluginSetting) -> None:
        """
        注册插件配置项

        Args:
            setting: 配置项定义对象

        Raises:
            ValueError: 配置键已存在

        Example:
            ```python
            self.add_setting(PluginSetting(
                key="max_retries",
                label="Max Retries",
                type="number",
                default=3,
                min=0,
                max=10,
                description="Maximum number of retry attempts"
            ))
            ```
        """
        if setting.key in self._settings:
            raise ValueError(f"Setting '{setting.key}' already registered")
        self._settings[setting.key] = setting
        self._logger.debug(f"Setting registered: {setting.key}")

    def add_event_handler(
        self,
        event_type: str,
        handler: Callable[[Any], Coroutine[Any, Any, None]],
    ) -> None:
        """
        注册事件处理器

        Args:
            event_type: 事件类型
            handler: 异步事件处理函数

        Raises:
            ValueError: 同一事件类型已注册处理器

        Example:
            ```python
            async def on_workflow_completed(event: Event) -> None:
                print(f"Workflow completed: {event.payload['id']}")

            self.add_event_handler("workflow.completed", on_workflow_completed)
            ```
        """
        if event_type in self._event_handlers:
            raise ValueError(f"Handler for '{event_type}' already registered")
        self._event_handlers[event_type] = handler
        self._logger.debug(f"Event handler registered: {event_type}")

    def remove_event_handler(self, event_type: str) -> bool:
        """
        移除事件处理器

        Args:
            event_type: 事件类型

        Returns:
            bool: 是否成功移除
        """
        if event_type in self._event_handlers:
            del self._event_handlers[event_type]
            self._logger.debug(f"Event handler removed: {event_type}")
            return True
        return False

    def remove_command(self, command_id: str) -> bool:
        """
        移除已注册的命令

        Args:
            command_id: 命令 ID

        Returns:
            bool: 是否成功移除
        """
        if command_id in self._commands:
            del self._commands[command_id]
            self._logger.debug(f"Command removed: {command_id}")
            return True
        return False

    def remove_setting(self, key: str) -> bool:
        """
        移除已注册的配置项

        Args:
            key: 配置键

        Returns:
            bool: 是否成功移除
        """
        if key in self._settings:
            del self._settings[key]
            self._logger.debug(f"Setting removed: {key}")
            return True
        return False

    def get_command(self, command_id: str) -> PluginCommand | None:
        """
        获取已注册的命令

        Args:
            command_id: 命令 ID

        Returns:
            PluginCommand | None: 命令对象，不存在返回 None
        """
        return self._commands.get(command_id)

    def get_setting(self, key: str) -> PluginSetting | None:
        """
        获取已注册的配置项

        Args:
            key: 配置键

        Returns:
            PluginSetting | None: 配置项对象，不存在返回 None
        """
        return self._settings.get(key)

    @property
    def commands(self) -> dict[str, PluginCommand]:
        """获取所有注册的命令"""
        return self._commands.copy()

    @property
    def settings(self) -> dict[str, PluginSetting]:
        """获取所有注册的配置项"""
        return self._settings.copy()

    @property
    def event_handlers(self) -> dict[str, Callable]:
        """获取所有注册的事件处理器"""
        return self._event_handlers.copy()

    # ========== 工具方法 ==========

    async def _cleanup(self) -> None:
        """
        清理所有注册的资源

        内部方法，在插件卸载时自动调用。
        """
        # 移除所有事件处理器
        for event_type in list(self._event_handlers.keys()):
            self.remove_event_handler(event_type)

        # 清空命令和设置
        self._commands.clear()
        self._settings.clear()

        self._logger.debug("All resources cleaned up")
