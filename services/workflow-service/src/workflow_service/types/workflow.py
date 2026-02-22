"""Workflow type definitions."""

from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field, validator


class WorkflowBase(BaseModel):
    """Base workflow schema."""

    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    format: str = "snakemake"
    config: Optional[Dict[str, Any]] = None

    @validator("format")
    def validate_format(cls, v: str) -> str:
        """Validate workflow format."""
        valid_formats = ["snakemake", "yaml"]
        if v.lower() not in valid_formats:
            raise ValueError(
                f"Invalid format: '{v}'. Valid options: {', '.join(valid_formats)}"
            )
        return v.lower()

    class Config:
        orm_mode = True


class WorkflowCreate(BaseModel):
    """Workflow creation schema."""

    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    format: str = "snakemake"
    content: Optional[str] = None
    snakefile_path: Optional[str] = None
    config: Optional[Dict[str, Any]] = None

    @validator("content", "snakefile_path")
    def validate_source(cls, v, values, **kwargs):
        """At least one source must be provided."""
        if "content" not in values or not values["content"]:
            if "snakefile_path" not in values or not values["snakefile_path"]:
                raise ValueError("Either content or snakefile_path must be provided")
        return v

    class Config:
        orm_mode = True


class WorkflowUpdate(BaseModel):
    """Workflow update schema."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    config: Optional[Dict[str, Any]] = None

    class Config:
        orm_mode = True


class Workflow(WorkflowBase):
    """Complete workflow schema."""

    id: UUID
    content: str
    snakefile_path: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class WorkflowList(BaseModel):
    """Workflow list response."""

    items: List[Workflow]
    total: int
    offset: int
    limit: int
