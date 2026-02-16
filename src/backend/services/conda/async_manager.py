"""
异步 Conda 环境管理器

基于 WorkflowExecutionEngine 的异步模式实现，
提供高性能的 Conda 环境管理功能，支持进度跟踪、并发控制和实时监控。
"""

from __future__ import annotations

import asyncio
import json
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, AsyncIterator, Callable, Protocol

from loguru import logger

from backend.core.logging import get_logger

logger = get_logger(__name__)


class OperationStatus(str, Enum):
    """操作执行状态"""
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


@dataclass
class OperationProgress:
    """操作进度信息"""
    operation_id: str
    operation_type: str
    status: OperationStatus
    message: str = ""
    progress_percentage: float = 0.0
    start_time: float | None = None
    end_time: float | None = None
    details: dict[str, Any] = field(default_factory=dict)
    logs: list[str] = field(default_factory=list)

    @property
    def duration_seconds(self) -> float:
        """计算执行持续时间"""
        if self.start_time is None:
            return 0.0
        end = self.end_time or time.time()
        return end - self.start_time

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "operation_id": self.operation_id,
            "operation_type": self.operation_type,
            "status": self.status.value,
            "message": self.message,
            "progress_percentage": self.progress_percentage,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_seconds": self.duration_seconds,
            "details": self.details,
            "logs": self.logs,
        }


class ProgressCallback(Protocol):
    """进度回调协议"""

    async def __call__(self, progress: OperationProgress) -> None:
        """进度更新时调用"""
        ...


