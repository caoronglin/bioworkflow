"""
核心接口定义 - 依赖反转原则

定义所有服务的抽象接口，实现松耦合架构
"""

from abc import ABC, abstractmethod
from typing import Any, AsyncIterator, Callable, Generic, TypeVar

T = TypeVar("T")


class Repository(ABC, Generic[T]):
    """通用仓储接口"""

    @abstractmethod
    async def get_by_id(self, id: str) -> T | None:
        """通过 ID 获取实体"""
        pass

    @abstractmethod
    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        filters: dict[str, Any] | None = None,
    ) -> list[T]:
        """获取所有实体"""
        pass

    @abstractmethod
    async def create(self, entity: T) -> T:
        """创建实体"""
        pass

    @abstractmethod
    async def update(self, entity: T) -> T:
        """更新实体"""
        pass

    @abstractmethod
    async def delete(self, id: str) -> bool:
        """删除实体"""
        pass

    @abstractmethod
    async def exists(self, id: str) -> bool:
        """检查实体是否存在"""
        pass


class UnitOfWork(ABC):
    """工作单元接口 - 管理事务"""

    @abstractmethod
    async def commit(self) -> None:
        """提交事务"""
        pass

    @abstractmethod
    async def rollback(self) -> None:
        """回滚事务"""
        pass

    @abstractmethod
    async def __aenter__(self) -> "UnitOfWork":
        """异步上下文管理器入口"""
        pass

    @abstractmethod
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """异步上下文管理器出口"""
        pass


class CacheService(ABC):
    """缓存服务接口"""

    @abstractmethod
    async def get(self, key: str) -> Any | None:
        """获取缓存值"""
        pass

    @abstractmethod
    async def set(
        self,
        key: str,
        value: Any,
        ttl: int | None = None,
    ) -> None:
        """设置缓存值"""
        pass

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """删除缓存"""
        pass

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """检查缓存是否存在"""
        pass

    @abstractmethod
    async def clear(self) -> None:
        """清空缓存"""
        pass


class EventPublisher(ABC):
    """事件发布接口"""

    @abstractmethod
    async def publish(self, event_type: str, payload: dict[str, Any]) -> None:
        """发布事件"""
        pass

    @abstractmethod
    def subscribe(
        self,
        event_type: str,
        handler: Callable[[dict[str, Any]], Any],
    ) -> None:
        """订阅事件"""
        pass


class WorkflowEngine(ABC):
    """工作流引擎接口"""

    @abstractmethod
    async def execute(
        self,
        workflow_id: str,
        parameters: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """执行工作流"""
        pass

    @abstractmethod
    async def cancel(self, execution_id: str) -> bool:
        """取消执行"""
        pass

    @abstractmethod
    async def get_status(self, execution_id: str) -> dict[str, Any]:
        """获取执行状态"""
        pass


class PackageManager(ABC):
    """包管理器接口"""

    @abstractmethod
    async def list_environments(self) -> list[dict[str, Any]]:
        """列出所有环境"""
        pass

    @abstractmethod
    async def create_environment(
        self,
        name: str,
        python_version: str,
        packages: list[str] | None = None,
    ) -> dict[str, Any]:
        """创建环境"""
        pass

    @abstractmethod
    async def remove_environment(self, name: str) -> bool:
        """删除环境"""
        pass

    @abstractmethod
    async def install_packages(
        self,
        env_name: str,
        packages: list[str],
    ) -> bool:
        """安装包"""
        pass


class SearchService(ABC):
    """搜索服务接口"""

    @abstractmethod
    async def search(
        self,
        query: str,
        index: str | None = None,
        filters: dict[str, Any] | None = None,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """执行搜索"""
        pass

    @abstractmethod
    async def index_document(
        self,
        index: str,
        doc_id: str,
        document: dict[str, Any],
    ) -> bool:
        """索引文档"""
        pass


class MetricsCollector(ABC):
    """指标收集接口"""

    @abstractmethod
    def record_counter(
        self,
        name: str,
        value: int = 1,
        labels: dict[str, str] | None = None,
    ) -> None:
        """记录计数器"""
        pass

    @abstractmethod
    def record_histogram(
        self,
        name: str,
        value: float,
        labels: dict[str, str] | None = None,
    ) -> None:
        """记录直方图"""
        pass

    @abstractmethod
    def record_gauge(
        self,
        name: str,
        value: float,
        labels: dict[str, str] | None = None,
    ) -> None:
        """记录仪表盘"""
        pass


class JupyterKernelService(ABC):
    """Jupyter 内核服务接口 - 最小化实现"""

    @abstractmethod
    async def start_kernel(self, kernel_name: str = "python3") -> str:
        """启动内核，返回 kernel_id"""
        pass

    @abstractmethod
    async def shutdown_kernel(self, kernel_id: str) -> bool:
        """关闭内核"""
        pass

    @abstractmethod
    async def execute_code(
        self,
        kernel_id: str,
        code: str,
        execution_id: str | None = None,
    ) -> AsyncIterator[dict[str, Any]]:
        """执行代码，返回执行结果流"""
        pass

    @abstractmethod
    async def interrupt_kernel(self, kernel_id: str) -> bool:
        """中断内核执行"""
        pass

    @abstractmethod
    async def get_kernel_status(self, kernel_id: str) -> dict[str, Any]:
        """获取内核状态"""
        pass

    @abstractmethod
    async def list_kernels(self) -> list[dict[str, Any]]:
        """列出所有活跃内核"""
        pass
