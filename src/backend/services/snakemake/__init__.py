"""
Snakemake Workflow Services

This package provides asynchronous Snakemake workflow execution services,
following Snakemake 8.x best practices for non-blocking workflow operations.
"""

from backend.services.snakemake.workflow_engine import (
    # Enums
    WorkflowStatus,
    JobStatus,

    # Data classes
    JobInfo,
    WorkflowProgress,

    # Main engine
    WorkflowExecutionEngine,

    # Convenience functions
    get_workflow_engine,
    shutdown_workflow_engine,
    run_workflow,
    get_status,
    cancel,
    create_snakefile,
)

__all__ = [
    # Enums
    "WorkflowStatus",
    "JobStatus",

    # Data classes
    "JobInfo",
    "WorkflowProgress",

    # Main engine
    "WorkflowExecutionEngine",

    # Convenience functions
    "get_workflow_engine",
    "shutdown_workflow_engine",
    "run_workflow",
    "get_status",
    "cancel",
    "create_snakefile",
]
