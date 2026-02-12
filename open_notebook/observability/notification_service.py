"""
Admin notification service for error alerts.

This module provides pluggable notification backends for sending error alerts
to administrators via webhook, Slack, or email.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class NotificationPayload(BaseModel):
    """
    Structured notification payload for admin error alerts.

    All fields are user/company-safe (no sensitive data).
    Stack traces and context buffers are truncated for brevity.
    """

    # Error identification
    error_summary: str = Field(..., description="Brief error message (max 200 chars)")
    error_type: str = Field(..., description="Exception class name")
    severity: str = Field(default="ERROR", description="Log severity level")

    # Request context (from Story 7.2)
    request_id: Optional[str] = Field(None, description="Unique request correlation ID")
    user_id: Optional[str] = Field(None, description="Affected user (if authenticated)")
    company_id: Optional[str] = Field(None, description="Affected company (if scoped)")
    endpoint: Optional[str] = Field(None, description="API endpoint (e.g., 'POST /api/chat')")

    # Timing
    timestamp: datetime = Field(..., description="Error occurrence time (UTC)")

    # Context (from Story 7.2 rolling buffer)
    context_snippet: List[str] = Field(
        default_factory=list,
        description="Last 3 operations before error (human-readable)",
    )

    # Debug reference
    stack_trace_preview: Optional[str] = Field(
        None,
        max_length=500,
        description="First 500 chars of stack trace",
    )

    # Deduplication metadata
    suppressed_count: int = Field(
        default=0,
        description="Number of duplicate notifications suppressed in last 5min",
    )

    def format_for_webhook(self) -> Dict[str, Any]:
        """Format payload as generic JSON for webhook POST"""
        return {
            "error": {
                "summary": self.error_summary,
                "type": self.error_type,
                "severity": self.severity,
            },
            "request": {
                "id": self.request_id,
                "endpoint": self.endpoint,
                "timestamp": self.timestamp.isoformat(),
            },
            "affected": {
                "user_id": self.user_id,
                "company_id": self.company_id,
            },
            "context": {
                "recent_operations": self.context_snippet,
                "stack_trace_preview": self.stack_trace_preview,
            },
            "meta": {
                "suppressed_duplicates": self.suppressed_count,
            },
        }

    def format_for_slack(self) -> Dict[str, Any]:
        """Format payload as Slack Block Kit message"""
        # Color coding by severity
        color = "#DC2626" if self.severity == "ERROR" else "#F59E0B"  # red or amber

        # Build context fields
        fields = [
            {"type": "mrkdwn", "text": f"*Error Type:*\n{self.error_type}"},
            {"type": "mrkdwn", "text": f"*Endpoint:*\n`{self.endpoint or 'N/A'}`"},
            {"type": "mrkdwn", "text": f"*Request ID:*\n`{self.request_id or 'N/A'}`"},
            {"type": "mrkdwn", "text": f"*Timestamp:*\n{self.timestamp.isoformat()}"},
        ]

        if self.user_id:
            fields.append({"type": "mrkdwn", "text": f"*User:*\n`{self.user_id}`"})
        if self.company_id:
            fields.append({"type": "mrkdwn", "text": f"*Company:*\n`{self.company_id}`"})

        # Build context snippet section
        context_text = (
            "\n".join(f"• {op}" for op in self.context_snippet)
            if self.context_snippet
            else "_No context available_"
        )

        # Deduplication notice
        dedup_text = ""
        if self.suppressed_count > 0:
            dedup_text = f"\n\n_Note: {self.suppressed_count} duplicate notifications suppressed in last 5 minutes_"

        return {
            "attachments": [
                {
                    "color": color,
                    "blocks": [
                        {
                            "type": "header",
                            "text": {
                                "type": "plain_text",
                                "text": f"🚨 {self.severity}: {self.error_summary[:50]}",
                            },
                        },
                        {"type": "section", "fields": fields},
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": f"*Recent Operations:*\n{context_text}{dedup_text}",
                            },
                        },
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": f"*Stack Trace Preview:*\n```{self.stack_trace_preview or 'N/A'}```",
                            },
                        },
                    ],
                }
            ]
        }

    def format_for_email(self) -> tuple[str, str]:
        """Format payload as (HTML, plain text) email body"""
        # HTML email body
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; }}
                .error-summary {{ background: #FEE2E2; padding: 15px; border-left: 4px solid #DC2626; }}
                .metadata {{ background: #F3F4F6; padding: 10px; margin-top: 15px; }}
                .context {{ background: #FFFBEB; padding: 10px; margin-top: 15px; }}
                code {{ background: #F3F4F6; padding: 2px 5px; }}
            </style>
        </head>
        <body>
            <h2 style="color: #DC2626;">🚨 Error Notification: {self.severity}</h2>

            <div class="error-summary">
                <strong>{self.error_type}</strong>: {self.error_summary}
            </div>

            <div class="metadata">
                <table>
                    <tr><td><strong>Request ID:</strong></td><td><code>{self.request_id or 'N/A'}</code></td></tr>
                    <tr><td><strong>Endpoint:</strong></td><td><code>{self.endpoint or 'N/A'}</code></td></tr>
                    <tr><td><strong>Timestamp:</strong></td><td>{self.timestamp.isoformat()}</td></tr>
                    <tr><td><strong>User:</strong></td><td><code>{self.user_id or 'N/A'}</code></td></tr>
                    <tr><td><strong>Company:</strong></td><td><code>{self.company_id or 'N/A'}</code></td></tr>
                </table>
            </div>

            <div class="context">
                <h3>Recent Operations</h3>
                <ul>
                    {''.join(f"<li>{op}</li>" for op in self.context_snippet) if self.context_snippet else "<li>No context available</li>"}
                </ul>
            </div>

            <div class="context">
                <h3>Stack Trace Preview</h3>
                <pre>{self.stack_trace_preview or 'N/A'}</pre>
            </div>

            {f'<p><em>Note: {self.suppressed_count} duplicate notifications suppressed in last 5 minutes</em></p>' if self.suppressed_count > 0 else ''}
        </body>
        </html>
        """

        # Plain text fallback
        plain = f"""
        🚨 Error Notification: {self.severity}

        {self.error_type}: {self.error_summary}

        Request ID: {self.request_id or 'N/A'}
        Endpoint: {self.endpoint or 'N/A'}
        Timestamp: {self.timestamp.isoformat()}
        User: {self.user_id or 'N/A'}
        Company: {self.company_id or 'N/A'}

        Recent Operations:
        {chr(10).join(f'- {op}' for op in self.context_snippet) if self.context_snippet else '- No context available'}

        Stack Trace Preview:
        {self.stack_trace_preview or 'N/A'}

        {f'Note: {self.suppressed_count} duplicate notifications suppressed in last 5 minutes' if self.suppressed_count > 0 else ''}
        """

        return (html, plain)


