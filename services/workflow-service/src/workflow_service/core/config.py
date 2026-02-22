"""Configuration for workflow service."""

from typing import Optional, List, Dict, Any
from pydantic import BaseSettings, validator
import os


class Settings(BaseSettings):
    """Application settings."""

    # Service configuration
    SERVICE_NAME: str = "workflow-service"
    SERVICE_VERSION: str = "0.1.0"
    LOG_LEVEL: str = "INFO"

    # Server configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8001
    WORKERS: int = 1

    # Database configuration
    DATABASE_URL: str = "sqlite:///workflow.db"
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 0

    # Workflow configuration
    WORKFLOW_BASE_DIR: str = "workflows"
    WORKFLOW_QUEUE_SIZE: int = 100
    WORKFLOW_EXECUTION_TIMEOUT: int = 3600
    WORKFLOW_MAX_RETRIES: int = 3

    # Resource management
    SCHEDULER_CONCURRENCY: int = 2
    RESOURCE_TOTAL_CPU: float = 8.0
    RESOURCE_TOTAL_MEMORY: int = 16 * 1024 * 1024  # 16GB
    RESOURCE_TOTAL_GPU: int = 0

    # Scheduling configuration
    SCHEDULING_STRATEGY: str = "fifo"
    SCHEDULER_QUEUE_SIZE: int = 100
    SCHEDULER_PREFETCH: int = 1
    SCHEDULER_RETRY_DELAY: int = 5

    # Visualization configuration
    VISUALIZATION_ENABLED: bool = True
    VISUALIZATION_FORMATS: List[str] = ["dot", "mermaid"]

    # Monitoring configuration
    MONITORING_ENABLED: bool = True
    METRICS_PORT: int = 8002

    # Environment variables prefix for easy configuration
    class Config:
        env_prefix = "WORKFLOW_"
        case_sensitive = True

    @validator("SCHEDULING_STRATEGY")
    def validate_strategy(cls, v: str) -> str:
        """Validate scheduling strategy."""
        valid_strategies = ["fifo", "sjf", "priority", "least_load", "resource_aware"]
        if v.lower() not in valid_strategies:
            raise ValueError(
                f"Invalid scheduling strategy: '{v}'. "
                f"Valid options: {', '.join(valid_strategies)}"
            )
        return v.lower()

    @validator("VISUALIZATION_FORMATS")
    def validate_visualization_formats(cls, v: List[str]) -> List[str]:
        """Validate visualization formats."""
        valid_formats = ["dot", "mermaid", "json", "html", "png"]
        invalid = [f for f in v if f.lower() not in valid_formats]
        if invalid:
            raise ValueError(
                f"Invalid visualization formats: {', '.join(invalid)}. "
                f"Valid options: {', '.join(valid_formats)}"
            )
        return [f.lower() for f in v]

    @validator("WORKFLOW_BASE_DIR")
    def validate_workflow_dir(cls, v: str) -> str:
        """Ensure workflow directory exists."""
        if not os.path.exists(v):
            os.makedirs(v, exist_ok=True)
        return v


_settings = None


def get_settings() -> Settings:
    """Get settings instance with caching."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
