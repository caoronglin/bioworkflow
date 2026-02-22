"""Task database model."""

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
)
from sqlalchemy.orm import relationship, Mapped
from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()


class Task(Base):
    """Individual task in a workflow."""

    __tablename__ = "tasks"

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
    name = Column(String(255), nullable=False, index=True)
    command = Column(Text, nullable=False)
    inputs = Column(JSON, nullable=True, default=list)
    outputs = Column(JSON, nullable=True, default=list)
    dependencies = relationship(
        "Task",
        secondary="task_dependencies",
        primaryjoin="Task.id == task_dependencies.c.source_id",
        secondaryjoin="Task.id == task_dependencies.c.target_id",
        backref="dependents",
        lazy="selectin",
    )
    resources = Column(JSON, nullable=True, default=dict)
    container = Column(String(500), nullable=True)
    environment = Column(String(255), nullable=True)
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
        back_populates="tasks",
    )
    task_executions: Mapped[List["TaskExecution"]] = relationship(
        "TaskExecution",
        back_populates="task",
    )

    def __repr__(self):
        return f"<Task {self.name}>"
