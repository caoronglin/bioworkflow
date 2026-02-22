"""Pydantic models for Miniforge Service."""

from __future__ import annotations

import re
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class PackageChannel(str, Enum):
    """Supported Conda channels."""

    CONDA_FORGE = "conda-forge"
    BIOCUNDA = "bioconda"
    DEFAULTS = "defaults"
    PYTORCH = "pytorch"
    NVIDIA = "nvidia"
    CUSTOM = "custom"


class EnvironmentStatus(str, Enum):
    """Environment status."""

    CREATING = "creating"
    ACTIVE = "active"
    INACTIVE = "inactive"
    UPDATING = "updating"
    DELETING = "deleting"
    ERROR = "error"


class Package(BaseModel):
    """Package information."""

    model_config = ConfigDict(frozen=True)

    name: str = Field(..., description="Package name")
    version: Optional[str] = Field(None, description="Installed version")
    channel: Optional[PackageChannel] = Field(None, description="Package channel")
    build: Optional[str] = Field(None, description="Build string")
    size: Optional[int] = Field(None, description="Package size in bytes")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate package name."""
        if not re.match(r"^[a-zA-Z0-9_][a-zA-Z0-9._-]*$", v):
            raise ValueError(f"Invalid package name: {v}")
        return v.lower()


class PackageInstall(BaseModel):
    """Package installation request."""

    name: str = Field(..., description="Package name")
    version: Optional[str] = Field(None, description="Version specification")
    channel: Optional[PackageChannel] = Field(
        default=PackageChannel.CONDA_FORGE,
        description="Package channel"
    )
    build: Optional[str] = Field(None, description="Build specification")


class EnvironmentBase(BaseModel):
    """Base environment model."""

    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Environment name"
    )
    description: Optional[str] = Field(
        None,
        max_length=500,
        description="Environment description"
    )
    python_version: Optional[str] = Field(
        None,
        pattern=r"^3\.(8|9|10|11|12)$",
        description="Python version (e.g., 3.11)"
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate environment name."""
        if not re.match(r"^[a-zA-Z0-9_-]+$", v):
            raise ValueError(
                "Environment name must contain only letters, numbers, hyphens, and underscores"
            )
        return v


class EnvironmentCreate(EnvironmentBase):
    """Environment creation request."""

    packages: List[PackageInstall] = Field(
        default_factory=list,
        description="Packages to install"
    )
    channels: List[PackageChannel] = Field(
        default_factory=lambda: [PackageChannel.CONDA_FORGE, PackageChannel.BIOCUNDA],
        description="Conda channels"
    )
    environment_file: Optional[Path] = Field(
        None,
        description="Environment YAML file path"
    )

    @model_validator(mode="after")
    def validate_packages_or_file(self) -> "EnvironmentCreate":
        """Validate that either packages or environment file is provided."""
        if not self.packages and not self.environment_file:
            # Allow empty packages for basic Python environment
            pass
        return self


class EnvironmentUpdate(BaseModel):
    """Environment update request."""

    description: Optional[str] = Field(None, description="Updated description")
    add_packages: List[PackageInstall] = Field(
        default_factory=list,
        description="Packages to add"
    )
    remove_packages: List[str] = Field(
        default_factory=list,
        description="Packages to remove"
    )
    update_packages: List[str] = Field(
        default_factory=list,
        description="Packages to update"
    )


class Environment(EnvironmentBase):
    """Complete environment information."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="Unique environment ID")
    path: Path = Field(..., description="Environment directory path")
    status: EnvironmentStatus = Field(..., description="Current status")
    packages: List[Package] = Field(
        default_factory=list,
        description="Installed packages"
    )
    channels: List[PackageChannel] = Field(
        default_factory=list,
        description="Configured channels"
    )
    size_bytes: Optional[int] = Field(
        None,
        description="Total environment size in bytes"
    )
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    created_by: Optional[str] = Field(
        None,
        description="User who created the environment"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata"
    )


class EnvironmentList(BaseModel):
    """List of environments response."""

    environments: List[Environment] = Field(..., description="Environments")
    total: int = Field(..., description="Total count")
    page: int = Field(1, description="Current page")
    page_size: int = Field(20, description="Page size")


class EnvironmentCloneRequest(BaseModel):
    """Environment clone request."""

    new_name: str = Field(..., description="Name for the cloned environment")
    description: Optional[str] = Field(None, description="Description for clone")

    @field_validator("new_name")
    @classmethod
    def validate_new_name(cls, v: str) -> str:
        """Validate new environment name."""
        if not re.match(r"^[a-zA-Z0-9_-]+$", v):
            raise ValueError(
                "Environment name must contain only letters, numbers, hyphens, and underscores"
            )
        return v


class EnvironmentExportRequest(BaseModel):
    """Environment export request."""

    format: ExportFormat = Field(
        default=ExportFormat.YAML,
        description="Export format"
    )
    include_builds: bool = Field(
        default=False,
        description="Include build strings"
    )
    from_history: bool = Field(
        default=False,
        description="Export only explicitly installed packages"
    )


class ExportFormat(str, Enum):
    """Environment export format."""

    YAML = "yaml"
    JSON = "json"
    REQUIREMENTS = "requirements"


class PackageSearchResult(BaseModel):
    """Package search result."""

    packages: List[Package] = Field(..., description="Matching packages")
    total: int = Field(..., description="Total matches")
    query: str = Field(..., description="Search query")
    channel: Optional[PackageChannel] = Field(None, description="Channel searched")


class SystemInfo(BaseModel):
    """System information."""

    platform: str = Field(..., description="Operating system")
    architecture: str = Field(..., description="CPU architecture")
    miniforge_version: str = Field(..., description="Miniforge version")
    conda_version: str = Field(..., description="Conda version")
    mamba_version: str = Field(..., description="Mamba version")
    base_prefix: Path = Field(..., description="Base environment path")
    envs_dirs: List[Path] = Field(..., description="Environment directories")
    pkgs_dirs: List[Path] = Field(..., description="Package cache directories")
