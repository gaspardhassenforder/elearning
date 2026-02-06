"""
Debug endpoints for system monitoring and troubleshooting.

Includes:
- Notification health check (Story 7.3)
- Test notification trigger (Story 7.3)
"""

from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from api.auth import require_admin
from open_notebook.observability.notification_service import (
    get_notification_service,
    NotificationPayload,
)

router = APIRouter(prefix="/debug")


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
