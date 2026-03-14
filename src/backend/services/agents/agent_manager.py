"""
智能体管理器

管理所有AgentScope智能体的生命周期、注册和发现。
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime
from typing import Any, TypeVar

from loguru import logger

from backend.services.agents.base_agent import (
    AgentCapability,
    AgentConfig,
    AgentResult,
    BaseAgent,
)
from backend.services.agents.workflow_agent import WorkflowAgent

T = TypeVar("T", bound=BaseAgent)


@dataclass
class AgentInfo:
    """智能体信息"""

    name: str
    agent_type: str
    capabilities: list[AgentCapability]
    status: str
    created_at: datetime
    last_activity: datetime | None
    execution_count: int
    metadata: dict[str, Any]


class AgentManager:
    """
    智能体管理器

    单例模式，管理所有智能体的生命周期。
    """

    _instance: AgentManager | None = None
    _lock = asyncio.Lock()

    def __new__(cls) -> AgentManager:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return

        self._agents: dict[str, BaseAgent] = {}
        self._agent_types: dict[str, type[BaseAgent]] = {}
        self._creation_times: dict[str, datetime] = {}
        self._initialized = True

        logger.info("AgentManager initialized")

    def register_agent_type(
        self,
        name: str,
        agent_class: type[BaseAgent],
    ) -> None:
        """注册智能体类型"""
        self._agent_types[name] = agent_class
        logger.debug(f"Registered agent type: {name}")

    async def create_agent(
        self,
        name: str,
        agent_type: str | None = None,
        config: AgentConfig | None = None,
        **kwargs: Any,
    ) -> BaseAgent:
        """创建智能体实例"""
        async with self._lock:
            if name in self._agents:
                raise ValueError(f"Agent with name '{name}' already exists")

            # 确定智能体类
            if agent_type and agent_type in self._agent_types:
                agent_class = self._agent_types[agent_type]
            else:
                agent_class = WorkflowAgent

            # 创建配置
            if config is None:
                config = AgentConfig(
                    name=name,
                    model_name=kwargs.get("model_name", "gpt-4"),
                    capabilities=kwargs.get("capabilities", []),
                )

            # 创建实例
            agent = agent_class(config)

            # 存储
            self._agents[name] = agent
            self._creation_times[name] = agent._created_at

            logger.info(f"Created agent: {name} (type: {agent_class.__name__})")

            return agent

    async def get_agent(self, name: str) -> BaseAgent | None:
        """获取智能体实例"""
        return self._agents.get(name)

    async def remove_agent(self, name: str, terminate: bool = True) -> bool:
        """移除智能体"""
        async with self._lock:
            agent = self._agents.get(name)
            if agent is None:
                return False

            if terminate:
                await agent.terminate()

            del self._agents[name]
            del self._creation_times[name]

            logger.info(f"Removed agent: {name}")
            return True

    async def execute_task(
        self,
        agent_name: str,
        task: str,
        context: dict[str, Any] | None = None,
    ) -> AgentResult:
        """在指定智能体上执行任务"""
        agent = await self.get_agent(agent_name)
        if agent is None:
            return AgentResult(
                success=False,
                content="",
                error=f"Agent '{agent_name}' not found",
            )

        return await agent.execute(task, context)

    def list_agents(self) -> list[AgentInfo]:
        """列出所有智能体信息"""
        return [
            AgentInfo(
                name=name,
                agent_type=agent.__class__.__name__,
                capabilities=agent.capabilities,
                status=agent.status.name,
                created_at=self._creation_times.get(name, agent._created_at),
                last_activity=agent._last_activity,
                execution_count=agent.execution_count,
                metadata=agent._config.metadata,
            )
            for name, agent in self._agents.items()
        ]

    async def cleanup(self) -> None:
        """清理所有智能体"""
        async with self._lock:
            for name, agent in list(self._agents.items()):
                try:
                    await agent.terminate()
                    logger.debug(f"Terminated agent: {name}")
                except Exception as exc:
                    logger.error(f"Failed to terminate agent {name}: {exc}")

            self._agents.clear()
            self._creation_times.clear()

            logger.info("AgentManager cleanup completed")


# 全局管理器实例
_agent_manager: AgentManager | None = None
_manager_lock = asyncio.Lock()


async def get_agent_manager() -> AgentManager:
    """获取AgentManager单例"""
    global _agent_manager

    if _agent_manager is None:
        async with _manager_lock:
            if _agent_manager is None:
                _agent_manager = AgentManager()

                # 注册默认智能体类型
                _agent_manager.register_agent_type("workflow", WorkflowAgent)

                logger.info("AgentManager singleton initialized with default agent types")

    return _agent_manager


async def reset_agent_manager() -> None:
    """重置AgentManager（主要用于测试）"""
    global _agent_manager

    if _agent_manager is not None:
        await _agent_manager.cleanup()
        _agent_manager = None
        logger.info("AgentManager reset")
