"""Task type definitions."""

from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field
from enum import Enum


class ResourceRequirements(BaseModel):
    """Resource requirements for a task."""

    cpu: Optional[float] = Field(None, ge=0.1, le=16.0)
    memory: Optional[int] = Field(None, ge=128, le=32 * 1024)
    gpu: Optional[int] = Field(None, ge=0, le=8)
    disk: Optional[int] = Field(None, ge=0)
    tmpdir: Optional[int] = Field(None, ge=0)
    custom: Optional[Dict[str, Any]] = None

    class Config:
        orm_mode = True


class TaskStatus(str, Enum):
    """Task execution status."""

    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"
    cancelled = "cancelled"


class TaskBase(BaseModel):
    """Base task schema."""

    name: str = Field(..., min_length=1, max_length=255)
    command: str
    inputs: List[str] = Field(default_factory=list)
    outputs: List[str] = Field(default_factory=list)
    resources: ResourceRequirements = Field(default_factory=ResourceRequirements)
    container: Optional[str] = None
    environment: Optional[str] = None

    class Config:
        orm_mode = True


class TaskCreate(BaseModel):
    """Task creation schema."""

    name: str = Field(..., min_length=1, max_length=255)
    command: str
    inputs: List[str] = Field(default_factory=list)
    outputs: List[str] = Field(default_factory=list)
    dependencies: List[UUID] = Field(default_factory=list)
    resources: ResourceRequirements = Field(default_factory=ResourceRequirements)
    container: Optional[str] = None
    environment: Optional[str] = None

    class Config:
        orm_mode = True


class TaskUpdate(BaseModel):
    """Task update schema."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    command: Optional[str] = None
    resources: Optional[ResourceRequirements] = None
    container: Optional[str] = None
    environment: Optional[str] = None

    class Config:
        orm_mode = True


class Task(BaseModel):
    """Complete task schema."""

    id: UUID
    workflow_id: UUID
    name: str
    command: str
    inputs: List[str]
    outputs: List[str]
    resources: ResourceRequirements
    container: Optional[str]
    environment: Optional[str]
    dependencies: List["Task"]
    status: TaskStatus = TaskStatus.pending
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class TaskExecution(BaseModel):
    """Task execution details."""

    id: UUID
    task_id: UUID
    start_time: Optional[datetime]
    end_time: Optional[datetime]
    duration: Optional[int]
    status: TaskStatus = TaskStatus.pending
    exit_code: Optional[int]
    stdout: Optional[str] = None
    stderr: Optional[str] = None

    class Config:
        orm_mode = True