class NotificationBackend(ABC):
    """
    Abstract base class for admin notification backends.

    All backends must implement send() with graceful failure handling.
    Notification delivery failures MUST NOT raise exceptions - they should
    log warnings and return silently.
    """

    @abstractmethod
    async def send(self, payload: NotificationPayload) -> bool:
        """
        Send notification to admin.

        Args:
            payload: Structured notification data

        Returns:
            True if notification sent successfully, False otherwise

        Raises:
            Never raises - all failures handled internally with logging
        """
        pass

    @abstractmethod
    def health_check(self) -> dict:
        """
        Check backend health status.

        Returns:
            {
                "backend_type": "webhook",
                "configured": True,
                "last_success": "2026-02-06T14:30:00Z",
                "last_failure": None,
                "failure_count_24h": 0,
            }
        """
        pass


import asyncio
import hashlib
import httpx
import os
from collections import OrderedDict
from datetime import timezone, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from loguru import logger
from pydantic_settings import BaseSettings
from typing import Literal

try:
    import aiosmtplib
    AIOSMTPLIB_AVAILABLE = True
except ImportError:
    AIOSMTPLIB_AVAILABLE = False


class NotificationDeduplicator:
    """
    LRU cache-based notification deduplication.

    Suppresses duplicate notifications within a configurable time window (default: 5 minutes).
    Tracks suppressed count and includes it in next notification after window expires.
    """

    def __init__(self, window_seconds: int = 300, max_size: int = 100):
        """
        Initialize deduplicator.

        Args:
            window_seconds: Time window for deduplication (default: 300 = 5 minutes)
            max_size: Maximum cache size (default: 100, LRU eviction)
        """
        self.window_seconds = window_seconds
        self.max_size = max_size
        # OrderedDict acts as LRU cache (oldest entries first)
        self._cache: OrderedDict[str, tuple[datetime, int]] = OrderedDict()

    def _cache_key(self, payload: NotificationPayload) -> str:
        """
        Generate cache key from error signature.

        Key excludes user/company to deduplicate across all users.
        Includes: error_type, endpoint, error_summary (first 100 chars)
        """
        signature = f"{payload.error_type}:{payload.endpoint or 'unknown'}:{payload.error_summary[:100]}"
        return hashlib.md5(signature.encode()).hexdigest()

    def _evict_oldest(self):
        """Evict oldest entry when cache is full (LRU)"""
        if len(self._cache) >= self.max_size:
            self._cache.popitem(last=False)  # Remove oldest (first) item

    def _clean_expired(self):
        """Remove expired entries from cache"""
        now = datetime.now(datetime.UTC if hasattr(datetime, "UTC") else timezone.utc)
        expired_keys = [
            key
            for key, (timestamp, _) in self._cache.items()
            if (now - timestamp).total_seconds() > self.window_seconds
        ]
        for key in expired_keys:
            del self._cache[key]

    def should_send(self, payload: NotificationPayload) -> tuple[bool, int]:
        """
        Check if notification should be sent.

        Args:
            payload: Notification payload to check

        Returns:
            (should_send, suppressed_count) tuple:
            - should_send: True if notification should be sent, False if suppressed
            - suppressed_count: Number of notifications suppressed since last send

        Side effects:
            Updates cache with current timestamp and increments suppressed count
        """
        self._clean_expired()
        key = self._cache_key(payload)
        now = datetime.now(datetime.UTC if hasattr(datetime, "UTC") else timezone.utc)

        if key in self._cache:
            # Duplicate within window
            last_sent, suppressed_count = self._cache[key]
            self._cache[key] = (last_sent, suppressed_count + 1)  # Increment suppressed count
            self._cache.move_to_end(key)  # Mark as recently used (LRU)
            return (False, suppressed_count + 1)
        else:
            # First occurrence or window expired
            self._evict_oldest()
            self._cache[key] = (now, 0)  # Store timestamp, 0 suppressed count
            return (True, 0)

    def mark_sent(self, payload: NotificationPayload):
        """
        Mark notification as successfully sent and reset suppressed count.

        Call after successful notification delivery to update cache.
        """
        key = self._cache_key(payload)
        now = datetime.now(datetime.UTC if hasattr(datetime, "UTC") else timezone.utc)
        if key in self._cache:
            _, suppressed_count = self._cache[key]
            self._cache[key] = (now, 0)  # Reset suppressed count after successful send
            return suppressed_count
        return 0


