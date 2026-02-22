"""
Constants and configuration values used throughout the application.
"""

from typing import Dict, Any


# ID Prefixes for different entity types
ID_PREFIXES = {
    "pipeline": "pipe",
    "task": "task",
    "resource": "res",
    "schedule": "sched",
    "worker": "worker",
    "execution": "exec",
    "artifact": "art",
    "user": "user",
    "api_key": "key",
}


# Default timeout values (in seconds)
DEFAULT_TIMEOUTS = {
    "api_request": 30,
    "database_query": 60,
    "cache_operation": 5,
    "task_execution": 3600,
    "pipeline_execution": 86400,
    "worker_heartbeat": 30,
    "scheduler_poll": 10,
    "file_upload": 300,
    "file_download": 300,
}


# Maximum retry attempts
MAX_RETRIES = {
    "database": 3,
    "api_call": 3,
    "task_execution": 2,
    "worker_registration": 5,
    "scheduler_operation": 3,
    "file_operation": 3,
    "cache_operation": 2,
}


# Resource limits
RESOURCE_LIMITS = {
    "max_cpu_cores": 128,
    "max_memory_gb": 1024,
    "max_disk_gb": 10240,
    "max_gpu_count": 16,
    "max_concurrent_tasks": 1000,
    "max_pipeline_depth": 100,
    "max_task_dependencies": 50,
    "max_artifact_size_mb": 1024,
    "max_log_size_mb": 100,
}


# Validation patterns
VALID_NAME_PATTERN = r"^[a-zA-Z][a-zA-Z0-9_-]{1,63}$"
VALID_ID_PATTERN = r"^[a-z]+-[a-zA-Z0-9_-]{10,63}$"
VALID_EMAIL_PATTERN = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
VALID_URL_PATTERN = r"^https?://[^\s/$.?#].[^\s]*$"


# Date/Time formats
DATETIME_FORMAT_ISO = "%Y-%m-%dT%H:%M:%S.%fZ"
DATETIME_FORMAT_READABLE = "%Y-%m-%d %H:%M:%S"
DATE_FORMAT = "%Y-%m-%d"
TIME_FORMAT = "%H:%M:%S"


# HTTP status codes (subset used in the application)
HTTP_STATUS = {
    "OK": 200,
    "CREATED": 201,
    "ACCEPTED": 202,
    "NO_CONTENT": 204,
    "BAD_REQUEST": 400,
    "UNAUTHORIZED": 401,
    "FORBIDDEN": 403,
    "NOT_FOUND": 404,
    "CONFLICT": 409,
    "UNPROCESSABLE_ENTITY": 422,
    "TOO_MANY_REQUESTS": 429,
    "INTERNAL_SERVER_ERROR": 500,
    "NOT_IMPLEMENTED": 501,
    "BAD_GATEWAY": 502,
    "SERVICE_UNAVAILABLE": 503,
    "GATEWAY_TIMEOUT": 504,
}


# Log levels
LOG_LEVELS = {
    "DEBUG": "DEBUG",
    "INFO": "INFO",
    "WARNING": "WARNING",
    "ERROR": "ERROR",
    "CRITICAL": "CRITICAL",
}


# Cache TTLs (in seconds)
CACHE_TTLS = {
    "pipeline": 300,
    "task": 60,
    "resource": 600,
    "worker": 30,
    "schedule": 60,
    "user": 300,
    "api_key": 60,
}


# Pagination defaults
PAGINATION = {
    "default_page_size": 20,
    "max_page_size": 100,
    "min_page_size": 1,
}


# File upload limits
FILE_UPLOAD = {
    "max_file_size_mb": 1024,
    "allowed_extensions": [
        ".json",
        ".yaml",
        ".yml",
        ".toml",
        ".ini",
        ".conf",
        ".py",
        ".sh",
        ".bash",
        ".zsh",
        ".fish",
        ".snake",
        ".smk",
        ".workflow",
        ".txt",
        ".md",
        ".rst",
        ".csv",
        ".tsv",
        ".parquet",
        ".fasta",
        ".fastq",
        ".sam",
        ".bam",
        ".vcf",
        ".log",
    ],
    "blocked_extensions": [
        ".exe",
        ".dll",
        ".so",
        ".dylib",
        ".bin",
        ".zip",
        ".tar",
        ".gz",
        ".bz2",
        ".xz",
        ".7z",
        ".rar",
        ".iso",
        ".img",
    ],
}


# Environment variable prefixes
ENV_PREFIXES = {
    "app": "BIOFLOW_",
    "database": "DB_",
    "cache": "CACHE_",
    "queue": "QUEUE_",
    "storage": "STORAGE_",
    "auth": "AUTH_",
    "log": "LOG_",
    "metrics": "METRICS_",
}
