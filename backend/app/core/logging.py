"""
AdTicks — Structured logging configuration.

Provides:
- JSON structured logging for production
- Request ID tracking across services
- Error context capture
- Request ID propagation to Celery tasks and external calls
"""

import json
import logging
import sys
import uuid
from contextlib import contextmanager
from contextvars import ContextVar, copy_context
from typing import Generator

# Context variable for request tracking
request_id_context: ContextVar[str | None] = ContextVar("request_id", default=None)


class JSONFormatter(logging.Formatter):
    """Format logs as JSON for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        """Convert log record to JSON."""
        log_data = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": request_id_context.get(),
        }

        # Add extra fields
        if hasattr(record, "extra_fields"):
            log_data.update(record.extra_fields)

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data)


def setup_logging(environment: str = "development"):
    """Configure logging for the application."""
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Choose formatter based on environment
    if environment == "production":
        formatter = JSONFormatter()
    else:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # Suppress verbose third-party logs
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("fastapi").setLevel(logging.INFO)


def get_logger(name: str) -> logging.LoggerAdapter:
    """Get a logger with context support."""
    logger = logging.getLogger(name)

    class ContextLoggerAdapter(logging.LoggerAdapter):
        """Add context info to logs."""

        def process(self, msg: str, kwargs: dict) -> tuple[str, dict]:
            """Add extra fields to log record."""
            extra = kwargs.get("extra", {})
            if "request_id" not in extra:
                extra["request_id"] = request_id_context.get()
            kwargs["extra"] = {"extra_fields": extra}
            return msg, kwargs

    return ContextLoggerAdapter(logger, {})


def set_request_id(request_id: str | None = None) -> str:
    """Set the current request ID for context tracking."""
    if request_id is None:
        request_id = str(uuid.uuid4())
    request_id_context.set(request_id)
    return request_id


def get_request_id() -> str | None:
    """Get the current request ID from context."""
    return request_id_context.get()


def set_request_id_for_task(request_id: str | None) -> None:
    """Set request ID for Celery task execution.
    
    Call this in Celery task signal handlers to propagate the request ID
    from the HTTP context to the task context.
    """
    if request_id:
        request_id_context.set(request_id)


@contextmanager
def with_request_id(request_id: str | None) -> Generator[None, None, None]:
    """Context manager to temporarily set a request ID.
    
    Useful for executing code in a specific request context.
    Restores the previous request ID when exiting.
    
    Example:
        with with_request_id("req-123"):
            logger.info("message")  # Will have request_id="req-123"
    """
    token = request_id_context.set(request_id)
    try:
        yield
    finally:
        request_id_context.reset(token)


def get_context_with_request_id(request_id: str | None) -> dict:
    """Get a copy of the current context with a specific request ID.
    
    Useful for passing to Celery tasks to preserve context.
    """
    ctx = copy_context()
    ctx.run(request_id_context.set, request_id)
    return {"context": ctx, "request_id": request_id}
