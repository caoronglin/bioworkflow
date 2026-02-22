"""Monitoring endpoints for Prometheus metrics."""

from typing import Dict, Any
from fastapi import APIRouter
from prometheus_client import (
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)
from prometheus_client.exposition import CONTENT_TYPE_LATEST


router = APIRouter()

# Metrics definitions
WORKFLOW_COUNT = Gauge("workflow_count", "Number of workflows")
TASK_COUNT = Gauge("task_count", "Number of tasks")
EXECUTION_COUNT = Gauge("execution_count", "Number of executions")

EXECUTION_DURATION = Histogram(
    "execution_duration_seconds",
    "Execution duration in seconds",
    ["workflow", "status"],
)
TASK_DURATION = Histogram(
    "task_duration_seconds",
    "Task execution duration in seconds",
    ["workflow", "task"],
)

ERROR_COUNT = Counter("error_count", "Number of errors", ["type"])


def get_metrics_app():
    """Get metrics application."""
    from fastapi import FastAPI

    metrics_app = FastAPI(title="Workflow Service Metrics")

    @metrics_app.get("/metrics")
    async def metrics():
        """Prometheus metrics endpoint."""
        return generate_latest()

    return metrics_app


@router.get("/metrics")
async def get_metrics():
    """Prometheus metrics endpoint."""
    return generate_latest()


@router.get("/stats")
async def get_statistics():
    """Get comprehensive statistics."""
    return {
        "workflows": {
            "total": WORKFLOW_COUNT._value.get(),
            "active": WORKFLOW_COUNT._value.get(),
        },
        "tasks": {
            "total": TASK_COUNT._value.get(),
            "pending": TASK_COUNT._value.get(),
        },
        "executions": {
            "total": EXECUTION_COUNT._value.get(),
            "running": EXECUTION_COUNT._value.get(),
        },
    }
