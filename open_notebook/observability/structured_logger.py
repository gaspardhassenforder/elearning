"""
Structured logging with JSON formatter for production environments.

This module configures loguru to output structured JSON logs in production
while maintaining human-readable logs in development. Integrates with
request context to include correlation IDs and context buffers in logs.
"""

import json
import os
import sys
from typing import Any, Dict

from loguru import logger

from open_notebook.observability.request_context import context_buffer, get_request_context

# Determine environment
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
STRUCTURED_LOGGING = os.getenv("STRUCTURED_LOGGING", "false").lower() == "true"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO" if ENVIRONMENT == "production" else "DEBUG")


def json_formatter(record: Dict[str, Any]) -> str:
    """
    Format log record as JSON for production.

    Args:
        record: Loguru record dictionary containing log details

    Returns:
        JSON-formatted log entry with newline

    Note:
        Includes request context (request_id, user_id, company_id, endpoint)
        and context buffer for ERROR level logs.
    """
    # Base log entry
    log_entry = {
        "timestamp": record["time"].isoformat(),
        "level": record["level"].name,
        "message": record["message"],
        "module": record["name"],
        "function": record["function"],
        "line": record["line"],
    }

    # Add request context if available
    ctx = get_request_context()
    if ctx:
        log_entry.update(ctx)

    # Add exception info if present
    if record["exception"]:
        exc_type, exc_value, exc_tb = record["exception"]
        log_entry["error_type"] = exc_type.__name__ if exc_type else None
        log_entry["error_message"] = str(exc_value) if exc_value else None
        # Format stack trace
        if exc_tb:
            import traceback

            log_entry["stack_trace"] = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))

    # Add context buffer for ERROR level logs
    if record["level"].name == "ERROR":
        buffer = context_buffer.get()
        if buffer is not None:
            log_entry["context_buffer"] = buffer.peek()

    # Add any extra fields from record["extra"]
    if record["extra"]:
        # Merge extra fields, but don't overwrite base fields
        for key, value in record["extra"].items():
            if key not in log_entry:
                # Serialize non-primitive types
                if isinstance(value, (str, int, float, bool, type(None))):
                    log_entry[key] = value
                elif isinstance(value, (list, dict)):
                    log_entry[key] = value
                else:
                    log_entry[key] = str(value)

    # Add metadata
    log_entry["metadata"] = {
        "environment": ENVIRONMENT,
        "process_id": record["process"].id,
        "thread_id": record["thread"].id,
    }

    return json.dumps(log_entry, default=str) + "\n"


def human_readable_formatter(record: Dict[str, Any]) -> str:
    """
    Format log record as human-readable colored output for development.

    Args:
        record: Loguru record dictionary

    Returns:
        Formatted string with colors and context

    Note:
        Includes request_id if available for correlation.
    """
    # Get request context for request_id
    ctx = get_request_context()
    request_id = ctx.get("request_id", "no-request") if ctx else "no-request"

    # Build format string with colors
    time_str = "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green>"
    level_str = "<level>{level: <8}</level>"
    request_id_str = f"<cyan>{request_id[:8]}</cyan>"
    location_str = "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan>"
    message_str = "<level>{message}</level>"

    format_str = f"{time_str} | {level_str} | {request_id_str} | {location_str} - {message_str}"

    return format_str


def configure_logging():
    """
    Configure loguru logging based on environment.

    - Production: JSON structured logs to stderr
    - Development: Human-readable colored logs to stderr

    Note:
        Called automatically on module import or can be called manually
        to reconfigure logging.
    """
    # Remove default handler
    logger.remove()

    if STRUCTURED_LOGGING or ENVIRONMENT == "production":
        # Production: JSON structured logging
        logger.add(
            sys.stderr,
            format=json_formatter,
            level=LOG_LEVEL,
            serialize=False,  # We handle serialization in json_formatter
            backtrace=True,
            diagnose=False,  # Don't include variable values in production
        )
    else:
        # Development: Human-readable logging
        logger.add(
            sys.stderr,
            format=human_readable_formatter,
            level=LOG_LEVEL,
            colorize=True,
            backtrace=True,
            diagnose=True,  # Include variable values for debugging
        )

    logger.debug(f"Logging configured: environment={ENVIRONMENT}, level={LOG_LEVEL}, structured={STRUCTURED_LOGGING}")


def structured_log(level: str, message: str, **extra):
    """
    Log a message with structured context.

    Args:
        level: Log level (debug, info, warning, error, critical)
        message: Log message
        **extra: Additional fields to include in log entry

    Example:
        >>> structured_log("info", "User login successful",
        ...                user_id="user:123", ip_address="192.168.1.1")
    """
    log_func = getattr(logger, level.lower())
    log_func(message, **extra)


# Auto-configure on import
configure_logging()
