"""依赖注入容器 - 实现模块解耦

使用依赖注入模式，所有服务通过容器管理，避免硬编码依赖
"""

from typing import Any, Callable, TypeVar, get_type_hints
from functools import wraps
import inspect

T = TypeVar("T")


class DependencyContainer:
    """
    依赖注入容器

    支持单例、瞬态、作用域三种生命周期

    使用示例:
    ```python
    container = DependencyContainer()

    # 注册服务
    container.register_singleton(DatabaseService, DatabaseService())
    container.register_transient(Logger, lambda: Logger("app"))

    # 解析服务
    db = container.resolve(DatabaseService)
    ```
    """

    def __init__(self):
        self._singletons: dict[type, Any] = {}
        self._transient_factories: dict[type, Callable[[], Any]] = {}
        self._scoped_instances: dict[type, Any] = {}
        self._interface_mappings: dict[type, type] = {}

    def register_singleton(self, interface: type[T], instance: T) -> "DependencyContainer":
        """
        注册单例服务

        Args:
            interface: 服务接口类型
            instance: 单例实例
        """
        self._singletons[interface] = instance
        return self

    def register_transient(self, interface: type[T], factory: Callable[[], T]) -> "DependencyContainer":
        """
        注册瞬态服务（每次解析创建新实例）

        Args:
            interface: 服务接口类型
            factory: 实例工厂函数
        """
        self._transient_factories[interface] = factory
        return self

    def register_scoped(self, interface: type[T], factory: Callable[[], T]) -> "DependencyContainer":
        """
        注册作用域服务（同作用域共享实例）

        Args:
            interface: 服务接口类型
            factory: 实例工厂函数
        """
        # 作用域服务在 begin_scope 时初始化
        self._transient_factories[interface] = factory
        return self

    def map_interface(self, interface: type, implementation: type) -> "DependencyContainer":
        """
        映射接口到实现类

        Args:
            interface: 接口类型
            implementation: 实现类类型
        """
        self._interface_mappings[interface] = implementation
        return self

    def resolve(self, interface: type[T]) -> T:
        """
        解析服务

        Args:
            interface: 服务接口类型

        Returns:
            服务实例

        Raises:
            KeyError: 未找到注册的服务
        """
        # 1. 检查单例
        if interface in self._singletons:
            return self._singletons[interface]

        # 2. 检查作用域实例
        if interface in self._scoped_instances:
            return self._scoped_instances[interface]

        # 3. 检查瞬态工厂
        if interface in self._transient_factories:
            instance = self._transient_factories[interface]()
            # 如果这是一个作用域服务，缓存实例
            if interface in self._scoped_instances:
                self._scoped_instances[interface] = instance
            return instance

        # 4. 检查接口映射
        if interface in self._interface_mappings:
            impl_class = self._interface_mappings[interface]
            # 尝试自动实例化（假设有无参构造函数）
            instance = impl_class()
            return instance

        raise KeyError(f"未找到类型 {interface.__name__} 的注册服务")

    def begin_scope(self) -> "Scope":
        """
        开始新的作用域

        在作用域内，作用域服务将共享同一实例
        """
        return Scope(self)

    def create_child(self) -> "DependencyContainer":
        """
        创建子容器

        子容器继承父容器的注册，但可以有独立的覆盖
        """
        child = DependencyContainer()
        child._singletons = self._singletons.copy()
        child._interface_mappings = self._interface_mappings.copy()
        # 注意：不复制工厂，子容器需要重新注册
        return child


class Scope:
    """作用域上下文管理器"""

    def __init__(self, container: DependencyContainer):
        self.container = container
        self._previous_scoped = {}

    async def __aenter__(self):
        """进入作用域"""
        # 保存当前作用域实例
        self._previous_scoped = self.container._scoped_instances.copy()
        # 清空作用域实例，让每个作用域有独立实例
        self.container._scoped_instances = {}
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """退出作用域"""
        # 恢复之前的作用域实例
        self.container._scoped_instances = self._previous_scoped

    def resolve(self, interface: type[T]) -> T:
        """在当前作用域解析服务"""
        return self.container.resolve(interface)


# 全局容器实例（应用级单例）
container = DependencyContainer()


def inject(*dependencies: type):
    """
    依赖注入装饰器

    自动从容器解析依赖并注入函数参数

    使用示例:
    ```python
    @inject(DatabaseService, Logger)
    async def process_data(db: DatabaseService, logger: Logger, data: dict):
        # db 和 logger 会自动从容器注入
        await db.save(data)
        logger.info("Data saved")
    ```
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # 从容器解析依赖
            resolved_deps = [container.resolve(dep) for dep in dependencies]
            # 将解析的依赖添加到参数前面
            all_args = resolved_deps + list(args)
            return await func(*all_args, **kwargs)

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            resolved_deps = [container.resolve(dep) for dep in dependencies]
            all_args = resolved_deps + list(args)
            return func(*all_args, **kwargs)

        # 根据被装饰函数是否是异步选择包装器
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    return decorator


def register_service(
    interface: type = None,
    scope: str = "singleton"
):
    """
    服务注册装饰器

    自动将类注册到依赖注入容器

    使用示例:
    ```python
    @register_service(interface=DatabaseInterface, scope="singleton")
    class DatabaseService:
        def __init__(self):
            self.connection = create_connection()
    ```
    """
    def decorator(cls: type) -> type:
        # 确定要注册的接口
        reg_interface = interface or cls

        if scope == "singleton":
            # 单例模式 - 立即实例化
            instance = cls()
            container.register_singleton(reg_interface, instance)
        elif scope == "transient":
            # 瞬态模式 - 每次创建新实例
            container.register_transient(reg_interface, lambda: cls())
        elif scope == "scoped":
            # 作用域模式
            container.register_scoped(reg_interface, lambda: cls())
        else:
            raise ValueError(f"Unknown scope: {scope}")

        return cls
    return decorator
