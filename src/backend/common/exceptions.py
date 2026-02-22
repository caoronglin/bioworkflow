"""
Custom exception classes for the application.
"""

from typing import Any, Dict, Optional


class BioflowError(Exception):
    """Base exception for all application errors."""

    def __init__(
        self,
        message: str,
        code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        status_code: int = 500,
    ):
        super().__init__(message)
        self.message = message
        self.code = code or "INTERNAL_ERROR"
        self.details = details or {}
        self.status_code = status_code

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary."""
        return {
            "error": {
                "code": self.code,
                "message": self.message,
                "details": self.details,
            }
        }


class ValidationError(BioflowError):
    """Raised when input validation fails."""

    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            details={"field": field, **(details or {})},
            status_code=400,
        )


class NotFoundError(BioflowError):
    """Raised when a requested resource is not found."""

    def __init__(
        self,
        resource_type: str,
        resource_id: str,
        message: Optional[str] = None,
    ):
        msg = message or f"{resource_type} with ID '{resource_id}' not found"
        super().__init__(
            message=msg,
            code="NOT_FOUND",
            details={"resource_type": resource_type, "resource_id": resource_id},
            status_code=404,
        )


class ConflictError(BioflowError):
    """Raised when there's a conflict with the current state."""

    def __init__(
        self,
        message: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
    ):
        super().__init__(
            message=message,
            code="CONFLICT",
            details={
                "resource_type": resource_type,
                "resource_id": resource_id,
            },
            status_code=409,
        )


class AuthenticationError(BioflowError):
    """Raised when authentication fails."""

    def __init__(self, message: str = "Authentication failed"):
        super().__init__(
            message=message,
            code="AUTHENTICATION_ERROR",
            status_code=401,
        )


class AuthorizationError(BioflowError):
    """Raised when user is not authorized to perform an action."""

    def __init__(
        self,
        message: str = "Not authorized",
        required_permission: Optional[str] = None,
    ):
        super().__init__(
            message=message,
            code="AUTHORIZATION_ERROR",
            details={"required_permission": required_permission},
            status_code=403,
        )


class ServiceError(BioflowError):
    """Raised when a service operation fails."""

    def __init__(
        self,
        service_name: str,
        message: str,
        cause: Optional[Exception] = None,
    ):
        details = {"service_name": service_name}
        if cause:
            details["cause"] = str(cause)

        super().__init__(
            message=message,
            code="SERVICE_ERROR",
            details=details,
            status_code=503,
        )


class SchedulerError(ServiceError):
    """Raised when scheduler operation fails."""

    def __init__(self, message: str, cause: Optional[Exception] = None):
        super().__init__(
            service_name="scheduler",
            message=message,
            cause=cause,
        )
        self.code = "SCHEDULER_ERROR"


class WorkerError(ServiceError):
    """Raised when worker operation fails."""

    def __init__(self, message: str, cause: Optional[Exception] = None):
        super().__init__(
            service_name="worker",
            message=message,
            cause=cause,
        )
        self.code = "WORKER_ERROR"


class ExecutionError(BioflowError):
    """Raised when task execution fails."""

    def __init__(
        self,
        task_id: str,
        message: str,
        exit_code: Optional[int] = None,
        stderr: Optional[str] = None,
    ):
        super().__init__(
            message=message,
            code="EXECUTION_ERROR",
            details={
                "task_id": task_id,
                "exit_code": exit_code,
                "stderr": stderr,
            },
            status_code=500,
        )


class TimeoutError(BioflowError):
    """Raised when an operation times out."""

    def __init__(
        self,
        operation: str,
        timeout_seconds: float,
        message: Optional[str] = None,
    ):
        msg = message or f"Operation '{operation}' timed out after {timeout_seconds}s"
        super().__init__(
            message=msg,
            code="TIMEOUT_ERROR",
            details={
                "operation": operation,
                "timeout_seconds": timeout_seconds,
            },
            status_code=504,
        )
