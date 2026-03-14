"""
AgentScope智能体服务层

提供基于AgentScope的智能体管理、多智能体协作、工作流自动化等功能。
"""

from backend.services.agents.agent_manager import AgentManager, get_agent_manager
from backend.services.agents.workflow_agent import WorkflowAgent
from backend.services.agents.code_agent import CodeAgent
from backend.services.agents.analysis_agent import AnalysisAgent
from backend.services.agents.multi_agent_system import MultiAgentSystem, get_multi_agent_system

__all__ = [
    "AgentManager",
    "get_agent_manager",
    "WorkflowAgent",
    "CodeAgent",
    "AnalysisAgent",
    "MultiAgentSystem",
    "get_multi_agent_system",
]
