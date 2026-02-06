"""
Request context tracking using Python contextvars.

This module provides thread-safe context variables for tracking request metadata
and operation history across async boundaries. Uses Python's built-in contextvars
which automatically propagate across await boundaries and provide isolation
between concurrent requests.
"""

import contextvars
import time
from datetime import UTC, datetime
from typing import Any, Dict, Optional

from open_notebook.observability.context_buffer import RollingContextBuffer

# Context variable for request metadata (thread-safe for async)
request_context: contextvars.ContextVar[Optional[Dict[str, Any]]] = contextvars.ContextVar(
    "request_context", default=None
)

# Context variable for rolling buffer (thread-safe for async)
context_buffer: contextvars.ContextVar[Optional[RollingContextBuffer]] = contextvars.ContextVar(
    "context_buffer", default=None
)


def get_request_context() -> Dict[str, Any]:
    """
    Get current request context (safe across async boundaries).

    Returns:
        Dictionary containing request metadata (request_id, user_id,
        company_id, endpoint, timestamp) or empty dict if no context set.

    Note:
        This function is safe to call from any async context and will
        return the context for the current request, even across await
        boundaries.
    """
    ctx = request_context.get()
    return ctx if ctx else {}


def log_operation(
    operation_type: str,
    details: Dict[str, Any],
    duration_ms: Optional[float] = None,
):
    """
    Append operation to rolling buffer.

    Args:
        operation_type: Type of operation (db_query, ai_call, tool_invoke,
                       service_call, graph_chain_start, etc.)
        details: Dictionary of operation-specific details
        duration_ms: Optional operation duration in milliseconds

    Note:
        If no context buffer is set (e.g., outside a request), this is a no-op.
        Operations are automatically timestamped and added to the rolling buffer.

    Example:
        >>> log_operation("db_query", {
        ...     "query": "SELECT * FROM source WHERE notebook = $notebook",
        ...     "params": {"notebook": "notebook:abc"},
        ...     "result_count": 5
        ... }, duration_ms=45.2)
    """
    buffer = context_buffer.get()
    if buffer is not None:
        buffer.append(
            {
                "type": operation_type,
                "details": sanitize_details(details),
                "timestamp": datetime.now(UTC).isoformat(),
                "duration_ms": duration_ms,
            }
        )


def sanitize_details(details: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sanitize operation details to prevent logging sensitive data.

    Args:
        details: Raw operation details

    Returns:
        Sanitized details with truncated strings and removed credentials

    Note:
        - Truncates strings to 200 characters
        - Removes keys containing 'password', 'token', 'secret', 'key'
        - Replaces non-serializable types with type name
    """
    sanitized = {}

    # Exact match keywords (e.g., "password", "token" but not "tokens")
    exact_sensitive = {"password", "token", "secret", "credential", "auth", "api_key", "access_key"}
    # Substring match keywords (anywhere in key name)
    substring_sensitive = {"_password", "_token", "_secret", "_key", "_credential", "_auth"}

    for key, value in details.items():
        key_lower = key.lower()

        # Check exact matches first (e.g., "token" but not "tokens")
        is_sensitive = key_lower in exact_sensitive

        # Check substring matches (e.g., "api_key", "auth_token")
        if not is_sensitive:
            is_sensitive = any(keyword in key_lower for keyword in substring_sensitive)

        if is_sensitive:
            sanitized[key] = "***REDACTED***"
            continue

        # Truncate long strings
        if isinstance(value, str):
            sanitized[key] = value[:200] if len(value) > 200 else value
        # Convert complex types to string representation
        elif not isinstance(value, (int, float, bool, type(None))):
            sanitized[key] = str(value)[:200]
        else:
            sanitized[key] = value

    return sanitized


def measure_operation(operation_type: str, details: Dict[str, Any]):
    """
    Context manager for measuring operation duration.

    Args:
        operation_type: Type of operation
        details: Operation details

    Yields:
        None

    Example:
        >>> with measure_operation("db_query", {"query": "SELECT * FROM source"}):
        ...     result = await db.query(...)
    """

    class OperationTimer:
        def __init__(self, op_type: str, op_details: Dict[str, Any]):
            self.op_type = op_type
            self.op_details = op_details
            self.start_time = None

        def __enter__(self):
            self.start_time = time.time()
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            duration_ms = (time.time() - self.start_time) * 1000
            if exc_type:
                # Log error if exception occurred
                log_operation(
                    f"{self.op_type}_error",
                    {**self.op_details, "error": str(exc_val), "error_type": exc_type.__name__},
                    duration_ms=duration_ms,
                )
            else:
                # Log success
                log_operation(self.op_type, self.op_details, duration_ms=duration_ms)
            return False  # Don't suppress exception

    return OperationTimer(operation_type, details)
