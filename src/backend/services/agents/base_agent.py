"""
AgentScope基础智能体抽象类

定义所有智能体的通用接口和行为。
"""

from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Callable, Protocol, TypeVar

from loguru import logger


class AgentStatus(Enum):
    """智能体状态"""

    IDLE = auto()
    RUNNING = auto()
    PAUSED = auto()
    ERROR = auto()
    TERMINATED = auto()


class AgentCapability(Enum):
    """智能体能力类型"""

    CODE_GENERATION = "code_generation"
    CODE_REVIEW = "code_review"
    WORKFLOW_DESIGN = "workflow_design"
    DATA_ANALYSIS = "data_analysis"
    DOCUMENTATION = "documentation"
    TESTING = "testing"
    DEBUGGING = "debugging"


@dataclass
class AgentConfig:
    """智能体配置"""

    name: str
    description: str = ""
    model_name: str = "gpt-4"
    temperature: float = 0.7
    max_tokens: int = 4096
    timeout: float = 60.0
    retry_count: int = 3
    capabilities: list[AgentCapability] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentResult:
    """智能体执行结果"""

    success: bool
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    execution_time: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ToolCall:
    """工具调用定义"""

    name: str
    description: str
    parameters: dict[str, Any]
    handler: Callable[..., Any] | None = None


T = TypeVar("T")


class AgentProtocol(Protocol):
    """智能体协议"""

    @property
    def name(self) -> str: ...

    @property
    def status(self) -> AgentStatus: ...

    async def execute(self, task: str, context: dict[str, Any] | None = None) -> AgentResult: ...

    async def pause(self) -> None: ...

    async def resume(self) -> None: ...

    async def terminate(self) -> None: ...


class BaseAgent(ABC):
    """
    AgentScope基础智能体抽象类

    所有具体智能体的基类，提供通用功能和接口。
    """

    def __init__(self, config: AgentConfig) -> None:
        self._config = config
        self._status = AgentStatus.IDLE
        self._created_at = datetime.now()
        self._last_activity: datetime | None = None
        self._execution_count = 0
        self._tools: dict[str, ToolCall] = {}
        self._lock = asyncio.Lock()

        logger.info(f"Initialized agent: {self.name} with capabilities: {config.capabilities}")

    @property
    def name(self) -> str:
        """智能体名称"""
        return self._config.name

    @property
    def status(self) -> AgentStatus:
        """当前状态"""
        return self._status

    @property
    def capabilities(self) -> list[AgentCapability]:
        """能力列表"""
        return self._config.capabilities

    @property
    def execution_count(self) -> int:
        """执行次数"""
        return self._execution_count

    def register_tool(self, tool: ToolCall) -> None:
        """注册工具"""
        self._tools[tool.name] = tool
        logger.debug(f"Registered tool '{tool.name}' for agent {self.name}")

    def unregister_tool(self, tool_name: str) -> None:
        """注销工具"""
        if tool_name in self._tools:
            del self._tools[tool_name]
            logger.debug(f"Unregistered tool '{tool_name}' for agent {self.name}")

    async def execute(
        self,
        task: str,
        context: dict[str, Any] | None = None,
    ) -> AgentResult:
        """
        执行任务

        Args:
            task: 任务描述
            context: 上下文信息

        Returns:
            执行结果
        """
        async with self._lock:
            if self._status == AgentStatus.TERMINATED:
                return AgentResult(
                    success=False,
                    content="",
                    error="Agent has been terminated",
                )

            if self._status == AgentStatus.PAUSED:
                return AgentResult(
                    success=False,
                    content="",
                    error="Agent is paused",
                )

            self._status = AgentStatus.RUNNING
            self._execution_count += 1

        start_time = asyncio.get_event_loop().time()

        try:
            result = await self._execute_impl(task, context or {})
            result.execution_time = asyncio.get_event_loop().time() - start_time

            self._last_activity = datetime.now()

            async with self._lock:
                if self._status != AgentStatus.TERMINATED:
                    self._status = AgentStatus.IDLE

            return result

        except Exception as exc:
            execution_time = asyncio.get_event_loop().time() - start_time

            async with self._lock:
                self._status = AgentStatus.ERROR

            logger.error(f"Agent {self.name} execution failed: {exc}")

            return AgentResult(
                success=False,
                content="",
                error=str(exc),
                execution_time=execution_time,
            )

    @abstractmethod
    async def _execute_impl(
        self,
        task: str,
        context: dict[str, Any],
    ) -> AgentResult:
        """
        具体执行实现（子类必须实现）

        Args:
            task: 任务描述
            context: 上下文信息

        Returns:
            执行结果
        """
        ...

    async def pause(self) -> None:
        """暂停智能体"""
        async with self._lock:
            if self._status == AgentStatus.RUNNING:
                self._status = AgentStatus.PAUSED
                logger.info(f"Agent {self.name} paused")

    async def resume(self) -> None:
        """恢复智能体"""
        async with self._lock:
            if self._status == AgentStatus.PAUSED:
                self._status = AgentStatus.IDLE
                logger.info(f"Agent {self.name} resumed")

    async def terminate(self) -> None:
        """终止智能体"""
        async with self._lock:
            self._status = AgentStatus.TERMINATED
            logger.info(f"Agent {self.name} terminated")

    def get_stats(self) -> dict[str, Any]:
        """获取统计信息"""
        return {
            "name": self.name,
            "status": self._status.name,
            "capabilities": [c.value for c in self._capabilities],
            "execution_count": self._execution_count,
            "created_at": self._created_at.isoformat(),
            "last_activity": self._last_activity.isoformat() if self._last_activity else None,
            "registered_tools": list(self._tools.keys()),
            "config": {
                "model_name": self._config.model_name,
                "temperature": self._config.temperature,
                "max_tokens": self._config.max_tokens,
                "timeout": self._config.timeout,
            },
        }


__all__ = [
    "BaseAgent",
    "AgentConfig",
    "AgentResult",
    "AgentStatus",
    "AgentCapability",
    "ToolCall",
    "AgentProtocol",
]
