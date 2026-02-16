"""
Conda Environment Management Services

This package provides both synchronous and asynchronous Conda environment
management services.
"""

# Synchronous manager (legacy)
from backend.services.conda.manager import CondaManager

# Asynchronous manager (new)
from backend.services.conda.async_manager import (
    AsyncCondaManager,
    CondaEnvironment,
    CondaPackage,
    CondaOperationStatus,
    CondaOperationType,
    CondaOperationProgress,
    get_conda_manager,
    shutdown_conda_manager,
    create_environment,
    delete_environment,
    list_environments,
    install_packages,
)

__all__ = [
    # Synchronous
    "CondaManager",
    # Asynchronous
    "AsyncCondaManager",
    "CondaEnvironment",
    "CondaPackage",
    "CondaOperationStatus",
    "CondaOperationType",
    "CondaOperationProgress",
    "get_conda_manager",
    "shutdown_conda_manager",
    "create_environment",
    "delete_environment",
    "list_environments",
    "install_packages",
]
