"""Workflow database model."""

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


class Workflow(Base):
    """Workflow definition in the database."""

    __tablename__ = "workflows"

    id = Column(
        String,
        primary_key=True,
        default=lambda: str(uuid4()),
    )
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    format = Column(String(50), nullable=False, default="snakemake")
    content = Column(Text, nullable=False)
    snakefile_path = Column(String(500), nullable=True)
    config = Column(JSON, nullable=True, default=dict)
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
    tasks: Mapped[List["Task"]] = relationship(
        "Task",
        back_populates="workflow",
        lazy="selectin",
    )
    executions: Mapped[List["Execution"]] = relationship(
        "Execution",
        back_populates="workflow",
        lazy="selectin",
    )

    def __repr__(self):
        return f"<Workflow {self.name}>"
