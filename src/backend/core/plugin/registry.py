"""
插件注册表 - 管理插件的生命周期

提供插件发现、加载、卸载、依赖解析等功能。
采用单例模式，确保全局唯一的插件管理器。

使用示例:
    ```python
    from backend.core.plugin.registry import PluginRegistry

    # 获取单例实例
    registry = PluginRegistry.get_instance()

    # 发现并加载所有插件
    await registry.discover_plugins()
    await registry.load_all()

    # 加载特定插件
    await registry.load_plugin("my-plugin")

    # 禁用插件
    await registry.disable_plugin("my-plugin")

    # 卸载插件
    await registry.unload_plugin("my-plugin")

    # 获取插件信息
    plugin = registry.get_plugin("my-plugin")
    info = registry.get_plugin_info("my-plugin")
    ```
"""

import asyncio
import importlib.util
import sys
from pathlib import Path
from typing import Any

from loguru import logger

from backend.core.plugin.base import Plugin, PluginManifest, PluginState
from backend.core.plugin.exceptions import (
    PluginAlreadyLoadedError,
    PluginDependencyError,
    PluginLoadError,
    PluginNotFoundError,
    PluginNotLoadedError,
    PluginValidationError,
)


class PluginInfo:
    """
    插件信息包装器

    包含插件实例及其加载元数据。

    Attributes:
        plugin: 插件实例
        path: 插件文件路径
        load_time: 加载时间（毫秒）
        error: 错误消息（如果有）
    """

    def __init__(
        self,
        plugin: Plugin,
        path: Path | None = None,
        load_time: float = 0.0,
        error: str | None = None,
    ) -> None:
        self.plugin = plugin
        self.path = path
        self.load_time = load_time
        self.error = error
        self.loaded_at: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """转换为字典格式"""
        return {
            "id": self.plugin.id,
            "name": self.plugin.name,
            "version": self.plugin.version,
            "description": self.plugin.manifest.description if self.plugin.manifest else "",
            "author": self.plugin.manifest.author if self.plugin.manifest else "",
            "state": self.plugin.state.value,
            "path": str(self.path) if self.path else None,
            "load_time": self.load_time,
            "error": self.error,
            "dependencies": (self.plugin.manifest.dependencies if self.plugin.manifest else []),
        }


