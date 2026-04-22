"""
AdTicks — Custom exception classes.

Defines application-specific exceptions with proper error codes and HTTP status codes.
"""

from typing import Any, Optional


class AdTicksException(Exception):
    """Base exception for AdTicks application."""

    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = 500,
        details: Optional[dict[str, Any]] = None,
    ):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)


class ValidationError(AdTicksException):
    """Raised when input validation fails."""

    def __init__(self, message: str, details: Optional[dict[str, Any]] = None):
        super().__init__(
            code="VALIDATION_ERROR",
            message=message,
            status_code=422,
            details=details,
        )


class AuthenticationError(AdTicksException):
    """Raised when authentication fails."""

    def __init__(self, message: str = "Authentication failed"):
        super().__init__(
            code="AUTHENTICATION_ERROR",
            message=message,
            status_code=401,
        )


class AuthorizationError(AdTicksException):
    """Raised when user lacks permission."""

    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(
            code="AUTHORIZATION_ERROR",
            message=message,
            status_code=403,
        )


class NotFoundError(AdTicksException):
    """Raised when resource is not found."""

    def __init__(self, resource: str, identifier: str = ""):
        message = f"{resource} not found"
        if identifier:
            message += f": {identifier}"
        super().__init__(
            code="NOT_FOUND",
            message=message,
            status_code=404,
        )


class ConflictError(AdTicksException):
    """Raised when resource already exists."""

    def __init__(self, message: str):
        super().__init__(
            code="CONFLICT",
            message=message,
            status_code=409,
        )


class RateLimitError(AdTicksException):
    """Raised when rate limit is exceeded."""

    def __init__(self, message: str = "Too many requests"):
        super().__init__(
            code="RATE_LIMIT_EXCEEDED",
            message=message,
            status_code=429,
        )


class ExternalServiceError(AdTicksException):
    """Raised when external service (API, LLM) fails."""

    def __init__(self, service: str, message: str):
        super().__init__(
            code="EXTERNAL_SERVICE_ERROR",
            message=f"{service} error: {message}",
            status_code=502,
        )


class TaskError(AdTicksException):
    """Raised when async task fails."""

    def __init__(self, task_name: str, message: str):
        super().__init__(
            code="TASK_ERROR",
            message=f"Task '{task_name}' failed: {message}",
            status_code=500,
        )
