"""
Worker-related models for task execution and worker management.
"""
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class WorkerStatus(str, Enum):
    """Worker node status."""
    IDLE = "idle"
    BUSY = "busy"
    OFFLINE = "offline"
    MAINTENANCE = "maintenance"
    ERROR = "error"


class WorkerType(str, Enum):
    """Type of worker node."""
    STANDARD = "standard"
    GPU = "gpu"
    HIGH_MEMORY = "high_memory"
    SPOT = "spot"
    DEDICATED = "dedicated"


class WorkerTaskStatus(str, Enum):
    """Status of a task being executed by a worker."""
    PENDING = "pending"
    PREPARING = "preparing"
    RUNNING = "running"
    CLEANING = "cleaning"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class WorkerCapabilities(BaseModel):
    """Worker node capabilities and specifications."""
    cpu_cores: int = Field(..., description="Number of CPU cores")
    memory_gb: float = Field(..., description="Memory in GB")
    disk_gb: float = Field(..., description="Disk space in GB")
    gpu_count: int = Field(0, description="Number of GPUs")
    gpu_type: Optional[str] = Field(None, description="GPU type")
    network_bandwidth_mbps: Optional[float] = Field(None, description="Network bandwidth in Mbps")
    supported_executors: List[str] = Field(default_factory=list, description="List of supported executor types")
    labels: Dict[str, str] = Field(default_factory=dict, description="Additional labels and tags")
    custom_properties: Dict[str, Any] = Field(default_factory=dict, description="Custom capability properties")


class WorkerRegistration(BaseModel):
    """Worker registration information."""
    worker_id: str = Field(..., description="Unique worker ID")
    worker_type: WorkerType = Field(WorkerType.STANDARD, description="Type of worker")
    hostname: str = Field(..., description="Worker hostname")
    ip_address: str = Field(..., description="Worker IP address")
    port: int = Field(..., description="Worker service port")
    version: str = Field(..., description="Worker software version")
    capabilities: WorkerCapabilities = Field(..., description="Worker capabilities")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    registered_at: Optional[datetime] = Field(None, description="Registration timestamp")


class Worker(BaseModel):
    """Worker node information."""
    id: str = Field(..., description="Unique worker ID")
    type: WorkerType = Field(WorkerType.STANDARD, description="Type of worker")
    status: WorkerStatus = Field(WorkerStatus.IDLE, description="Current status")
    hostname: str = Field(..., description="Worker hostname")
    ip_address: str = Field(..., description="Worker IP address")
    port: int = Field(..., description="Worker service port")
    version: str = Field(..., description="Worker software version")
    capabilities: WorkerCapabilities = Field(..., description="Worker capabilities")
    current_task_id: Optional[str] = Field(None, description="ID of currently executing task")
    task_count: int = Field(0, description="Total number of completed tasks")
    error_count: int = Field(0, description="Total number of errors")
    last_seen_at: Optional[datetime] = Field(None, description="Last heartbeat timestamp")
    registered_at: Optional[datetime] = Field(None, description="Registration timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "worker-001",
                "type": "standard",
                "status": "idle",
                "hostname": "worker-node-1",
                "ip_address": "192.168.1.100",
                "port": 8080,
                "version": "1.0.0",
                "capabilities": {
                    "cpu_cores": 8,
                    "memory_gb": 32.0,
                    "disk_gb": 500.0,
                    "gpu_count": 0
                },
                "task_count": 150,
                "error_count": 3
            }
        }


class WorkerTask(BaseModel):
    """Task execution information on a worker."""
    task_id: str = Field(..., description="Task ID")
    schedule_id: str = Field(..., description="Schedule ID")
    worker_id: str = Field(..., description="Worker ID executing the task")
    status: WorkerTaskStatus = Field(WorkerTaskStatus.PENDING, description="Task execution status")
    command: str = Field(..., description="Command to execute")
    working_directory: Optional[str] = Field(None, description="Working directory")
    environment: Dict[str, str] = Field(default_factory=dict, description="Environment variables")
    resources: Dict[str, Any] = Field(default_factory=dict, description="Resource requirements")
    started_at: Optional[datetime] = Field(None, description="When task started")
    completed_at: Optional[datetime] = Field(None, description="When task completed")
    exit_code: Optional[int] = Field(None, description="Process exit code")
    stdout: Optional[str] = Field(None, description="Standard output")
    stderr: Optional[str] = Field(None, description="Standard error")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    artifacts: List[Dict[str, Any]] = Field(default_factory=list, description="Output artifacts")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class WorkerResult(BaseModel):
    """Result of a task execution by a worker."""
    task_id: str = Field(..., description="Task ID")
    schedule_id: str = Field(..., description="Schedule ID")
    worker_id: str = Field(..., description="Worker ID")
    status: WorkerTaskStatus = Field(..., description="Final status")
    exit_code: Optional[int] = Field(None, description="Process exit code")
    stdout: Optional[str] = Field(None, description="Standard output")
    stderr: Optional[str] = Field(None, description="Standard error")
    error_message: Optional[str] = Field(None, description="Error message")
    artifacts: List[Dict[str, Any]] = Field(default_factory=list, description="Output artifacts")
    execution_time_ms: Optional[int] = Field(None, description="Execution time in milliseconds")
    started_at: Optional[datetime] = Field(None, description="When task started")
    completed_at: Optional[datetime] = Field(None, description="When task completed")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class WorkerHeartbeat(BaseModel):
    """Worker heartbeat information."""
    worker_id: str = Field(..., description="Worker ID")
    status: WorkerStatus = Field(..., description="Current status")
    current_task_id: Optional[str] = Field(None, description="Currently executing task")
    cpu_percent: Optional[float] = Field(None, description="CPU usage percentage")
    memory_percent: Optional[float] = Field(None, description="Memory usage percentage")
    disk_usage_gb: Optional[float] = Field(None, description="Disk usage in GB")
    network_io_bytes: Optional[Dict[str, int]] = Field(None, description="Network I/O statistics")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Heartbeat timestamp")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class WorkerStats(BaseModel):
    """Worker statistics."""
    total_workers: int = Field(0, description="Total number of workers")
    idle_workers: int = Field(0, description="Number of idle workers")
    busy_workers: int = Field(0, description="Number of busy workers")
    offline_workers: int = Field(0, description="Number of offline workers")
    error_workers: int = Field(0, description="Number of workers in error state")
    total_task_count: int = Field(0, description="Total completed tasks across all workers")
    total_error_count: int = Field(0, description="Total errors across all workers")
    average_cpu_percent: Optional[float] = Field(None, description="Average CPU usage")
    average_memory_percent: Optional[float] = Field(None, description="Average memory usage")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update time")


class WorkerFilter(BaseModel):
    """Filter options for worker queries."""
    worker_ids: Optional[List[str]] = Field(None, description="Filter by worker IDs")
    types: Optional[List[WorkerType]] = Field(None, description="Filter by worker type")
    statuses: Optional[List[WorkerStatus]] = Field(None, description="Filter by status")
    has_task: Optional[bool] = Field(None, description="Filter by whether worker has a task")
    capabilities: Optional[Dict[str, Any]] = Field(None, description="Filter by capabilities")
    labels: Optional[Dict[str, str]] = Field(None, description="Filter by labels")
    registered_after: Optional[datetime] = Field(None, description="Registered after this time")
    registered_before: Optional[datetime] = Field(None, description="Registered before this time")
    last_seen_within_seconds: Optional[int] = Field(None, description="Last seen within this many seconds")