class NotificationConfig(BaseSettings):
    """
    Configuration for admin error notifications.

    Loads from environment variables with defaults for MVP (disabled).
    """

    model_config = {"env_prefix": "", "case_sensitive": False}

    error_notification_backend: Literal["none", "webhook", "slack", "email"] = "none"

    # Webhook backend config
    webhook_url: Optional[str] = None

    # Slack backend config
    slack_webhook_url: Optional[str] = None

    # Email backend config
    smtp_host: Optional[str] = None
    smtp_port: int = 587
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_use_tls: bool = True
    admin_email: Optional[str] = None

    @classmethod
    def from_env(cls) -> "NotificationConfig":
        """Load configuration from environment variables"""
        return cls()


def create_notification_backend(config: Optional[NotificationConfig] = None) -> NotificationBackend:
    """
    Factory function to create notification backend from configuration.

    Args:
        config: Optional NotificationConfig (loads from env if None)

    Returns:
        Configured notification backend (or NullBackend if disabled/invalid)
    """
    if config is None:
        config = NotificationConfig.from_env()

    backend_type = config.error_notification_backend.lower()

    try:
        if backend_type == "webhook":
            if not config.webhook_url:
                logger.warning("Webhook backend selected but WEBHOOK_URL not configured - falling back to NullBackend")
                return NullBackend()
            return WebhookBackend(webhook_url=config.webhook_url)

        elif backend_type == "slack":
            if not config.slack_webhook_url:
                logger.warning("Slack backend selected but SLACK_WEBHOOK_URL not configured - falling back to NullBackend")
                return NullBackend()
            return SlackBackend(webhook_url=config.slack_webhook_url)

        elif backend_type == "email":
            # Check aiosmtplib availability BEFORE creating backend
            if not AIOSMTPLIB_AVAILABLE:
                logger.warning(
                    "Email backend selected but aiosmtplib not installed - falling back to NullBackend. "
                    "Install with: pip install aiosmtplib"
                )
                return NullBackend()

            if not all([config.smtp_host, config.smtp_user, config.smtp_password, config.admin_email]):
                logger.warning(
                    "Email backend selected but SMTP configuration incomplete - falling back to NullBackend. "
                    "Required: SMTP_HOST, SMTP_USER, SMTP_PASSWORD, ADMIN_EMAIL"
                )
                return NullBackend()
            return EmailBackend(
                smtp_host=config.smtp_host,
                smtp_port=config.smtp_port,
                smtp_user=config.smtp_user,
                smtp_password=config.smtp_password,
                admin_email=config.admin_email,
                use_tls=config.smtp_use_tls,
            )

        else:  # "none" or invalid value
            logger.info("Notification backend set to 'none' - admin notifications disabled")
            return NullBackend()

    except Exception as e:
        logger.error("Failed to create notification backend ({}): {} - falling back to NullBackend", backend_type, str(e))
        return NullBackend()


