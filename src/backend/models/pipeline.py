"""流水线和执行模型"""

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import JSON, DateTime, Enum as SQLEnum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .user import User


class PipelineStatus(str, Enum):
    """流水线状态"""
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    ARCHIVED = "archived"
    ERROR = "error"


class ExecutionStatus(str, Enum):
    """执行状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class Pipeline(Base):
    """流水线模型"""

    __tablename__ = "pipelines"

    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Snakemake 相关
    snakefile_path: Mapped[str] = mapped_column(String(500), nullable=False)
    conda_environment: Mapped[str | None] = mapped_column(String(100), nullable=True)
    workdir: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # 参数配置
    parameters: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # 状态
    status: Mapped[PipelineStatus] = mapped_column(
        SQLEnum(PipelineStatus),
        default=PipelineStatus.DRAFT,
        nullable=False,
    )
    version: Mapped[int] = mapped_column(default=1, nullable=False)

    # 所有权
    owner_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    owner: Mapped["User"] = relationship("User", backref="pipelines")

    # 统计
    total_executions: Mapped[int] = mapped_column(default=0, nullable=False)
    last_execution_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "snakefile_path": self.snakefile_path,
            "conda_environment": self.conda_environment,
            "workdir": self.workdir,
            "parameters": self.parameters,
            "status": self.status.value,
            "version": self.version,
            "owner_id": self.owner_id,
            "total_executions": self.total_executions,
            "last_execution_at": self.last_execution_at.isoformat() if self.last_execution_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class PipelineExecution(Base):
    """流水线执行记录"""

    __tablename__ = "pipeline_executions"

    pipeline_id: Mapped[str] = mapped_column(ForeignKey("pipelines.id"), nullable=False)
    pipeline: Mapped["Pipeline"] = relationship("Pipeline", backref="executions")

    # 执行配置
    parameters: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # 状态
    status: Mapped[ExecutionStatus] = mapped_column(
        SQLEnum(ExecutionStatus),
        default=ExecutionStatus.PENDING,
        nullable=False,
    )

    # 时间戳
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # 执行结果
    output_dir: Mapped[str | None] = mapped_column(String(500), nullable=True)
    log_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # 资源使用统计
    cpu_time_seconds: Mapped[float | None] = mapped_column(nullable=True)
    memory_peak_mb: Mapped[float | None] = mapped_column(nullable=True)
    disk_read_mb: Mapped[float | None] = mapped_column(nullable=True)
    disk_write_mb: Mapped[float | None] = mapped_column(nullable=True)

    # 触发者
    triggered_by: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    user: Mapped["User"] = relationship("User", backref="executions")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "pipeline_id": self.pipeline_id,
            "parameters": self.parameters,
            "status": self.status.value,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "output_dir": self.output_dir,
            "log_path": self.log_path,
            "error_message": self.error_message,
            "triggered_by": self.triggered_by,
        }
