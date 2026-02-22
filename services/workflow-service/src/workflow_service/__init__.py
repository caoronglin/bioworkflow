"""Workflow Service - manages workflow execution and DAG processing.

This module provides a FastAPI microservice for managing:
- Workflow definitions and execution
- DAG (Directed Acyclic Graph) generation and traversal
- Task scheduling and dependency management
- Workflow status tracking and monitoring

Key Components:
- Workflow management API
- DAG generation from Snakemake workflows
- Task scheduler with various scheduling strategies
- Workflow execution engine
- Visualization tools for workflow diagrams

"""

__version__ = "0.1.0"
__author__ = "Your Name"
__email__ = "you@example.com"

from .core import (
    create_app,
    get_app,
)
from .types import (
    Workflow,
    Task,
    Execution,
)

__all__ = [
    "create_app",
    "get_app",
    "Workflow",
    "Task",
    "Execution",
]