class NotificationService:
    """
    High-level notification service with deduplication.

    Combines notification backend with deduplication logic.
    """

    def __init__(self, backend: NotificationBackend, deduplicator: Optional[NotificationDeduplicator] = None):
        self.backend = backend
        self.deduplicator = deduplicator or NotificationDeduplicator()

    async def notify(self, payload: NotificationPayload) -> bool:
        """
        Send notification with deduplication.

        Args:
            payload: Notification payload

        Returns:
            True if notification was sent, False if suppressed or failed
        """
        # Check deduplication
        should_send, suppressed_count = self.deduplicator.should_send(payload)

        if not should_send:
            logger.debug(
                f"Notification suppressed (duplicate within window): {payload.error_type} - {payload.error_summary[:50]}"
            )
            return False

        # Include suppressed count in payload
        payload.suppressed_count = suppressed_count

        # Send notification
        result = await self.backend.send(payload)

        if result:
            # Mark as sent to update deduplication cache
            self.deduplicator.mark_sent(payload)

        return result


# Global notification service instance (singleton)
_notification_service: Optional[NotificationService] = None


def get_notification_service() -> NotificationService:
    """
    Get global notification service singleton.

    Lazily initialized on first call from environment variables.
    """
    global _notification_service
    if _notification_service is None:
        backend = create_notification_backend()
        _notification_service = NotificationService(backend=backend)
    return _notification_service


