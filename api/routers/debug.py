"""Debug endpoints for system monitoring and troubleshooting.

Includes:
- Notification health check (Story 7.3)
- Test notification trigger (Story 7.3)
- Error log inspection (Story 7.2)
"""

from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any

from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import BaseModel, Field
from loguru import logger

from api.auth import User, require_admin
from open_notebook.observability.notification_service import (
    get_notification_service,
    NotificationPayload,
)

router = APIRouter(prefix="/debug", tags=["debug"])


# ============================================================================
# Story 7.3: Notification Health & Testing
# ============================================================================


class NotificationHealthResponse(BaseModel):
    """Notification health check response"""

    backend_type: str
    backend_health: dict
    last_notification_attempt: str | None = None


class TestNotificationRequest(BaseModel):
    """Request to trigger test notification"""

    error_summary: str = "Test notification from admin"
    error_type: str = "TestNotification"
    severity: str = "ERROR"


@router.get("/notification-health", dependencies=[Depends(require_admin)])
async def notification_health() -> NotificationHealthResponse:
    """
    Check notification backend health status.

    Returns backend type, configuration status, and recent delivery statistics.
    Admin-only endpoint for monitoring notification system.
    """
    service = get_notification_service()
    backend_health = service.backend.health_check()

    return NotificationHealthResponse(
        backend_type=backend_health.get("backend_type", "unknown"),
        backend_health=backend_health,
    )


@router.post("/test-notification", dependencies=[Depends(require_admin)])
async def test_notification(request: TestNotificationRequest):
    """
    Trigger test notification to verify configuration.

    Sends a test notification through the configured backend.
    Admin-only endpoint for testing notification setup.
    """
    service = get_notification_service()

    payload = NotificationPayload(
        error_summary=request.error_summary,
        error_type=request.error_type,
        severity=request.severity,
        request_id="test-request-id",
        endpoint="POST /api/debug/test-notification",
        timestamp=datetime.now(datetime.UTC if hasattr(datetime, "UTC") else timezone.utc),
        context_snippet=["Test notification triggered by admin"],
    )

    result = await service.notify(payload)

    return {
        "success": result,
        "message": "Notification sent successfully" if result else "Notification delivery failed or suppressed",
    }


# ============================================================================
# Story 7.2: Error Log Inspection
# ============================================================================


class ErrorLogEntry(BaseModel):
    """Structured error log entry."""

    timestamp: str = Field(..., description="ISO 8601 timestamp")
    level: str = Field(..., description="Log level (ERROR, WARNING, etc.)")
    request_id: str | None = Field(None, description="Request correlation ID")
    user_id: str | None = Field(None, description="User ID if authenticated")
    company_id: str | None = Field(None, description="Company ID if applicable")
    endpoint: str | None = Field(None, description="API endpoint")
    error_type: str = Field(..., description="Error type/class name")
    message: str = Field(..., description="Error message")
    stack_trace: str | None = Field(None, description="Stack trace (if available)")
    context_buffer: List[Dict[str, Any]] | None = Field(
        None, description="Rolling context buffer (recent operations)"
    )
    metadata: Dict[str, Any] | None = Field(None, description="Additional metadata")


class ErrorLogsResponse(BaseModel):
    """Response model for error logs endpoint."""

    errors: List[ErrorLogEntry] = Field(..., description="List of error log entries")
    total: int = Field(..., description="Total number of errors matching filters")
    limit: int = Field(..., description="Limit applied to query")
    offset: int = Field(..., description="Offset applied to query")


@router.get("/errors", response_model=ErrorLogsResponse)
async def get_errors(
    limit: int = Query(100, ge=1, le=1000, description="Maximum errors to return"),
    offset: int = Query(0, ge=0, description="Number of errors to skip"),
    user_id: str | None = Query(None, description="Filter by user ID"),
    company_id: str | None = Query(None, description="Filter by company ID"),
    error_type: str | None = Query(None, description="Filter by error type"),
    since: datetime | None = Query(None, description="Errors since timestamp"),
    _admin: User = Depends(require_admin),
) -> ErrorLogsResponse:
    """
    Get recent structured error logs (admin only).

    Story 7.2 - Task 9: Admin debug endpoint for error inspection.

    Query params:
    - limit: Max errors to return (default: 100, max: 1000)
    - offset: Number of errors to skip (for pagination)
    - user_id: Filter by user
    - company_id: Filter by company
    - error_type: Filter by error type
    - since: Errors since timestamp (default: last 24h)

    Returns:
        ErrorLogsResponse with filtered error log entries

    Raises:
        HTTPException 403: Unauthorized (not admin)
        HTTPException 500: Error reading logs
    """
    logger.info(
        f"Admin {_admin.id} requesting error logs: "
        f"limit={limit}, offset={offset}, user_id={user_id}, "
        f"company_id={company_id}, error_type={error_type}, since={since}"
    )

    # Default: last 24 hours
    if not since:
        since = datetime.utcnow() - timedelta(hours=24)

    try:
        # Get errors from in-memory error store
        # Note: This is a simple implementation using log file parsing
        # Production deployments should use a proper log aggregation service
        # (e.g., Elasticsearch, Loki, CloudWatch Logs)

        errors = await _get_recent_errors_from_logs(
            limit=limit,
            offset=offset,
            user_id=user_id,
            company_id=company_id,
            error_type=error_type,
            since=since,
        )

        return ErrorLogsResponse(
            errors=errors,
            total=len(errors),  # Note: This is the filtered count, not total
            limit=limit,
            offset=offset,
        )

    except Exception as e:
        logger.error("Error retrieving error logs: {}", str(e), exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve error logs. Check server logs for details."
        )


async def _get_recent_errors_from_logs(
    limit: int,
    offset: int,
    user_id: str | None,
    company_id: str | None,
    error_type: str | None,
    since: datetime,
) -> List[ErrorLogEntry]:
    """
    Parse log files to extract structured error entries.

    This is a simple implementation for MVP. Production deployments should
    use proper log aggregation services.

    Args:
        limit: Maximum number of errors to return
        offset: Number of errors to skip
        user_id: Filter by user ID
        company_id: Filter by company ID
        error_type: Filter by error type
        since: Only errors after this timestamp

    Returns:
        List of ErrorLogEntry matching filters
    """
    # TODO: Implement proper log parsing or connect to log aggregation service
    # For now, return empty list with note that this is placeholder

    logger.warning(
        "Debug error endpoint called but log parsing not implemented. "
        "In production, integrate with log aggregation service (ELK, Loki, CloudWatch)."
    )

    # Return placeholder response
    return []

    # Note for implementation:
    # 1. If using file-based logging, parse JSON log files
    # 2. If using log aggregation service, query via API
    # 3. Apply filters: since, user_id, company_id, error_type
    # 4. Apply pagination: offset, limit
    # 5. Return structured ErrorLogEntry objects
