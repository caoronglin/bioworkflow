"""
插件系统异常定义

提供插件加载、管理和执行过程中的专用异常类，
支持精确的错误处理和友好的错误消息。
"""


class PluginError(Exception):
    """
    插件系统基础异常类

    所有插件相关异常的基类，提供统一的异常层次结构。

    Attributes:
        message: 错误消息
        plugin_name: 相关插件名称（如果有）
    """

    def __init__(self, message: str, plugin_name: str | None = None) -> None:
        self.message = message
        self.plugin_name = plugin_name
        super().__init__(self._format_message())

    def _format_message(self) -> str:
        """格式化错误消息"""
        if self.plugin_name:
            return f"[Plugin: {self.plugin_name}] {self.message}"
        return self.message


class PluginLoadError(PluginError):
    """
    插件加载失败异常

    当插件无法加载时抛出，可能原因包括：
    - 插件文件不存在
    - 插件模块导入失败
    - 插件类定义错误
    - 必需的依赖缺失

    Example:
        ```python
        try:
            await registry.load_plugin("my-plugin")
        except PluginLoadError as e:
            logger.error(f"Failed to load plugin: {e}")
        ```
    """

    pass


class PluginDependencyError(PluginError):
    """
    插件依赖解析失败异常

    当插件依赖无法满足时抛出，包括：
    - 依赖的插件未安装
    - 依赖的插件版本不兼容
    - 循环依赖检测

    Attributes:
        message: 错误消息
        plugin_name: 请求插件名称
        missing_dependency: 缺失的依赖名称
    """

    def __init__(
        self,
        message: str,
        plugin_name: str | None = None,
        missing_dependency: str | None = None,
    ) -> None:
        super().__init__(message, plugin_name)
        self.missing_dependency = missing_dependency


class PluginNotFoundError(PluginError):
    """
    插件未找到异常

    当请求的插件不存在于注册表中时抛出。

    Example:
        ```python
        plugin = registry.get_plugin("non-existent")
        # Raises PluginNotFoundError
        ```
    """

    pass


class PluginAlreadyLoadedError(PluginError):
    """
    插件已加载异常

    当尝试重复加载已加载的插件时抛出。
    """

    pass


class PluginNotLoadedError(PluginError):
    """
    插件未加载异常

    当尝试操作未加载的插件时抛出（如禁用、卸载）。
    """

    pass


class PluginValidationError(PluginError):
    """
    插件验证失败异常

    当插件元数据或配置未通过验证时抛出，包括：
    - 必需的元数据字段缺失
    - 元数据格式错误
    - 插件配置无效
    """

    pass


class PluginExecutionError(PluginError):
    """
    插件执行失败异常

    当插件方法执行过程中发生错误时抛出。
    """

    pass


class PluginHookError(PluginError):
    """
    插件钩子执行失败异常

    当钩子函数执行失败或钩子点未注册时抛出。
    """

    pass
