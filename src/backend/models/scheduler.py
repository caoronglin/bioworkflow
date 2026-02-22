"""
Scheduler-related models for task scheduling and resource allocation.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ScheduleStatus(str, Enum):
    """Schedule request status."""

    PENDING = "pending"
    SCHEDULED = "scheduled"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class SchedulePriority(int, Enum):
    """Schedule priority levels."""

    LOW = 1
    NORMAL = 5
    HIGH = 10
    CRITICAL = 20


class ScheduleRequest(BaseModel):
    """Request to schedule a task or pipeline."""

    task_id: str = Field(..., description="ID of the task to schedule")
    pipeline_id: Optional[str] = Field(None, description="ID of the parent pipeline")
    priority: SchedulePriority = Field(SchedulePriority.NORMAL, description="Scheduling priority")
    resources: Dict[str, Any] = Field(default_factory=dict, description="Resource requirements")
    dependencies: List[str] = Field(default_factory=list, description="Task dependencies")
    scheduled_at: Optional[datetime] = Field(None, description="When to schedule the task")
    timeout: Optional[int] = Field(None, description="Timeout in seconds")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    class Config:
        json_schema_extra = {
            "example": {
                "task_id": "task-123",
                "pipeline_id": "pipeline-456",
                "priority": 5,
                "resources": {"cpu": 2, "memory": "4G"},
                "dependencies": ["task-001", "task-002"],
            }
        }


class ScheduleResponse(BaseModel):
    """Response from a schedule request."""

    schedule_id: str = Field(..., description="Unique schedule ID")
    task_id: str = Field(..., description="ID of the scheduled task")
    pipeline_id: Optional[str] = Field(None, description="ID of the parent pipeline")
    status: ScheduleStatus = Field(..., description="Current schedule status")
    priority: SchedulePriority = Field(..., description="Schedule priority")
    scheduled_at: datetime = Field(..., description="When the task was scheduled")
    started_at: Optional[datetime] = Field(None, description="When the task started")
    completed_at: Optional[datetime] = Field(None, description="When the task completed")
    worker_id: Optional[str] = Field(None, description="ID of the worker executing the task")
    result: Optional[Dict[str, Any]] = Field(None, description="Task execution result")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    retry_count: int = Field(0, description="Number of retry attempts")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    class Config:
        json_schema_extra = {
            "example": {
                "schedule_id": "sched-789",
                "task_id": "task-123",
                "status": "scheduled",
                "priority": 5,
                "scheduled_at": "2024-01-15T10:00:00Z",
            }
        }


class ScheduleStats(BaseModel):
    """Statistics for scheduling operations."""

    total_scheduled: int = Field(0, description="Total number of scheduled tasks")
    pending: int = Field(0, description="Number of pending tasks")
    running: int = Field(0, description="Number of running tasks")
    completed: int = Field(0, description="Number of completed tasks")
    failed: int = Field(0, description="Number of failed tasks")
    cancelled: int = Field(0, description="Number of cancelled tasks")
    average_wait_time: Optional[float] = Field(None, description="Average wait time in seconds")
    average_execution_time: Optional[float] = Field(
        None, description="Average execution time in seconds"
    )
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update time")


class ResourceAllocation(BaseModel):
    """Resource allocation information."""

    schedule_id: str = Field(..., description="Schedule ID")
    resources: Dict[str, Any] = Field(..., description="Allocated resources")
    allocated_at: datetime = Field(..., description="When resources were allocated")
    expires_at: Optional[datetime] = Field(None, description="When allocation expires")


class ScheduleFilter(BaseModel):
    """Filter options for schedule queries."""

    task_ids: Optional[List[str]] = Field(None, description="Filter by task IDs")
    pipeline_ids: Optional[List[str]] = Field(None, description="Filter by pipeline IDs")
    statuses: Optional[List[ScheduleStatus]] = Field(None, description="Filter by status")
    priorities: Optional[List[SchedulePriority]] = Field(None, description="Filter by priority")
    worker_ids: Optional[List[str]] = Field(None, description="Filter by worker ID")
    scheduled_after: Optional[datetime] = Field(None, description="Scheduled after this time")
    scheduled_before: Optional[datetime] = Field(None, description="Scheduled before this time")
    has_error: Optional[bool] = Field(None, description="Filter by error status")
