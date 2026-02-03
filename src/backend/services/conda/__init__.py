"""
services 子模块 - Conda 包管理

提供 Conda 环境管理、包安装、换源等功能
"""

from .manager import (
    CondaManager,
    CondaEnvironment,
    CondaPackage,
    CondaError,
    get_conda_manager,
)
from .channels import (
    ChannelManager,
    ChannelConfig,
    MIRROR_SOURCES,
    BIOINFORMATICS_CHANNELS,
    get_channel_manager,
)

__all__ = [
    "CondaManager",
    "CondaEnvironment",
    "CondaPackage",
    "CondaError",
    "get_conda_manager",
    "ChannelManager",
    "ChannelConfig",
    "MIRROR_SOURCES",
    "BIOINFORMATICS_CHANNELS",
    "get_channel_manager",
]
