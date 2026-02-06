"""
Request logging middleware for FastAPI.

This middleware handles request lifecycle logging with context tracking:
- Generates unique request IDs
- Initializes request context (user_id, company_id, endpoint)
- Tracks request duration
- Logs successful requests
- Flushes context buffer on errors
- Cleans up context after request completes
"""

import time
import uuid
from datetime import UTC, datetime

from fastapi import Request
from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from open_notebook.observability.context_buffer import RollingContextBuffer
from open_notebook.observability.request_context import context_buffer, request_context


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for request lifecycle logging with context tracking.

    Responsibilities:
    - Generate unique request_id for correlation
    - Initialize request context (user_id, company_id, endpoint)
    - Initialize rolling context buffer
    - Log request start/end with timing
    - Flush context buffer on error for diagnostics
    - Clean up context after request completes

    Note:
        Must be registered in FastAPI app BEFORE CORSMiddleware to ensure
        context is available for all subsequent middleware and route handlers.
    """

    async def dispatch(self, request: Request, call_next):
        """
        Process request with context tracking.

        Args:
            request: Incoming HTTP request
            call_next: Next middleware/handler in chain

        Returns:
            Response from downstream handlers

        Note:
            Context variables are set at the start of the request and cleared
            in the finally block to prevent memory leaks between requests.
        """
        # Generate unique request ID
        request_id = str(uuid.uuid4())

        # Extract user info from request state (set by auth dependencies)
        user_id = getattr(request.state, "user_id", None)
        company_id = getattr(request.state, "company_id", None)

        # Initialize request context
        ctx = {
            "request_id": request_id,
            "user_id": user_id,
            "company_id": company_id,
            "endpoint": f"{request.method} {request.url.path}",
            "timestamp": datetime.now(UTC).isoformat(),
        }
        request_context.set(ctx)

        # Initialize rolling buffer
        buffer = RollingContextBuffer(max_size=50)
        context_buffer.set(buffer)

        # Log request start
        logger.info("Request started", extra=ctx)

        # Track timing
        start_time = time.time()

        try:
            # Process request
            response: Response = await call_next(request)

            # Log successful completion
            duration_ms = (time.time() - start_time) * 1000
            logger.info(
                "Request completed",
                extra={
                    **ctx,
                    "status_code": response.status_code,
                    "duration_ms": duration_ms,
                },
            )

            # Discard buffer on success (no need to log operations for successful requests)
            buffer.clear()

            return response

        except Exception as e:
            # Log error with full context buffer
            duration_ms = (time.time() - start_time) * 1000
            logger.error(
                f"Request failed: {str(e)}",
                extra={
                    **ctx,
                    "duration_ms": duration_ms,
                    "error_type": type(e).__name__,
                    "context_buffer": buffer.flush(),
                },
                exc_info=True,
            )
            raise

        finally:
            # Clean up context (prevent memory leaks)
            request_context.set(None)
            context_buffer.set(None)