class PluginRegistry:
    """
    插件注册表 - 单例类

    管理所有插件的生命周期，包括：
    - 插件发现：扫描插件目录
    - 插件加载：导入并初始化插件
    - 依赖解析：确保依赖顺序
    - 状态管理：跟踪插件状态

    线程安全：使用 asyncio 锁保护并发访问

    Example:
        ```python
        # 获取单例
        registry = PluginRegistry.get_instance()

        # 配置插件目录
        registry.set_plugin_path(Path("./plugins"))

        # 发现插件
        discovered = await registry.discover_plugins()
        print(f"Discovered {len(discovered)} plugins")

        # 加载所有插件
        loaded = await registry.load_all()
        print(f"Loaded {len(loaded)} plugins")

        # 启用插件
        await registry.enable_plugin("my-plugin")
        ```
    """

    _instance: "PluginRegistry | None" = None
    _lock: asyncio.Lock | None = None

    def __new__(cls) -> "PluginRegistry":
        """单例模式实现"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        """初始化插件注册表"""
        if self._initialized:
            return

        self._plugins: dict[str, PluginInfo] = {}
        self._plugin_path: Path | None = None
        self._logger = logger.bind(module="plugin_registry")
        self._initialized = True

    @classmethod
    async def get_instance(cls) -> "PluginRegistry":
        """
        获取插件注册表单例（异步安全版本）

        Returns:
            PluginRegistry: 单例实例
        """
        if cls._instance is None:
            # 创建实例
            cls._instance = cls()

        # 确保锁已初始化
        if cls._lock is None:
            cls._lock = asyncio.Lock()

        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """重置单例（用于测试）"""
        cls._instance = None
        cls._lock = None

    async def _acquire_lock(self) -> None:
        """获取异步锁"""
        if self._lock is None:
            self._lock = asyncio.Lock()
        await self._lock.acquire()

    def _release_lock(self) -> None:
        """释放异步锁"""
        if self._lock and self._lock.locked():
            self._lock.release()

    def set_plugin_path(self, path: Path | str) -> None:
        """
        设置插件目录路径

        Args:
            path: 插件目录路径

        Example:
            ```python
            registry.set_plugin_path("./plugins")
            registry.set_plugin_path(Path("/absolute/path/to/plugins"))
            ```
        """
        if isinstance(path, str):
            path = Path(path)

        if not path.exists():
            self._logger.warning(f"Plugin path does not exist: {path}")
            path.mkdir(parents=True, exist_ok=True)
            self._logger.info(f"Created plugin directory: {path}")

        self._plugin_path = path.absolute()
        self._logger.info(f"Plugin path set to: {self._plugin_path}")

    @property
    def plugin_path(self) -> Path | None:
        """获取插件目录路径"""
        return self._plugin_path

    async def discover_plugins(self) -> list[Path]:
        """
        扫描插件目录，发现所有可用插件

        扫描规则:
            - 查找 plugins 目录下的所有子目录
            - 每个子目录应该包含 __init__.py 和 main.py
            - main.py 应该导出 Plugin 子类

        Returns:
            list[Path]: 发现的插件路径列表

        Raises:
            ValueError: 未设置插件路径
        """
        if self._plugin_path is None:
            raise ValueError("Plugin path not set. Call set_plugin_path() first.")

        discovered = []
        self._logger.info(f"Scanning for plugins in {self._plugin_path}")

        # 扫描所有子目录
        for item in self._plugin_path.iterdir():
            if not item.is_dir():
                continue

            # 跳过隐藏目录和 __pycache__
            if item.name.startswith("_") or item.name == "__pycache__":
                continue

            # 检查是否有 main.py
            main_file = item / "main.py"
            if not main_file.exists():
                self._logger.debug(f"Skipping {item.name}: no main.py found")
                continue

            discovered.append(item)
            self._logger.debug(f"Found potential plugin: {item.name}")

        self._logger.info(f"Discovered {len(discovered)} plugin(s)")
        return discovered

    async def _load_plugin_module(self, plugin_path: Path) -> Any:
        """
        动态加载插件模块

        Args:
            plugin_path: 插件目录路径

        Returns:
            Any: 加载的模块对象

        Raises:
            PluginLoadError: 加载失败
        """
        main_file = plugin_path / "main.py"

        try:
            # 创建模块规范
            spec = importlib.util.spec_from_file_location(f"plugin_{plugin_path.name}", main_file)

            if spec is None or spec.loader is None:
                raise PluginLoadError(
                    f"Failed to create module spec for {plugin_path.name}",
                    plugin_name=plugin_path.name,
                )

            # 创建并加载模块
            module = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = module
            spec.loader.exec_module(module)

            self._logger.debug(f"Module loaded: {plugin_path.name}")
            return module

        except Exception as e:
            raise PluginLoadError(
                f"Failed to load module: {e}", plugin_name=plugin_path.name
            ) from e

    async def _validate_plugin(self, plugin: Plugin) -> None:
        """
        验证插件元数据

        Args:
            plugin: 插件实例

        Raises:
            PluginValidationError: 验证失败
        """
        if plugin.manifest is None:
            raise PluginValidationError("Plugin manifest is not defined", plugin_name=plugin.id)

        # 验证必需字段
        if not plugin.manifest.id:
            raise PluginValidationError("Plugin ID is required", plugin_name=plugin.id)

        if not plugin.manifest.name:
            raise PluginValidationError("Plugin name is required", plugin_name=plugin.id)

        if not plugin.manifest.version:
            raise PluginValidationError("Plugin version is required", plugin_name=plugin.id)

        # 验证 ID 格式
        if not plugin.manifest.id.replace("-", "").replace("_", "").isalnum():
            raise PluginValidationError(
                "Plugin ID must be alphanumeric (hyphens and underscores allowed)",
                plugin_name=plugin.id,
            )

        self._logger.debug(f"Plugin validated: {plugin.id}")

    async def _check_dependencies(self, plugin: Plugin) -> None:
        """
        检查插件依赖

        Args:
            plugin: 插件实例

        Raises:
            PluginDependencyError: 依赖不满足
        """
        if plugin.manifest is None:
            return

        for dep_id in plugin.manifest.dependencies:
            if dep_id not in self._plugins:
                raise PluginDependencyError(
                    f"Missing dependency: {dep_id}",
                    plugin_name=plugin.id,
                    missing_dependency=dep_id,
                )

            dep_info = self._plugins[dep_id]
            if dep_info.plugin.state not in (
                PluginState.LOADED,
                PluginState.ENABLED,
            ):
                raise PluginDependencyError(
                    f"Dependency '{dep_id}' is not loaded",
                    plugin_name=plugin.id,
                    missing_dependency=dep_id,
                )

        self._logger.debug(f"Dependencies checked: {plugin.id}")

    def _detect_circular_dependency(
        self, plugin_id: str, visited: set[str], path: list[str]
    ) -> None:
        """
        检测循环依赖

        Args:
            plugin_id: 插件 ID
            visited: 已访问的插件集合
            path: 当前依赖路径

        Raises:
            PluginDependencyError: 检测到循环依赖
        """
        if plugin_id in path:
            cycle = " -> ".join(path[path.index(plugin_id) :] + [plugin_id])
            raise PluginDependencyError(
                f"Circular dependency detected: {cycle}",
                plugin_name=plugin_id,
            )

        if plugin_id in visited:
            return

        visited.add(plugin_id)
        path.append(plugin_id)

        if plugin_id in self._plugins:
            plugin = self._plugins[plugin_id].plugin
            if plugin.manifest:
                for dep_id in plugin.manifest.dependencies:
                    self._detect_circular_dependency(dep_id, visited, path.copy())

    async def load_plugin(self, plugin_id: str | Path) -> Plugin:
        """
        加载单个插件

        Args:
            plugin_id: 插件 ID 或插件路径

        Returns:
            Plugin: 加载的插件实例

        Raises:
            PluginNotFoundError: 插件未找到
            PluginAlreadyLoadedError: 插件已加载
            PluginLoadError: 加载失败
            PluginDependencyError: 依赖不满足
        """
        async with self._lock or asyncio.Lock():
            # 如果传入的是路径，需要先获取插件 ID
            if isinstance(plugin_id, Path):
                plugin_path = plugin_id
                # 先临时加载模块获取 ID
                module = await self._load_plugin_module(plugin_path)
                # 查找 Plugin 子类
                plugin_class = None
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if isinstance(attr, type) and issubclass(attr, Plugin) and attr is not Plugin:
                        plugin_class = attr
                        break

                if plugin_class is None:
                    raise PluginLoadError(
                        "No Plugin subclass found in module",
                        plugin_name=plugin_path.name,
                    )

                # 创建临时实例获取 ID
                temp_plugin = plugin_class()
                if temp_plugin.manifest is None:
                    raise PluginLoadError(
                        "Plugin manifest is not defined",
                        plugin_name=plugin_path.name,
                    )
                plugin_id = temp_plugin.manifest.id
            else:
                # 从已发现的插件中查找路径
                plugin_path = None
                for pid, info in self._plugins.items():
                    if pid == plugin_id:
                        plugin_path = info.path
                        break

            # 检查是否已加载
            if plugin_id in self._plugins:
                if self._plugins[plugin_id].plugin.state != PluginState.UNLOADED:
                    raise PluginAlreadyLoadedError(
                        f"Plugin '{plugin_id}' is already loaded",
                        plugin_name=plugin_id,
                    )

            if plugin_path is None:
                raise PluginNotFoundError(f"Plugin '{plugin_id}' not found")

            self._logger.info(f"Loading plugin: {plugin_id}")
            start_time = asyncio.get_event_loop().time()

            try:
                # 加载模块
                module = await self._load_plugin_module(plugin_path)

                # 查找 Plugin 子类
                plugin_class: type[Plugin] | None = None
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if isinstance(attr, type) and issubclass(attr, Plugin) and attr is not Plugin:
                        plugin_class = attr
                        break

                if plugin_class is None:
                    raise PluginLoadError(
                        "No Plugin subclass found in module",
                        plugin_name=plugin_id,
                    )

                # 创建插件实例
                plugin = plugin_class()

                # 验证插件
                await self._validate_plugin(plugin)

                # 检查依赖
                await self._check_dependencies(plugin)

                # 调用生命周期方法
                await plugin.on_load()
                plugin._set_state(PluginState.LOADED)

                # 记录加载时间
                load_time = asyncio.get_event_loop().time() - start_time

                # 注册插件
                plugin_info = PluginInfo(
                    plugin=plugin,
                    path=plugin_path,
                    load_time=load_time * 1000,  # 转换为毫秒
                )
                plugin_info.loaded_at = asyncio.get_event_loop().time()
                self._plugins[plugin_id] = plugin_info

                self._logger.info(f"Plugin loaded: {plugin_id} ({load_time * 1000:.2f}ms)")
                return plugin

            except Exception as e:
                self._logger.error(f"Failed to load plugin {plugin_id}: {e}")
                if isinstance(e, PluginLoadError):
                    raise
                raise PluginLoadError(str(e), plugin_name=plugin_id) from e

    async def load_all(self) -> list[Plugin]:
        """
        加载所有已发现的插件

        自动处理依赖顺序，确保依赖的插件先加载。

        Returns:
            list[Plugin]: 成功加载的插件列表
        """
        async with self._lock or asyncio.Lock():
            if self._plugin_path is None:
                raise ValueError("Plugin path not set")

            loaded = []
            failed = []

            # 发现所有插件
            plugin_paths = await self.discover_plugins()

            if not plugin_paths:
                self._logger.info("No plugins found")
                return loaded

            # 构建依赖图并排序
            plugin_map: dict[str, Path] = {}
            for path in plugin_paths:
                # 临时加载获取 ID
                try:
                    module = await self._load_plugin_module(path)
                    for attr_name in dir(module):
                        attr = getattr(module, attr_name)
                        if (
                            isinstance(attr, type)
                            and issubclass(attr, Plugin)
                            and attr is not Plugin
                        ):
                            temp_plugin = attr()
                            if temp_plugin.manifest:
                                plugin_map[temp_plugin.manifest.id] = path
                            break
                except Exception as e:
                    self._logger.warning(f"Failed to load plugin {path.name}: {e}")
                    failed.append(path)

            # 拓扑排序处理依赖
            sorted_ids = self._topological_sort(plugin_map.keys())

            # 按顺序加载
            for plugin_id in sorted_ids:
                try:
                    plugin = await self.load_plugin(plugin_id)
                    loaded.append(plugin)
                except Exception as e:
                    self._logger.error(f"Failed to load {plugin_id}: {e}")
                    failed.append(plugin_map.get(plugin_id))

            self._logger.info(f"Loaded {len(loaded)} plugins, {len(failed)} failed")
            return loaded

    def _topological_sort(self, plugin_ids: list[str]) -> list[str]:
        """
        拓扑排序插件（处理依赖顺序）

        Args:
            plugin_ids: 插件 ID 列表

        Returns:
            list[str]: 排序后的插件 ID 列表
        """
        # 构建依赖图
        graph: dict[str, set[str]] = {pid: set() for pid in plugin_ids}
        in_degree: dict[str, int] = {pid: 0 for pid in plugin_ids}

        # 临时加载获取依赖信息
        for pid in plugin_ids:
            if pid in self._plugins and self._plugins[pid].plugin.manifest:
                deps = self._plugins[pid].plugin.manifest.dependencies
                for dep in deps:
                    if dep in plugin_ids:
                        graph[dep].add(pid)
                        in_degree[pid] += 1

        # Kahn 算法
        queue = [pid for pid in plugin_ids if in_degree[pid] == 0]
        result = []

        while queue:
            pid = queue.pop(0)
            result.append(pid)

            for dependent in graph[pid]:
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    queue.append(dependent)

        # 检测循环依赖
        if len(result) != len(plugin_ids):
            self._logger.error("Circular dependency detected in plugins")
            # 返回部分结果，未排序的插件会被跳过
            return result + [pid for pid in plugin_ids if pid not in result]

        return result

    def get_plugin(self, plugin_id: str) -> Plugin | None:
        """
        获取插件实例

        Args:
            plugin_id: 插件 ID

        Returns:
            Plugin | None: 插件实例，未找到返回 None
        """
        if plugin_id in self._plugins:
            return self._plugins[plugin_id].plugin
        return None

    def get_plugin_info(self, plugin_id: str) -> dict[str, Any] | None:
        """
        获取插件信息

        Args:
            plugin_id: 插件 ID

        Returns:
            dict | None: 插件信息字典，未找到返回 None
        """
        if plugin_id in self._plugins:
            return self._plugins[plugin_id].to_dict()
        return None

    def list_plugins(self, state: PluginState | None = None) -> list[dict[str, Any]]:
        """
        列出所有插件

        Args:
            state: 可选的状态过滤器

        Returns:
            list[dict]: 插件信息列表
        """
        plugins = []
        for info in self._plugins.values():
            if state is None or info.plugin.state == state:
                plugins.append(info.to_dict())
        return plugins

    async def enable_plugin(self, plugin_id: str) -> None:
        """
        启用插件

        Args:
            plugin_id: 插件 ID

        Raises:
            PluginNotFoundError: 插件未找到
            PluginNotLoadedError: 插件未加载
        """
        if plugin_id not in self._plugins:
            raise PluginNotFoundError(f"Plugin '{plugin_id}' not found")

        plugin_info = self._plugins[plugin_id]
        plugin = plugin_info.plugin

        if plugin.state == PluginState.UNLOADED:
            raise PluginNotLoadedError(f"Plugin '{plugin_id}' is not loaded", plugin_name=plugin_id)

        if plugin.state == PluginState.ENABLED:
            self._logger.debug(f"Plugin '{plugin_id}' is already enabled")
            return

        self._logger.info(f"Enabling plugin: {plugin_id}")
        await plugin.on_enable()
        plugin._set_state(PluginState.ENABLED)

    async def disable_plugin(self, plugin_id: str) -> None:
        """
        禁用插件

        Args:
            plugin_id: 插件 ID

        Raises:
            PluginNotFoundError: 插件未找到
        """
        if plugin_id not in self._plugins:
            raise PluginNotFoundError(f"Plugin '{plugin_id}' not found")

        plugin_info = self._plugins[plugin_id]
        plugin = plugin_info.plugin

        if plugin.state != PluginState.ENABLED:
            self._logger.debug(f"Plugin '{plugin_id}' is not enabled")
            return

        # 检查是否有其他插件依赖此插件
        for other_id, other_info in self._plugins.items():
            if other_id == plugin_id:
                continue
            if (
                other_info.plugin.manifest
                and plugin_id in other_info.plugin.manifest.dependencies
                and other_info.plugin.state == PluginState.ENABLED
            ):
                self._logger.warning(f"Plugin '{other_id}' depends on '{plugin_id}'")

        self._logger.info(f"Disabling plugin: {plugin_id}")
        await plugin.on_disable()
        plugin._set_state(PluginState.DISABLED)

    async def unload_plugin(self, plugin_id: str) -> None:
        """
        卸载插件

        Args:
            plugin_id: 插件 ID

        Raises:
            PluginNotFoundError: 插件未找到
        """
        if plugin_id not in self._plugins:
            raise PluginNotFoundError(f"Plugin '{plugin_id}' not found")

        plugin_info = self._plugins[plugin_id]
        plugin = plugin_info.plugin

        # 如果是启用状态，先禁用
        if plugin.state == PluginState.ENABLED:
            await self.disable_plugin(plugin_id)

        self._logger.info(f"Unloading plugin: {plugin_id}")
        await plugin.on_unload()
        await plugin._cleanup()
        plugin._set_state(PluginState.UNLOADED)

        # 从注册表移除
        del self._plugins[plugin_id]
        self._logger.info(f"Plugin unloaded: {plugin_id}")

    async def unload_all(self) -> None:
        """卸载所有插件（反向依赖顺序）"""
        # 反向卸载（依赖者先卸载）
        plugin_ids = list(self._plugins.keys())
        for plugin_id in reversed(plugin_ids):
            try:
                await self.unload_plugin(plugin_id)
            except Exception as e:
                self._logger.error(f"Failed to unload {plugin_id}: {e}")

    @property
    def loaded_count(self) -> int:
        """获取已加载的插件数量"""
        return len(self._plugins)

    @property
    def enabled_count(self) -> int:
        """获取已启用的插件数量"""
        return sum(1 for info in self._plugins.values() if info.plugin.state == PluginState.ENABLED)
