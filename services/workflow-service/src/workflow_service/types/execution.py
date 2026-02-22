"""Workflow execution type definitions."""

from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field
from enum import Enum


class ExecutionStatus(str, Enum):
    """Workflow execution status."""

    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"
    cancelled = "cancelled"


class ExecutionCreate(BaseModel):
    """Execution creation schema."""

    config: Optional[Dict[str, Any]] = None
    parameters: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None

    class Config:
        orm_mode = True


class ExecutionUpdate(BaseModel):
    """Execution update schema."""

    status: Optional[ExecutionStatus] = None
    config: Optional[Dict[str, Any]] = None

    class Config:
        orm_mode = True


class Execution(BaseModel):
    """Complete execution schema."""

    id: UUID
    workflow_id: UUID
    config: Dict[str, Any] = Field(default_factory=dict)
    parameters: Dict[str, Any] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)
    status: ExecutionStatus = ExecutionStatus.pending
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class ExecutionDetail(BaseModel):
    """Detailed execution information."""

    id: UUID
    workflow_id: UUID
    config: Dict[str, Any] = Field(default_factory=dict)
    parameters: Dict[str, Any] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)
    status: ExecutionStatus = ExecutionStatus.pending
    created_at: datetime
    updated_at: datetime
    task_executions: List["TaskExecution"] = Field(default_factory=list)


class ExecutionList(BaseModel):
    """Execution list response."""

    items: List[Execution]
    total: int
    offset: int
    limit: int
