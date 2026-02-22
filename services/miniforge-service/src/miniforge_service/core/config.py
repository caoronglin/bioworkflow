"""Configuration for Miniforge Service."""

import os
from functools import lru_cache
from pathlib import Path
from typing import List, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Service info
    service_name: str = Field(default="miniforge-service", description="Service name")
    service_version: str = Field(default="0.1.0-alpha.1", description="Service version")
    environment: str = Field(default="development", description="Environment (development/staging/production)")

    # Server settings
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8001, ge=1, le=65535, description="Server port")
    workers: int = Field(default=1, ge=1, description="Number of worker processes")
    debug: bool = Field(default=False, description="Debug mode")
    log_level: str = Field(default="info", description="Log level")

    # CORS settings
    cors_origins: List[str] = Field(default=["*"], description="Allowed CORS origins")

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse CORS origins from string or list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    # Miniforge settings
    miniforge_root: Optional[Path] = Field(default=None, description="Miniforge installation root")
    envs_dir: Optional[Path] = Field(default=None, description="Directory for environments")

    @field_validator("miniforge_root", mode="before")
    @classmethod
    def validate_miniforge_root(cls, v):
        """Validate miniforge root path."""
        if v is None:
            return None
        path = Path(v).expanduser().resolve()
        return path

    # Feature flags
    metrics_enabled: bool = Field(default=True, description="Enable Prometheus metrics")
    tracing_enabled: bool = Field(default=False, description="Enable OpenTelemetry tracing")

    # OpenTelemetry settings
    otel_enabled: bool = Field(default=False, description="Enable OpenTelemetry")
    otel_endpoint: Optional[str] = Field(default=None, description="OTLP endpoint")
    otel_service_name: str = Field(default="miniforge-service", description="Service name for tracing")

    # Security settings
    api_key: Optional[str] = Field(default=None, description="API key for authentication")
    max_env_size_gb: int = Field(default=100, ge=1, description="Maximum environment size in GB")
    max_environments: int = Field(default=50, ge=1, description="Maximum number of environments")

    # Cache settings
    cache_ttl: int = Field(default=300, description="Cache TTL in seconds")


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
