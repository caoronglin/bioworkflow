"""
Jupyter 内核管理服务 - 最小化解耦实现

通过 jupyter_client 与内核通信，不依赖完整的 Jupyter Lab
"""

import asyncio
import json
import uuid
from dataclasses import dataclass, field
from typing import Any, AsyncIterator

from jupyter_client import KernelManager
from jupyter_client.multikernelmanager import MultiKernelManager
from loguru import logger

from backend.core.interfaces import JupyterKernelService


@dataclass
class KernelSession:
    """内核会话"""
    kernel_id: str
    kernel_name: str
    manager: KernelManager
    client: Any = field(default=None)
    created_at: str = field(default_factory=lambda: __import__('datetime').datetime.utcnow().isoformat())
    last_activity: str = field(default_factory=lambda: __import__('datetime').datetime.utcnow().isoformat())
    execution_count: int = field(default=0)


class JupyterKernelManager(JupyterKernelService):
    """
    Jupyter 内核管理器

    最小化实现，仅包含核心功能：
    - 启动/停止内核
    - 代码执行
    - 结果流式返回
    """

    def __init__(self, kernel_timeout: int = 60):
        self._multi_manager = MultiKernelManager()
        self._kernels: dict[str, KernelSession] = {}
        self._kernel_timeout = kernel_timeout
        self._lock = asyncio.Lock()

    async def start_kernel(self, kernel_name: str = "python3") -> str:
        """
        启动新内核

        Args:
            kernel_name: 内核类型，如 python3, ir, julia-1.9

        Returns:
            kernel_id: 内核唯一标识
        """
        async with self._lock:
            try:
                # 启动内核
                kernel_id = self._multi_manager.start_kernel(kernel_name=kernel_name)
                manager = self._multi_manager.get_kernel(kernel_id)
                client = manager.client()

                # 创建会话
                session = KernelSession(
                    kernel_id=kernel_id,
                    kernel_name=kernel_name,
                    manager=manager,
                    client=client,
                )
                self._kernels[kernel_id] = session

                logger.info(f"Kernel started: {kernel_id} ({kernel_name})")
                return kernel_id

            except Exception as e:
                logger.error(f"Failed to start kernel: {e}")
                raise

    async def shutdown_kernel(self, kernel_id: str) -> bool:
        """关闭内核"""
        async with self._lock:
            if kernel_id not in self._kernels:
                return False

            try:
                session = self._kernels[kernel_id]

                # 关闭客户端
                if session.client:
                    session.client.stop_channels()

                # 关闭内核
                self._multi_manager.shutdown_kernel(kernel_id)

                # 移除会话
                del self._kernels[kernel_id]

                logger.info(f"Kernel shutdown: {kernel_id}")
                return True

            except Exception as e:
                logger.error(f"Failed to shutdown kernel {kernel_id}: {e}")
                return False

    async def execute_code(
        self,
        kernel_id: str,
        code: str,
        execution_id: str | None = None,
    ) -> AsyncIterator[dict[str, Any]]:
        """
        执行代码并流式返回结果

        Yields:
            执行结果消息，格式如下:
            {
                "type": "status" | "stream" | "display_data" | "execute_result" | "error",
                "content": {...},
                "execution_id": str
            }
        """
        if kernel_id not in self._kernels:
            yield {
                "type": "error",
                "content": {"message": f"Kernel {kernel_id} not found"},
                "execution_id": execution_id,
            }
            return

        session = self._kernels[kernel_id]
        execution_id = execution_id or str(uuid.uuid4())

        try:
            # 更新活动时间和执行计数
            session.last_activity = __import__('datetime').datetime.utcnow().isoformat()
            session.execution_count += 1

            client = session.client

            # 发送执行请求
            msg_id = client.execute(code)

            # 等待并处理响应
            while True:
                try:
                    # 设置超时
                    msg = await asyncio.wait_for(
                        asyncio.to_thread(client.get_iopub_msg, timeout=1),
                        timeout=self._kernel_timeout,
                    )

                    msg_type = msg["header"]["msg_type"]
                    content = msg["content"]

                    # 处理不同类型的消息
                    if msg_type == "status":
                        yield {
                            "type": "status",
                            "content": {"execution_state": content.get("execution_state")},
                            "execution_id": execution_id,
                        }

                        if content.get("execution_state") == "idle":
                            break

                    elif msg_type == "stream":
                        yield {
                            "type": "stream",
                            "content": {
                                "name": content.get("name"),
                                "text": content.get("text"),
                            },
                            "execution_id": execution_id,
                        }

                    elif msg_type == "display_data":
                        yield {
                            "type": "display_data",
                            "content": {
                                "data": content.get("data"),
                                "metadata": content.get("metadata"),
                            },
                            "execution_id": execution_id,
                        }

                    elif msg_type == "execute_result":
                        yield {
                            "type": "execute_result",
                            "content": {
                                "execution_count": content.get("execution_count"),
                                "data": content.get("data"),
                                "metadata": content.get("metadata"),
                            },
                            "execution_id": execution_id,
                        }

                    elif msg_type == "error":
                        yield {
                            "type": "error",
                            "content": {
                                "ename": content.get("ename"),
                                "evalue": content.get("evalue"),
                                "traceback": content.get("traceback"),
                            },
                            "execution_id": execution_id,
                        }

                except asyncio.TimeoutError:
                    yield {
                        "type": "error",
                        "content": {"message": "Execution timeout"},
                        "execution_id": execution_id,
                    }
                    break

        except Exception as e:
            logger.error(f"Error executing code in kernel {kernel_id}: {e}")
            yield {
                "type": "error",
                "content": {"message": str(e)},
                "execution_id": execution_id,
            }

    async def interrupt_kernel(self, kernel_id: str) -> bool:
        """中断内核执行"""
        if kernel_id not in self._kernels:
            return False

        try:
            self._multi_manager.interrupt_kernel(kernel_id)
            logger.info(f"Kernel interrupted: {kernel_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to interrupt kernel {kernel_id}: {e}")
            return False

    async def get_kernel_status(self, kernel_id: str) -> dict[str, Any]:
        """获取内核状态"""
        if kernel_id not in self._kernels:
            return {"status": "not_found"}

        session = self._kernels[kernel_id]

        return {
            "kernel_id": kernel_id,
            "kernel_name": session.kernel_name,
            "status": "active",
            "created_at": session.created_at,
            "last_activity": session.last_activity,
            "execution_count": session.execution_count,
        }

    async def list_kernels(self) -> list[dict[str, Any]]:
        """列出所有活跃内核"""
        return [
            {
                "kernel_id": k.kernel_id,
                "kernel_name": k.kernel_name,
                "created_at": k.created_at,
                "last_activity": k.last_activity,
                "execution_count": k.execution_count,
            }
            for k in self._kernels.values()
        ]

    async def shutdown_all(self) -> None:
        """关闭所有内核"""
        kernel_ids = list(self._kernels.keys())
        for kernel_id in kernel_ids:
            await self.shutdown_kernel(kernel_id)

        self._multi_manager.shutdown_all()
        logger.info("All kernels shutdown")
