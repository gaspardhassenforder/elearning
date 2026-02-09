"""Frontend Error Logging Router - Collect Client-Side Errors.

Story 7.2 - Task 8: Frontend Error Collection Endpoint
Collects client-side errors with structured logging for diagnostics.
"""

from fastapi import APIRouter, Request
from loguru import logger
from pydantic import BaseModel, Field

router = APIRouter(prefix="/logs", tags=["logs"])


class FrontendError(BaseModel):
    """Frontend error payload."""

    message: str = Field(..., description="Error message")
    stack: str | None = Field(None, description="Stack trace (if available)")
    url: str = Field(..., description="Page URL where error occurred")
    user_agent: str = Field(..., description="Browser user agent")
    request_id: str | None = Field(None, description="Request ID from context (if available)")
    user_id: str | None = Field(None, description="User ID from auth state (if available)")
    component: str | None = Field(None, description="React component name (if available)")
    error_type: str | None = Field(None, description="Error type/name")


@router.post("/frontend-error", status_code=204, include_in_schema=True)
async def log_frontend_error(error: FrontendError, request: Request):
    """
    Log frontend errors with structured format.

    Story 7.2 - Task 8: Collects client-side errors for backend observability.

    Rate limiting should be applied at the proxy/gateway level
    (10 requests/minute per IP recommended).

    Args:
        error: Frontend error details
        request: FastAPI request object (for metadata)

    Returns:
        204 No Content - error logged, no response needed
    """
    # Get request context if available (from Story 7.2 infrastructure)
    try:
        from open_notebook.observability.request_context import get_request_context

        ctx = get_request_context()
    except Exception:
        ctx = {}

    # Log error with structured format
    logger.error(
        f"Frontend error: {error.message}",
        extra={
            **ctx,  # Include request context if available
            "error_type": error.error_type or "FrontendError",
            "request_id": error.request_id,
            "user_id": error.user_id,
            "url": error.url,
            "user_agent": error.user_agent,
            "component": error.component,
            "stack_trace": error.stack,
            "client_ip": request.client.host if request.client else None,
        },
    )

    # 204 No Content - error logged, no response needed
    return None