class WebhookBackend(NotificationBackend):
    """
    Generic HTTP POST webhook notification backend.

    Features:
    - Async HTTP POST with 5-second timeout
    - 4 retry attempts with exponential backoff (1s, 2s, 4s)
    - Graceful failure handling (never raises)
    - Health check tracking (last success/failure timestamps)
    """

    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
        self.last_success: Optional[datetime] = None
        self.last_failure: Optional[datetime] = None
        self.failure_count_24h = 0

    async def send(self, payload: NotificationPayload) -> bool:
        """
        Send notification via HTTP POST with retry logic.

        Retry behavior:
        - Attempt 1: immediate
        - Attempt 2: after 1 second
        - Attempt 3: after 2 seconds
        - Attempt 4: after 4 seconds

        Returns False if all attempts fail, never raises.
        """
        for attempt in range(1, 5):  # 4 total attempts
            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    response = await client.post(
                        self.webhook_url,
                        json=payload.format_for_webhook(),
                        headers={"Content-Type": "application/json"},
                    )
                    response.raise_for_status()

                # Success
                self.last_success = datetime.now(datetime.UTC if hasattr(datetime, "UTC") else timezone.utc)
                logger.info(f"Notification sent via webhook (attempt {attempt})")
                return True

            except (httpx.HTTPError, httpx.TimeoutException) as e:
                logger.warning(
                    "Webhook notification failed (attempt {}/4): {}",
                    attempt, str(e),
                    extra={"webhook_url": self.webhook_url},
                )

                # Exponential backoff before retry
                if attempt < 4:
                    await asyncio.sleep(2 ** (attempt - 1))  # 1s, 2s, 4s

        # All attempts failed
        self.last_failure = datetime.now(datetime.UTC if hasattr(datetime, "UTC") else timezone.utc)
        self.failure_count_24h += 1
        logger.error(
            f"Webhook notification failed after 4 attempts",
            extra={"webhook_url": self.webhook_url, "payload": payload.model_dump()},
        )
        return False

    def health_check(self) -> dict:
        return {
            "backend_type": "webhook",
            "configured": bool(self.webhook_url),
            "webhook_url": self.webhook_url[:30] + "..." if len(self.webhook_url) > 30 else self.webhook_url,
            "last_success": self.last_success.isoformat() if self.last_success else None,
            "last_failure": self.last_failure.isoformat() if self.last_failure else None,
            "failure_count_24h": self.failure_count_24h,
        }


class SlackBackend(NotificationBackend):
    """
    Slack webhook notification backend with Block Kit formatting.

    Uses Slack Incoming Webhooks API with rich Block Kit messages.
    Inherits retry logic from WebhookBackend pattern.
    """

    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
        self.last_success: Optional[datetime] = None
        self.last_failure: Optional[datetime] = None
        self.failure_count_24h = 0

    async def send(self, payload: NotificationPayload) -> bool:
        """Send notification to Slack with Block Kit formatting"""
        for attempt in range(1, 5):
            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    response = await client.post(
                        self.webhook_url,
                        json=payload.format_for_slack(),
                        headers={"Content-Type": "application/json"},
                    )
                    response.raise_for_status()

                self.last_success = datetime.now(datetime.UTC if hasattr(datetime, "UTC") else timezone.utc)
                logger.info(f"Notification sent via Slack (attempt {attempt})")
                return True

            except (httpx.HTTPError, httpx.TimeoutException) as e:
                logger.warning(
                    "Slack notification failed (attempt {}/4): {}",
                    attempt, str(e),
                    extra={"slack_webhook_url": self.webhook_url[:30] + "..."},
                )
                if attempt < 4:
                    await asyncio.sleep(2 ** (attempt - 1))

        self.last_failure = datetime.now(datetime.UTC if hasattr(datetime, "UTC") else timezone.utc)
        self.failure_count_24h += 1
        logger.error(f"Slack notification failed after 4 attempts")
        return False

    def health_check(self) -> dict:
        return {
            "backend_type": "slack",
            "configured": bool(self.webhook_url),
            "webhook_url": self.webhook_url[:30] + "..." if len(self.webhook_url) > 30 else self.webhook_url,
            "last_success": self.last_success.isoformat() if self.last_success else None,
            "last_failure": self.last_failure.isoformat() if self.last_failure else None,
            "failure_count_24h": self.failure_count_24h,
        }


