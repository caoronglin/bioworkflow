"""Execution database model."""

from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4
from sqlalchemy import (
    Column,
    String,
    Text,
    DateTime,
    JSON,
    ForeignKey,
    Enum,
)
from sqlalchemy.orm import relationship, Mapped
from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()


class ExecutionStatus(Enum):
    """Execution status enum."""

    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"
    cancelled = "cancelled"


class Execution(Base):
    """Workflow execution instance."""

    __tablename__ = "executions"

    id = Column(
        String,
        primary_key=True,
        default=lambda: str(uuid4()),
    )
    workflow_id = Column(
        String,
        ForeignKey("workflows.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    config = Column(JSON, nullable=True, default=dict)
    parameters = Column(JSON, nullable=True, default=dict)
    tags = Column(JSON, nullable=True, default=list)
    status = Column(
        Enum(ExecutionStatus),
        nullable=False,
        default=ExecutionStatus.pending,
    )
    created_at = Column(
        DateTime,
        default=datetime.now,
    )
    updated_at = Column(
        DateTime,
        default=datetime.now,
        onupdate=datetime.now,
    )

    # Relationships
    workflow: Mapped["Workflow"] = relationship(
        "Workflow",
        back_populates="executions",
    )
    task_executions: Mapped[List["TaskExecution"]] = relationship(
        "TaskExecution",
        back_populates="execution",
    )

    def __repr__(self):
        return f"<Execution {self.id}>"
