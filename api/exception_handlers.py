"""
Global exception handlers for FastAPI with structured logging (Story 7.2).

This module provides exception handlers that:
- Log all HTTPExceptions with request context (AC5)
- Log unhandled exceptions with full context buffer (AC1, AC4)
- Flush context buffer on errors for diagnostics
- Return user-safe error responses without leaking internal details
"""

from fastapi import Request
from fastapi.responses import JSONResponse
from loguru import logger
from starlette.exceptions import HTTPException as StarletteHTTPException

from open_notebook.observability.request_context import (
    context_buffer as context_buffer_var,
    get_request_context,
)


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """
    Handle HTTPException with structured logging (AC5).

    Args:
        request: Incoming HTTP request
        exc: HTTP exception that was raised

    Returns:
        JSON response with error details and CORS headers

    Note:
        - Logs ALL HTTP exceptions with request context (AC5)
        - Includes context buffer for 5xx errors (server-side issues)
        - Excludes context buffer for 4xx errors (client-side issues)
    """
    # Get request context
    ctx = get_request_context()
    buffer = context_buffer_var.get()

    # Determine if we should include context buffer (only for server errors)
    extra_context = {**ctx, "status_code": exc.status_code}

    if exc.status_code >= 500 and buffer:
        # Server error - include context buffer for diagnostics
        extra_context["context_buffer"] = buffer.flush()
    elif buffer:
        # Client error - don't include buffer, but peek for logging
        extra_context["context_buffer_size"] = len(buffer.peek())

    # AC5: Log error BEFORE returning response
    logger.bind(**extra_context).error(
        "HTTP {status_code}: {detail}",
        status_code=exc.status_code,
        detail=exc.detail,
    )

    # Get origin for CORS headers
    origin = request.headers.get("origin", "*")

    # Return user-safe response (no buffer leakage)
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,  # Use "detail" to match FastAPI convention
            "request_id": ctx.get("request_id"),  # Include for user reference
        },
        headers={
            **(exc.headers or {}),
            "Access-Control-Allow-Origin": origin,
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Allow-Methods": "*",
            "Access-Control-Allow-Headers": "*",
        },
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Catch-all handler for unhandled exceptions (AC1, AC4).

    Args:
        request: Incoming HTTP request
        exc: Unhandled exception

    Returns:
        JSON response with generic error message

    Note:
        - Logs full error with stack trace and context buffer (AC1)
        - Flushes context buffer for diagnostic purposes (AC4)
        - Returns generic 500 error (don't expose internal details)
    """
    # Get request context and buffer
    ctx = get_request_context()
    buffer = context_buffer_var.get()

    # Log full error with stack trace and context (AC1, AC4)
    logger.bind(
        **ctx,
        error_type=type(exc).__name__,
        context_buffer=buffer.flush() if buffer else [],
    ).error(
        "Unhandled exception: {error}",
        error=str(exc),
        exc_info=True,  # Include full stack trace
    )

    # Get origin for CORS headers
    origin = request.headers.get("origin", "*")

    # Return generic 500 error (don't expose details)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "An unexpected error occurred. Please try again.",  # Use "detail" to match FastAPI convention
            "request_id": ctx.get("request_id"),  # Include for user reference
        },
        headers={
            "Access-Control-Allow-Origin": origin,
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Allow-Methods": "*",
            "Access-Control-Allow-Headers": "*",
        },
    )