class EmailBackend(NotificationBackend):
    """
    SMTP email notification backend.

    Features:
    - Async SMTP with aiosmtplib
    - HTML + plain text multipart messages
    - Configurable SMTP server (Gmail, SendGrid, custom)
    - Graceful connection failure handling
    """

    def __init__(
        self,
        smtp_host: str,
        smtp_port: int,
        smtp_user: str,
        smtp_password: str,
        admin_email: str,
        use_tls: bool = True,
    ):
        if not AIOSMTPLIB_AVAILABLE:
            logger.warning("aiosmtplib not installed - EmailBackend will fail")

        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_user = smtp_user
        self.smtp_password = smtp_password
        self.admin_email = admin_email
        self.use_tls = use_tls
        self.last_success: Optional[datetime] = None
        self.last_failure: Optional[datetime] = None
        self.failure_count_24h = 0

    async def send(self, payload: NotificationPayload) -> bool:
        """Send notification via SMTP email"""
        if not AIOSMTPLIB_AVAILABLE:
            logger.error("EmailBackend requires aiosmtplib - install with: pip install aiosmtplib")
            return False

        try:
            # Create multipart message
            msg = MIMEMultipart("alternative")
            msg["From"] = self.smtp_user
            msg["To"] = self.admin_email
            msg["Subject"] = f"🚨 Error Alert: {payload.error_type} - {payload.error_summary[:50]}"

            # Attach plain text and HTML parts
            html, plain = payload.format_for_email()
            msg.attach(MIMEText(plain, "plain"))
            msg.attach(MIMEText(html, "html"))

            # Send email
            await aiosmtplib.send(
                msg,
                hostname=self.smtp_host,
                port=self.smtp_port,
                username=self.smtp_user,
                password=self.smtp_password,
                use_tls=self.use_tls,
                timeout=10,
            )

            self.last_success = datetime.now(datetime.UTC if hasattr(datetime, "UTC") else timezone.utc)
            logger.info(f"Notification sent via email to {self.admin_email}")
            return True

        except Exception as e:
            self.last_failure = datetime.now(datetime.UTC if hasattr(datetime, "UTC") else timezone.utc)
            self.failure_count_24h += 1
            logger.error(
                "Email notification failed: {}",
                str(e),
                extra={"smtp_host": self.smtp_host, "admin_email": self.admin_email},
            )
            return False

    def health_check(self) -> dict:
        return {
            "backend_type": "email",
            "configured": bool(self.smtp_host and self.admin_email),
            "smtp_host": self.smtp_host,
            "smtp_port": self.smtp_port,
            "admin_email": self.admin_email,
            "last_success": self.last_success.isoformat() if self.last_success else None,
            "last_failure": self.last_failure.isoformat() if self.last_failure else None,
            "failure_count_24h": self.failure_count_24h,
            "aiosmtplib_available": AIOSMTPLIB_AVAILABLE,
        }


class NullBackend(NotificationBackend):
    """
    No-op notification backend (notifications disabled).

    Used when ERROR_NOTIFICATION_BACKEND is set to 'none' or not configured.
    """

    async def send(self, payload: NotificationPayload) -> bool:
        """No-op send - notifications disabled"""
        return True

    def health_check(self) -> dict:
        return {
            "backend_type": "none",
            "configured": False,
            "status": "Notifications disabled",
        }