class AsyncCondaManager:
    """
    异步 Conda 环境管理器

    提供完整的异步 Conda 环境管理功能，包括：
    - 环境的创建、删除、列表查询
    - 包的安装、更新、删除
    - 实时进度跟踪
    - 并发控制
    - 操作取消支持
    """

    def __init__(
        self,
        conda_path: str = "conda",
        max_concurrent_operations: int = 3,
        default_timeout: int = 600,
    ):
        """
        初始化异步 Conda 管理器

        Args:
            conda_path: Conda 可执行文件路径
            max_concurrent_operations: 最大并发操作数
            default_timeout: 默认超时时间（秒）
        """
        self._conda_path = conda_path
        self._max_concurrent_operations = max_concurrent_operations
        self._default_timeout = default_timeout

        # 并发控制
        self._semaphore = asyncio.Semaphore(max_concurrent_operations)

        # 操作跟踪
        self._operations: dict[str, OperationProgress] = {}
        self._cancelled: set[str] = set()

        # 回调函数
        self._callbacks: list[ProgressCallback] = []

        # 操作锁
        self._operation_lock = asyncio.Lock()

    def add_progress_callback(self, callback: ProgressCallback) -> None:
        """添加进度回调函数"""
        self._callbacks.append(callback)

    def remove_progress_callback(self, callback: ProgressCallback) -> None:
        """移除进度回调函数"""
        if callback in self._callbacks:
            self._callbacks.remove(callback)

    async def _notify_progress(self, progress: OperationProgress) -> None:
        """通知所有回调函数"""
        for callback in self._callbacks:
            try:
                await callback(progress)
            except Exception as e:
                logger.error(f"进度回调错误: {e}")

    def _create_progress(
        self,
        operation_type: str,
        message: str = "",
    ) -> OperationProgress:
        """创建新的进度对象"""
        operation_id = str(uuid.uuid4())
        progress = OperationProgress(
            operation_id=operation_id,
            operation_type=operation_type,
            status=OperationStatus.PENDING,
            message=message,
            start_time=time.time(),
        )
        self._operations[operation_id] = progress
        return progress

    async def _run_conda_command(
        self,
        args: list[str],
        operation_id: str,
        timeout: int | None = None,
        cwd: str | None = None,
    ) -> dict[str, Any]:
        """
        异步运行 Conda 命令

        Args:
            args: Conda 命令参数
            operation_id: 操作 ID
            timeout: 超时时间
            cwd: 工作目录

        Returns:
            命令执行结果
        """
        timeout = timeout or self._default_timeout
        cmd = [self._conda_path] + args

        progress = self._operations.get(operation_id)
        if progress:
            progress.status = OperationStatus.RUNNING
            progress.message = f"执行: {' '.join(cmd[:5])}..."
            await self._notify_progress(progress)

        logger.debug(f"执行 Conda 命令: {' '.join(cmd)}")

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd,
            )

            # 检查是否已取消
            if operation_id in self._cancelled:
                process.terminate()
                await process.wait()
                raise asyncio.CancelledError(f"操作已取消: {operation_id}")

            # 等待完成或超时
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout,
            )

            if progress:
                progress.logs.append(stdout.decode())
                if stderr:
                    progress.logs.append(stderr.decode())

            if process.returncode != 0:
                error_msg = stderr.decode().strip()
                raise RuntimeError(f"Conda 命令失败: {error_msg}")

            # 尝试解析 JSON 输出
            try:
                result = json.loads(stdout.decode())
            except json.JSONDecodeError:
                result = {"output": stdout.decode(), "success": True}

            if progress:
                progress.status = OperationStatus.COMPLETED
                progress.progress_percentage = 100.0
                progress.message = "操作完成"
                progress.end_time = time.time()
                await self._notify_progress(progress)

            return result

        except asyncio.TimeoutError:
            if progress:
                progress.status = OperationStatus.TIMEOUT
                progress.message = f"操作超时（{timeout}秒）"
                progress.end_time = time.time()
                await self._notify_progress(progress)
            raise TimeoutError(f"Conda 命令超时: {timeout}秒")

        except asyncio.CancelledError:
            if progress:
                progress.status = OperationStatus.CANCELLED
                progress.message = "操作已取消"
                progress.end_time = time.time()
                await self._notify_progress(progress)
            raise

        except Exception as e:
            if progress:
                progress.status = OperationStatus.FAILED
                progress.message = f"操作失败: {str(e)}"
                progress.end_time = time.time()
                await self._notify_progress(progress)
            raise

    # ============== 公共 API 方法 ==============

    async def create_environment(
        self,
        name: str,
        python_version: str = "3.11",
        packages: list[str] | None = None,
        channels: list[str] | None = None,
        timeout: int | None = None,
    ) -> str:
        """
        异步创建 Conda 环境

        Args:
            name: 环境名称
            python_version: Python 版本
            packages: 额外安装的包列表
            channels: 频道列表
            timeout: 超时时间

        Returns:
            操作 ID
        """
        progress = self._create_progress(
            operation_type="create_environment",
            message=f"创建环境: {name}",
        )
        operation_id = progress.operation_id

        # 在后台执行
        asyncio.create_task(
            self._create_environment_async(
                operation_id=operation_id,
                name=name,
                python_version=python_version,
                packages=packages or [],
                channels=channels or ["conda-forge"],
                timeout=timeout,
            )
        )

        return operation_id

    async def _create_environment_async(
        self,
        operation_id: str,
        name: str,
        python_version: str,
        packages: list[str],
        channels: list[str],
        timeout: int | None,
    ) -> None:
        """异步创建环境的内部实现"""
        async with self._semaphore:
            if operation_id in self._cancelled:
                return

            try:
                # 构建命令
                args = ["create", "-n", name, f"python={python_version}", "-y"]

                # 添加频道
                for channel in channels:
                    args.extend(["-c", channel])

                # 添加包
                if packages:
                    args.extend(packages)

                # 执行命令
                await self._run_conda_command(
                    args=args,
                    operation_id=operation_id,
                    timeout=timeout,
                )

                logger.info(f"环境创建成功: {name}")

            except Exception as e:
                logger.error(f"环境创建失败: {e}")

    async def delete_environment(
        self,
        name: str,
        timeout: int | None = None,
    ) -> str:
        """
        异步删除 Conda 环境

        Args:
            name: 环境名称
            timeout: 超时时间

        Returns:
            操作 ID
        """
        progress = self._create_progress(
            operation_type="delete_environment",
            message=f"删除环境: {name}",
        )
        operation_id = progress.operation_id

        asyncio.create_task(
            self._delete_environment_async(
                operation_id=operation_id,
                name=name,
                timeout=timeout,
            )
        )

        return operation_id

    async def _delete_environment_async(
        self,
        operation_id: str,
        name: str,
        timeout: int | None,
    ) -> None:
        """异步删除环境的内部实现"""
        async with self._semaphore:
            if operation_id in self._cancelled:
                return

            try:
                await self._run_conda_command(
                    args=["env", "remove", "-n", name, "-y"],
                    operation_id=operation_id,
                    timeout=timeout,
                )
                logger.info(f"环境删除成功: {name}")
            except Exception as e:
                logger.error(f"环境删除失败: {e}")

    async def list_environments(self) -> list[dict[str, Any]]:
        """
        异步列出所有 Conda 环境

        Returns:
            环境列表
        """
        try:
            result = await self._run_conda_command(
                args=["env", "list", "--json"],
                operation_id=str(uuid.uuid4()),
            )

            envs = []
            for env_info in result.get("envs", []):
                name = Path(env_info).name if "/" in env_info else env_info
                envs.append({
                    "name": name,
                    "path": env_info,
                    "is_active": result.get("active_prefix") == env_info,
                })

            return envs

        except Exception as e:
            logger.error(f"列出环境失败: {e}")
            return []

    async def get_environment_info(self, name: str) -> dict[str, Any] | None:
        """
        获取环境详细信息

        Args:
            name: 环境名称

        Returns:
            环境信息字典，失败返回 None
        """
        try:
            # 获取环境列表
            envs = await self.list_environments()
            env = next((e for e in envs if e["name"] == name), None)

            if not env:
                return None

            # 获取包列表
            packages = await self.list_packages(name)

            return {
                "name": name,
                "path": env["path"],
                "is_active": env["is_active"],
                "packages_count": len(packages),
                "packages": packages[:50],  # 只返回前50个包
            }

        except Exception as e:
            logger.error(f"获取环境信息失败: {e}")
            return None

    async def install_packages(
        self,
        env_name: str,
        packages: list[str],
        channels: list[str] | None = None,
        timeout: int | None = None,
    ) -> str:
        """
        异步安装包

        Args:
            env_name: 环境名称
            packages: 包列表
            channels: 频道列表
            timeout: 超时时间

        Returns:
            操作 ID
        """
        progress = self._create_progress(
            operation_type="install_packages",
            message=f"在 {env_name} 中安装包: {', '.join(packages)}",
        )
        operation_id = progress.operation_id

        asyncio.create_task(
            self._install_packages_async(
                operation_id=operation_id,
                env_name=env_name,
                packages=packages,
                channels=channels,
                timeout=timeout,
            )
        )

        return operation_id

    async def _install_packages_async(
        self,
        operation_id: str,
        env_name: str,
        packages: list[str],
        channels: list[str] | None,
        timeout: int | None,
    ) -> None:
        """异步安装包的内部实现"""
        async with self._semaphore:
            if operation_id in self._cancelled:
                return

            try:
                args = ["install", "-n", env_name, "-y"]

                if channels:
                    for channel in channels:
                        args.extend(["-c", channel])

                args.extend(packages)

                await self._run_conda_command(
                    args=args,
                    operation_id=operation_id,
                    timeout=timeout,
                )

                logger.info(f"包安装成功: {packages} 到环境 {env_name}")

            except Exception as e:
                logger.error(f"包安装失败: {e}")

    async def update_packages(
        self,
        env_name: str,
        packages: list[str] | None = None,
        timeout: int | None = None,
    ) -> str:
        """
        异步更新包

        Args:
            env_name: 环境名称
            packages: 包列表，None 表示更新所有包
            timeout: 超时时间

        Returns:
            操作 ID
        """
        progress = self._create_progress(
            operation_type="update_packages",
            message=f"更新 {env_name} 中的包",
        )
        operation_id = progress.operation_id

        asyncio.create_task(
            self._update_packages_async(
                operation_id=operation_id,
                env_name=env_name,
                packages=packages,
                timeout=timeout,
            )
        )

        return operation_id

    async def _update_packages_async(
        self,
        operation_id: str,
        env_name: str,
        packages: list[str] | None,
        timeout: int | None,
    ) -> None:
        """异步更新包的内部实现"""
        async with self._semaphore:
            if operation_id in self._cancelled:
                return

            try:
                args = ["update", "-n", env_name, "-y"]

                if packages:
                    args.extend(packages)
                else:
                    args.append("--all")

                await self._run_conda_command(
                    args=args,
                    operation_id=operation_id,
                    timeout=timeout,
                )

                logger.info(f"包更新成功: 环境 {env_name}")

            except Exception as e:
                logger.error(f"包更新失败: {e}")

    async def remove_packages(
        self,
        env_name: str,
        packages: list[str],
        timeout: int | None = None,
    ) -> str:
        """
        异步删除包

        Args:
            env_name: 环境名称
            packages: 包列表
            timeout: 超时时间

        Returns:
            操作 ID
        """
        progress = self._create_progress(
            operation_type="remove_packages",
            message=f"从 {env_name} 中删除包: {', '.join(packages)}",
        )
        operation_id = progress.operation_id

        asyncio.create_task(
            self._remove_packages_async(
                operation_id=operation_id,
                env_name=env_name,
                packages=packages,
                timeout=timeout,
            )
        )

        return operation_id

    async def _remove_packages_async(
        self,
        operation_id: str,
        env_name: str,
        packages: list[str],
        timeout: int | None,
    ) -> None:
        """异步删除包的内部实现"""
        async with self._semaphore:
            if operation_id in self._cancelled:
                return

            try:
                args = ["remove", "-n", env_name, "-y"] + packages

                await self._run_conda_command(
                    args=args,
                    operation_id=operation_id,
                    timeout=timeout,
                )

                logger.info(f"包删除成功: {packages} 从环境 {env_name}")

            except Exception as e:
                logger.error(f"包删除失败: {e}")

    async def list_packages(
        self,
        env_name: str,
    ) -> list[dict[str, Any]]:
        """
        异步列出环境中的包

        Args:
            env_name: 环境名称

        Returns:
            包列表
        """
        try:
            result = await self._run_conda_command(
                args=["list", "-n", env_name, "--json"],
                operation_id=str(uuid.uuid4()),
            )

            packages = []
            pkg_list = result if isinstance(result, list) else result.get("packages", [])

            for pkg in pkg_list:
                if isinstance(pkg, dict):
                    packages.append({
                        "name": pkg.get("name", ""),
                        "version": pkg.get("version", ""),
                        "channel": pkg.get("channel", ""),
                        "build": pkg.get("build_string"),
                    })

            return packages

        except Exception as e:
            logger.error(f"列出包失败: {e}")
            return []

    async def search_packages(
        self,
        query: str,
        channel: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """
        异步搜索包

        Args:
            query: 搜索关键词
            channel: 搜索频道
            limit: 返回结果数量限制

        Returns:
            搜索结果列表
        """
        try:
            args = ["search", query, "--json"]
            if channel:
                args.extend(["-c", channel])

            result = await self._run_conda_command(
                args=args,
                operation_id=str(uuid.uuid4()),
            )

            packages = []
            for name, variants in result.items():
                for variant in variants[:limit]:
                    packages.append({
                        "name": name,
                        "version": variant.get("version", ""),
                        "channel": variant.get("channel", ""),
                        "build": variant.get("build", ""),
                    })

            return packages

        except Exception as e:
            logger.error(f"搜索包失败: {e}")
            return []

    # ============== 操作管理方法 ==============

    async def get_operation_status(
        self,
        operation_id: str,
    ) -> OperationProgress | None:
        """
        获取操作状态

        Args:
            operation_id: 操作 ID

        Returns:
            操作进度对象，不存在返回 None
        """
        return self._operations.get(operation_id)

    async def list_operations(
        self,
        status: OperationStatus | None = None,
    ) -> list[OperationProgress]:
        """
        列出所有操作

        Args:
            status: 可选的状态过滤

        Returns:
            操作列表
        """
        operations = list(self._operations.values())
        if status:
            operations = [op for op in operations if op.status == status]
        return operations

    async def cancel_operation(self, operation_id: str) -> bool:
        """
        取消操作

        Args:
            operation_id: 操作 ID

        Returns:
            是否成功取消
        """
        if operation_id not in self._operations:
            return False

        progress = self._operations[operation_id]

        # 检查是否可以取消
        if progress.status in (
            OperationStatus.COMPLETED,
            OperationStatus.FAILED,
            OperationStatus.CANCELLED,
        ):
            return False

        self._cancelled.add(operation_id)
        progress.status = OperationStatus.CANCELLED
        progress.message = "操作已取消"
        progress.end_time = time.time()
        await self._notify_progress(progress)

        return True

    async def cleanup_old_operations(self, max_age_seconds: float = 3600) -> int:
        """
        清理旧的操作记录

        Args:
            max_age_seconds: 最大保留时间（秒）

        Returns:
            清理的操作数量
        """
        current_time = time.time()
        to_remove = []

        for operation_id, progress in self._operations.items():
            if progress.end_time is not None:
                if current_time - progress.end_time > max_age_seconds:
                    to_remove.append(operation_id)

        for operation_id in to_remove:
            del self._operations[operation_id]
            self._cancelled.discard(operation_id)

        return len(to_remove)

    # ============== 流式输出方法 ==============

    async def stream_operation_logs(
        self,
        operation_id: str,
    ) -> AsyncIterator[str]:
        """
        流式输出操作日志

        Args:
            operation_id: 操作 ID

        Yields:
            日志行
        """
        progress = self._operations.get(operation_id)
        if not progress:
            return

        # 输出已有日志
        for log in progress.logs:
            yield log

        # 持续输出新日志
        last_log_count = len(progress.logs)
        while progress.status in (
            OperationStatus.PENDING,
            OperationStatus.QUEUED,
            OperationStatus.RUNNING,
        ):
            if len(progress.logs) > last_log_count:
                for i in range(last_log_count, len(progress.logs)):
                    yield progress.logs[i]
                last_log_count = len(progress.logs)
            await asyncio.sleep(0.5)


# ============== 全局实例管理 ==============

_async_conda_manager: AsyncCondaManager | None = None


async def get_async_conda_manager(
    conda_path: str = "conda",
    max_concurrent_operations: int = 3,
) -> AsyncCondaManager:
    """
    获取异步 Conda 管理器实例

    Args:
        conda_path: Conda 路径
        max_concurrent_operations: 最大并发操作数

    Returns:
        AsyncCondaManager 实例
    """
    global _async_conda_manager

    if _async_conda_manager is None:
        _async_conda_manager = AsyncCondaManager(
            conda_path=conda_path,
            max_concurrent_operations=max_concurrent_operations,
        )

    return _async_conda_manager


async def close_async_conda_manager() -> None:
    """关闭异步 Conda 管理器"""
    global _async_conda_manager

    if _async_conda_manager is not None:
        # 取消所有进行中的操作
        operations = list(_async_conda_manager._operations.keys())
        for op_id in operations:
            await _async_conda_manager.cancel_operation(op_id)

        _async_conda_manager = None
