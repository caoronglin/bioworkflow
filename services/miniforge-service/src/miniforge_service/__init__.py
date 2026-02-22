"""Miniforge Service - Environment management microservice for BioWorkflow.

This package provides a FastAPI-based microservice for managing Conda/Mamba
environments using Miniforge.
"""

__version__ = "0.1.0-alpha.1"
__author__ = "BioWorkflow Team"
__email__ = "team@bioworkflow.org"

from miniforge_service.core.models import (
    Environment,
    EnvironmentCreate,
    EnvironmentUpdate,
    Package,
    PackageInstall,
)
from miniforge_service.core.manager import MiniforgeManager

__all__ = [
    "Environment",
    "EnvironmentCreate",
    "EnvironmentUpdate",
    "Package",
    "PackageInstall",
    "MiniforgeManager",
]
