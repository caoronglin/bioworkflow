"""
依赖注入容器 - 使用依赖注入模式管理所有服务

实现控制反转(IoC)，解耦服务之间的依赖关系
"""

from typing import Any, Type, TypeVar

from backend.core.interfaces import (
    CacheService,
    EventPublisher,
    JupyterKernelService,
    MetricsCollector,
    PackageManager,
    Repository,
    SearchService,
    UnitOfWork,
    WorkflowEngine,
)

T = TypeVar("T")


class ServiceContainer:
    """
    服务容器

    管理所有服务的注册和解析，实现依赖注入
    """

    def __init__(self):
        self._registrations: dict[Type, Any] = {}
        self._singletons: dict[Type, Any] = {}
        self._factories: dict[Type, callable] = {}

    def register_instance(self, interface: Type[T], instance: T) -> "ServiceContainer":
        """注册单例实例"""
        self._singletons[interface] = instance
        return self

    def register_factory(
        self,
        interface: Type[T],
        factory: callable,
    ) -> "ServiceContainer":
        """注册工厂函数"""
        self._factories[interface] = factory
        return self

    def register_type(
        self,
        interface: Type[T],
        implementation: Type[T],
        singleton: bool = False,
    ) -> "ServiceContainer":
        """注册类型映射"""
        self._registrations[interface] = {
            "implementation": implementation,
            "singleton": singleton,
        }
        return self

    def resolve(self, interface: Type[T]) -> T:
        """解析服务"""
        # 1. 检查单例实例
        if interface in self._singletons:
            return self._singletons[interface]

        # 2. 检查工厂函数
        if interface in self._factories:
            instance = self._factories[interface](self)
            self._singletons[interface] = instance
            return instance

        # 3. 检查类型注册
        if interface in self._registrations:
            reg = self._registrations[interface]
            impl_class = reg["implementation"]

            if reg["singleton"]:
                if interface not in self._singletons:
                    self._singletons[interface] = impl_class()
                return self._singletons[interface]
            else:
                return impl_class()

        raise KeyError(f"Service not registered: {interface}")

    def try_resolve(self, interface: Type[T]) -> T | None:
        """尝试解析服务，不存在返回 None"""
        try:
            return self.resolve(interface)
        except KeyError:
            return None


# 全局容器实例
_container: ServiceContainer | None = None


def get_container() -> ServiceContainer:
    """获取全局服务容器"""
    global _container
    if _container is None:
        _container = _create_default_container()
    return _container


def reset_container() -> None:
    """重置容器（用于测试）"""
    global _container
    _container = None


def _create_default_container() -> ServiceContainer:
    """创建默认配置的容器"""
    from backend.infrastructure.cache.redis_cache import RedisCacheService
    from backend.infrastructure.database.unit_of_work import SQLAlchemyUnitOfWork
    from backend.infrastructure.events.event_bus import EventBusPublisher
    from backend.infrastructure.metrics.prometheus import PrometheusMetrics
    from backend.infrastructure.search.elasticsearch import ElasticsearchService
    from backend.services.conda.manager import CondaPackageManager
    from backend.services.jupyter import JupyterKernelManager
    from backend.services.snakemake.workflow_engine import SnakemakeWorkflowEngine

    container = ServiceContainer()

    # 注册核心服务
    container.register_type(UnitOfWork, SQLAlchemyUnitOfWork)
    container.register_type(EventPublisher, EventBusPublisher, singleton=True)
    container.register_type(CacheService, RedisCacheService, singleton=True)
    container.register_type(WorkflowEngine, SnakemakeWorkflowEngine, singleton=True)
    container.register_type(PackageManager, CondaPackageManager, singleton=True)
    container.register_type(SearchService, ElasticsearchService, singleton=True)
    container.register_type(MetricsCollector, PrometheusMetrics, singleton=True)
    container.register_type(JupyterKernelService, JupyterKernelManager, singleton=True)

    return container


# 便捷函数
def get_unit_of_work() -> UnitOfWork:
    """获取工作单元"""
    return get_container().resolve(UnitOfWork)


def get_event_publisher() -> EventPublisher:
    """获取事件发布器"""
    return get_container().resolve(EventPublisher)


def get_cache_service() -> CacheService:
    """获取缓存服务"""
    return get_container().resolve(CacheService)


def get_workflow_engine() -> WorkflowEngine:
    """获取工作流引擎"""
    return get_container().resolve(WorkflowEngine)


def get_package_manager() -> PackageManager:
    """获取包管理器"""
    return get_container().resolve(PackageManager)


def get_search_service() -> SearchService:
    """获取搜索服务"""
    return get_container().resolve(SearchService)


def get_metrics_collector() -> MetricsCollector:
    """获取指标收集器"""
    return get_container().resolve(MetricsCollector)


def get_jupyter_kernel_service() -> JupyterKernelService:
    """获取 Jupyter 内核服务"""
    return get_container().resolve(JupyterKernelService)
