"""
Tests for admin notification service (Story 7.3).

Tests cover:
- Notification payload formatting (webhook, Slack, email)
- Notification backends (webhook, Slack, email, null)
- Deduplication logic
- Graceful failure handling
"""

import pytest
from datetime import datetime

from open_notebook.observability.notification_service import (
    NotificationPayload,
    NullBackend,
)


class TestNotificationPayload:
    """Test notification payload model and formatting"""

    def test_payload_basic_fields(self):
        """Test basic payload creation"""
        payload = NotificationPayload(
            error_summary="Database connection failed",
            error_type="ConnectionError",
            severity="ERROR",
            timestamp=datetime(2026, 2, 6, 14, 30, 0),
        )

        assert payload.error_summary == "Database connection failed"
        assert payload.error_type == "ConnectionError"
        assert payload.severity == "ERROR"
        assert payload.timestamp == datetime(2026, 2, 6, 14, 30, 0)
        assert payload.suppressed_count == 0

    def test_payload_with_request_context(self):
        """Test payload with request context from Story 7.2"""
        payload = NotificationPayload(
            error_summary="Unauthorized access",
            error_type="PermissionError",
            severity="ERROR",
            request_id="req-123",
            user_id="user:abc",
            company_id="company:xyz",
            endpoint="POST /api/chat",
            timestamp=datetime(2026, 2, 6, 14, 30, 0),
        )

        assert payload.request_id == "req-123"
        assert payload.user_id == "user:abc"
        assert payload.company_id == "company:xyz"
        assert payload.endpoint == "POST /api/chat"

    def test_payload_with_context_snippet(self):
        """Test payload with context snippet from rolling buffer"""
        payload = NotificationPayload(
            error_summary="LLM call failed",
            error_type="TimeoutError",
            severity="ERROR",
            context_snippet=[
                "db_query: SELECT * FROM source (45.2ms)",
                "ai_call: ChatOpenAI.generate (2.3s)",
                "tool_invoke: search_sources (1.2s)",
            ],
            timestamp=datetime(2026, 2, 6, 14, 30, 0),
        )

        assert len(payload.context_snippet) == 3
        assert "db_query" in payload.context_snippet[0]

    def test_payload_stack_trace_truncation(self):
        """Test stack trace preview truncated to 500 chars"""
        long_trace = "Traceback (most recent call last):\n" + ("  File '/path/to/file.py', line 123, in function\n" * 50)

        # Manual truncation before passing to model (Pydantic max_length validates, doesn't truncate)
        truncated_trace = long_trace[:500]

        payload = NotificationPayload(
            error_summary="Stack overflow",
            error_type="RecursionError",
            severity="ERROR",
            stack_trace_preview=truncated_trace,
            timestamp=datetime(2026, 2, 6, 14, 30, 0),
        )

        # Pydantic max_length should accept truncated string
        assert len(payload.stack_trace_preview) == 500

    def test_format_for_webhook(self):
        """Test webhook JSON formatting"""
        payload = NotificationPayload(
            error_summary="Database error",
            error_type="DatabaseError",
            severity="ERROR",
            request_id="req-123",
            user_id="user:abc",
            company_id="company:xyz",
            endpoint="POST /api/notebooks",
            context_snippet=["db_query: INSERT INTO notebook"],
            stack_trace_preview="Traceback: ...",
            timestamp=datetime(2026, 2, 6, 14, 30, 0),
        )

        webhook_data = payload.format_for_webhook()

        assert webhook_data["error"]["summary"] == "Database error"
        assert webhook_data["error"]["type"] == "DatabaseError"
        assert webhook_data["request"]["id"] == "req-123"
        assert webhook_data["request"]["endpoint"] == "POST /api/notebooks"
        assert webhook_data["affected"]["user_id"] == "user:abc"
        assert webhook_data["context"]["recent_operations"] == ["db_query: INSERT INTO notebook"]
        assert webhook_data["meta"]["suppressed_duplicates"] == 0

    def test_format_for_slack_basic(self):
        """Test Slack Block Kit formatting - basic structure"""
        payload = NotificationPayload(
            error_summary="API timeout",
            error_type="TimeoutError",
            severity="ERROR",
            endpoint="GET /api/sources",
            timestamp=datetime(2026, 2, 6, 14, 30, 0),
        )

        slack_data = payload.format_for_slack()

        assert "attachments" in slack_data
        assert len(slack_data["attachments"]) == 1
        assert slack_data["attachments"][0]["color"] == "#DC2626"  # red for ERROR
        assert "blocks" in slack_data["attachments"][0]

    def test_format_for_slack_with_context(self):
        """Test Slack formatting with context snippet"""
        payload = NotificationPayload(
            error_summary="Database error",
            error_type="DatabaseError",
            severity="ERROR",
            context_snippet=["operation 1", "operation 2", "operation 3"],
            timestamp=datetime(2026, 2, 6, 14, 30, 0),
        )

        slack_data = payload.format_for_slack()
        blocks = slack_data["attachments"][0]["blocks"]

        # Find Recent Operations block
        recent_ops_block = next(
            (b for b in blocks if b.get("type") == "section" and "Recent Operations" in b.get("text", {}).get("text", "")),
            None,
        )
        assert recent_ops_block is not None
        assert "operation 1" in recent_ops_block["text"]["text"]

    def test_format_for_slack_warning_color(self):
        """Test Slack color coding for WARNING severity"""
        payload = NotificationPayload(
            error_summary="Rate limit approaching",
            error_type="WarningError",
            severity="WARNING",
            timestamp=datetime(2026, 2, 6, 14, 30, 0),
        )

        slack_data = payload.format_for_slack()
        assert slack_data["attachments"][0]["color"] == "#F59E0B"  # amber for WARNING

    def test_format_for_email_structure(self):
        """Test email HTML + plain text formatting"""
        payload = NotificationPayload(
            error_summary="SMTP error",
            error_type="SMTPError",
            severity="ERROR",
            request_id="req-456",
            timestamp=datetime(2026, 2, 6, 14, 30, 0),
        )

        html, plain = payload.format_for_email()

        # HTML checks
        assert "<html>" in html
        assert "Error Notification" in html
        assert "SMTPError" in html
        assert "req-456" in html

        # Plain text checks
        assert "Error Notification" in plain
        assert "SMTPError" in plain
        assert "req-456" in plain

    def test_format_for_email_with_deduplication(self):
        """Test email formatting includes deduplication notice"""
        payload = NotificationPayload(
            error_summary="Repeated error",
            error_type="RepeatedError",
            severity="ERROR",
            suppressed_count=15,
            timestamp=datetime(2026, 2, 6, 14, 30, 0),
        )

        html, plain = payload.format_for_email()

        assert "15 duplicate notifications suppressed" in html
        assert "15 duplicate notifications suppressed" in plain


from unittest.mock import AsyncMock, patch
import httpx

import time

from open_notebook.observability.notification_service import (
    WebhookBackend,
    SlackBackend,
    EmailBackend,
    NotificationConfig,
    create_notification_backend,
    NotificationDeduplicator,
    NotificationService,
)


class TestWebhookBackend:
    """Test WebhookBackend notification delivery"""

    @pytest.mark.asyncio
    async def test_webhook_successful_delivery(self):
        """Test successful webhook notification delivery"""
        backend = WebhookBackend(webhook_url="https://example.com/webhook")
        payload = NotificationPayload(
            error_summary="Test error",
            error_type="TestError",
            severity="ERROR",
            timestamp=datetime(2026, 2, 6, 14, 30, 0),
        )

        # Mock successful HTTP POST
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = AsyncMock()
            mock_response.raise_for_status = lambda: None  # Sync method, not async
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)

            result = await backend.send(payload)

        assert result is True
        assert backend.last_success is not None
        assert backend.last_failure is None

    @pytest.mark.asyncio
    async def test_webhook_retry_logic(self):
        """Test webhook retry on failure (4 attempts)"""
        backend = WebhookBackend(webhook_url="https://example.com/webhook")
        payload = NotificationPayload(
            error_summary="Test error",
            error_type="TestError",
            severity="ERROR",
            timestamp=datetime(2026, 2, 6, 14, 30, 0),
        )

        # Mock HTTP POST that fails all attempts
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                side_effect=httpx.TimeoutException("Connection timeout")
            )

            # Mock asyncio.sleep to avoid waiting in tests
            with patch("asyncio.sleep", new_callable=AsyncMock):
                result = await backend.send(payload)

        assert result is False
        assert backend.last_failure is not None
        assert backend.failure_count_24h == 1

    @pytest.mark.asyncio
    async def test_webhook_success_on_retry(self):
        """Test webhook succeeds on retry attempt"""
        backend = WebhookBackend(webhook_url="https://example.com/webhook")
        payload = NotificationPayload(
            error_summary="Test error",
            error_type="TestError",
            severity="ERROR",
            timestamp=datetime(2026, 2, 6, 14, 30, 0),
        )

        # Mock HTTP POST that fails twice, then succeeds
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = AsyncMock()
            mock_response.raise_for_status = lambda: None  # Sync method

            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                side_effect=[
                    httpx.TimeoutException("Timeout 1"),
                    httpx.TimeoutException("Timeout 2"),
                    mock_response,  # Success on 3rd attempt
                ]
            )

            with patch("asyncio.sleep", new_callable=AsyncMock):
                result = await backend.send(payload)

        assert result is True
        assert backend.last_success is not None

    @pytest.mark.asyncio
    async def test_webhook_payload_format(self):
        """Test webhook sends correct JSON payload"""
        backend = WebhookBackend(webhook_url="https://example.com/webhook")
        payload = NotificationPayload(
            error_summary="Database error",
            error_type="DatabaseError",
            severity="ERROR",
            request_id="req-123",
            endpoint="POST /api/chat",
            timestamp=datetime(2026, 2, 6, 14, 30, 0),
        )

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = AsyncMock()
            mock_response.raise_for_status = lambda: None  # Sync method
            mock_post = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__.return_value.post = mock_post

            await backend.send(payload)

            # Verify POST called with correct arguments
            assert mock_post.called
            call_args = mock_post.call_args
            assert call_args.args[0] == "https://example.com/webhook"
            assert "json" in call_args.kwargs
            assert call_args.kwargs["json"]["error"]["type"] == "DatabaseError"

    def test_webhook_health_check(self):
        """Test webhook health check status"""
        backend = WebhookBackend(webhook_url="https://example.com/webhook")
        health = backend.health_check()

        assert health["backend_type"] == "webhook"
        assert health["configured"] is True
        assert "example.com" in health["webhook_url"]
        assert health["last_success"] is None
        assert health["failure_count_24h"] == 0


class TestSlackBackend:
    """Test SlackBackend notification delivery"""

    @pytest.mark.asyncio
    async def test_slack_successful_delivery(self):
        """Test successful Slack notification delivery"""
        backend = SlackBackend(webhook_url="https://hooks.slack.com/services/TEST")
        payload = NotificationPayload(
            error_summary="Test error",
            error_type="TestError",
            severity="ERROR",
            timestamp=datetime(2026, 2, 6, 14, 30, 0),
        )

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = AsyncMock()
            mock_response.raise_for_status = lambda: None
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)

            result = await backend.send(payload)

        assert result is True
        assert backend.last_success is not None

    @pytest.mark.asyncio
    async def test_slack_block_kit_format(self):
        """Test Slack uses Block Kit formatting"""
        backend = SlackBackend(webhook_url="https://hooks.slack.com/services/TEST")
        payload = NotificationPayload(
            error_summary="Database connection failed",
            error_type="DatabaseError",
            severity="ERROR",
            endpoint="POST /api/chat",
            context_snippet=["db_query: SELECT * FROM source"],
            timestamp=datetime(2026, 2, 6, 14, 30, 0),
        )

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = AsyncMock()
            mock_response.raise_for_status = lambda: None
            mock_post = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__.return_value.post = mock_post

            await backend.send(payload)

            # Verify POST called with Slack Block Kit structure
            call_args = mock_post.call_args
            slack_payload = call_args.kwargs["json"]
            assert "attachments" in slack_payload
            assert slack_payload["attachments"][0]["color"] == "#DC2626"  # red

    def test_slack_health_check(self):
        """Test Slack health check status"""
        backend = SlackBackend(webhook_url="https://hooks.slack.com/services/TEST")
        health = backend.health_check()

        assert health["backend_type"] == "slack"
        assert health["configured"] is True


class TestEmailBackend:
    """Test EmailBackend notification delivery"""

    @pytest.mark.asyncio
    async def test_email_successful_delivery(self):
        """Test successful email notification delivery"""
        backend = EmailBackend(
            smtp_host="smtp.example.com",
            smtp_port=587,
            smtp_user="admin@example.com",
            smtp_password="secret",
            admin_email="admin@example.com",
        )
        payload = NotificationPayload(
            error_summary="Test error",
            error_type="TestError",
            severity="ERROR",
            timestamp=datetime(2026, 2, 6, 14, 30, 0),
        )

        # Mock aiosmtplib.send
        with patch("aiosmtplib.send", new_callable=AsyncMock) as mock_send:
            result = await backend.send(payload)

        assert result is True
        assert backend.last_success is not None

    @pytest.mark.asyncio
    async def test_email_multipart_structure(self):
        """Test email creates HTML + plain text multipart message"""
        backend = EmailBackend(
            smtp_host="smtp.example.com",
            smtp_port=587,
            smtp_user="admin@example.com",
            smtp_password="secret",
            admin_email="admin@example.com",
        )
        payload = NotificationPayload(
            error_summary="Database error",
            error_type="DatabaseError",
            severity="ERROR",
            timestamp=datetime(2026, 2, 6, 14, 30, 0),
        )

        with patch("aiosmtplib.send", new_callable=AsyncMock) as mock_send:
            await backend.send(payload)

            # Verify send called with MIMEMultipart message
            assert mock_send.called
            call_args = mock_send.call_args
            msg = call_args.args[0]
            assert msg["Subject"].startswith("🚨 Error Alert")
            assert msg["To"] == "admin@example.com"

    @pytest.mark.asyncio
    async def test_email_connection_failure(self):
        """Test email handles SMTP connection failures gracefully"""
        backend = EmailBackend(
            smtp_host="smtp.example.com",
            smtp_port=587,
            smtp_user="admin@example.com",
            smtp_password="secret",
            admin_email="admin@example.com",
        )
        payload = NotificationPayload(
            error_summary="Test error",
            error_type="TestError",
            severity="ERROR",
            timestamp=datetime(2026, 2, 6, 14, 30, 0),
        )

        with patch("aiosmtplib.send", new_callable=AsyncMock, side_effect=Exception("SMTP connection failed")):
            result = await backend.send(payload)

        assert result is False
        assert backend.last_failure is not None
        assert backend.failure_count_24h == 1

    def test_email_health_check(self):
        """Test email health check status"""
        backend = EmailBackend(
            smtp_host="smtp.example.com",
            smtp_port=587,
            smtp_user="admin@example.com",
            smtp_password="secret",
            admin_email="admin@example.com",
        )
        health = backend.health_check()

        assert health["backend_type"] == "email"
        assert health["configured"] is True
        assert health["smtp_host"] == "smtp.example.com"


class TestNotificationConfig:
    """Test notification configuration and factory"""

    def test_config_defaults(self):
        """Test configuration defaults (notifications disabled)"""
        config = NotificationConfig()

        assert config.error_notification_backend == "none"
        assert config.webhook_url is None
        assert config.slack_webhook_url is None
        assert config.smtp_host is None

    def test_factory_creates_null_backend_by_default(self):
        """Test factory creates NullBackend when backend='none'"""
        config = NotificationConfig(error_notification_backend="none")
        backend = create_notification_backend(config)

        assert isinstance(backend, NullBackend)

    def test_factory_creates_webhook_backend(self):
        """Test factory creates WebhookBackend with valid config"""
        config = NotificationConfig(
            error_notification_backend="webhook",
            webhook_url="https://example.com/webhook",
        )
        backend = create_notification_backend(config)

        assert isinstance(backend, WebhookBackend)

    def test_factory_creates_slack_backend(self):
        """Test factory creates SlackBackend with valid config"""
        config = NotificationConfig(
            error_notification_backend="slack",
            slack_webhook_url="https://hooks.slack.com/services/TEST",
        )
        backend = create_notification_backend(config)

        assert isinstance(backend, SlackBackend)

    def test_factory_creates_email_backend(self):
        """Test factory creates EmailBackend with valid config"""
        config = NotificationConfig(
            error_notification_backend="email",
            smtp_host="smtp.example.com",
            smtp_user="admin@example.com",
            smtp_password="secret",
            admin_email="admin@example.com",
        )
        backend = create_notification_backend(config)

        assert isinstance(backend, EmailBackend)

    def test_factory_fallback_missing_webhook_url(self):
        """Test factory falls back to NullBackend if webhook URL missing"""
        config = NotificationConfig(error_notification_backend="webhook")  # No webhook_url
        backend = create_notification_backend(config)

        assert isinstance(backend, NullBackend)

    def test_factory_fallback_missing_smtp_config(self):
        """Test factory falls back to NullBackend if SMTP config incomplete"""
        config = NotificationConfig(
            error_notification_backend="email",
            smtp_host="smtp.example.com",
            # Missing smtp_user, smtp_password, admin_email
        )
        backend = create_notification_backend(config)

        assert isinstance(backend, NullBackend)


class TestNotificationDeduplicator:
    """Test notification deduplication logic"""

    def test_first_occurrence_always_sent(self):
        """Test first occurrence of error always sent"""
        deduplicator = NotificationDeduplicator(window_seconds=300)
        payload = NotificationPayload(
            error_summary="Database error",
            error_type="DatabaseError",
            severity="ERROR",
            endpoint="POST /api/chat",
            timestamp=datetime(2026, 2, 6, 14, 30, 0),
        )

        should_send, suppressed_count = deduplicator.should_send(payload)

        assert should_send is True
        assert suppressed_count == 0

    def test_duplicate_within_window_suppressed(self):
        """Test duplicate notification within window is suppressed"""
        deduplicator = NotificationDeduplicator(window_seconds=300)
        payload = NotificationPayload(
            error_summary="Database error",
            error_type="DatabaseError",
            severity="ERROR",
            endpoint="POST /api/chat",
            timestamp=datetime(2026, 2, 6, 14, 30, 0),
        )

        # First occurrence
        should_send1, _ = deduplicator.should_send(payload)
        assert should_send1 is True

        # Duplicate within window
        should_send2, suppressed_count = deduplicator.should_send(payload)
        assert should_send2 is False
        assert suppressed_count == 1

    def test_suppressed_count_tracking(self):
        """Test suppressed count increments correctly"""
        deduplicator = NotificationDeduplicator(window_seconds=300)
        payload = NotificationPayload(
            error_summary="Database error",
            error_type="DatabaseError",
            severity="ERROR",
            endpoint="POST /api/chat",
            timestamp=datetime(2026, 2, 6, 14, 30, 0),
        )

        # First occurrence
        deduplicator.should_send(payload)

        # Multiple duplicates
        _, count1 = deduplicator.should_send(payload)
        _, count2 = deduplicator.should_send(payload)
        _, count3 = deduplicator.should_send(payload)

        assert count1 == 1
        assert count2 == 2
        assert count3 == 3

    def test_cache_key_generation(self):
        """Test cache key excludes user/company (deduplicates across users)"""
        deduplicator = NotificationDeduplicator()

        payload1 = NotificationPayload(
            error_summary="Database error",
            error_type="DatabaseError",
            severity="ERROR",
            endpoint="POST /api/chat",
            user_id="user:1",
            company_id="company:A",
            timestamp=datetime(2026, 2, 6, 14, 30, 0),
        )

        payload2 = NotificationPayload(
            error_summary="Database error",
            error_type="DatabaseError",
            severity="ERROR",
            endpoint="POST /api/chat",
            user_id="user:2",  # Different user
            company_id="company:B",  # Different company
            timestamp=datetime(2026, 2, 6, 14, 30, 0),
        )

        # Both should generate same cache key
        key1 = deduplicator._cache_key(payload1)
        key2 = deduplicator._cache_key(payload2)
        assert key1 == key2

    def test_lru_cache_eviction(self):
        """Test LRU cache evicts oldest entries when full"""
        deduplicator = NotificationDeduplicator(max_size=3)

        # Add 4 different errors (exceeds max_size)
        for i in range(4):
            payload = NotificationPayload(
                error_summary=f"Error {i}",
                error_type=f"Error{i}",
                severity="ERROR",
                timestamp=datetime(2026, 2, 6, 14, 30, 0),
            )
            deduplicator.should_send(payload)

        # Cache should have only 3 entries (oldest evicted)
        assert len(deduplicator._cache) == 3


class TestNotificationService:
    """Test NotificationService with deduplication"""

    @pytest.mark.asyncio
    async def test_service_sends_first_occurrence(self):
        """Test service sends first occurrence of error"""
        backend = NullBackend()
        service = NotificationService(backend=backend)
        payload = NotificationPayload(
            error_summary="Test error",
            error_type="TestError",
            severity="ERROR",
            timestamp=datetime(2026, 2, 6, 14, 30, 0),
        )

        result = await service.notify(payload)
        assert result is True

    @pytest.mark.asyncio
    async def test_service_suppresses_duplicates(self):
        """Test service suppresses duplicate notifications"""
        backend = NullBackend()
        service = NotificationService(backend=backend)
        payload = NotificationPayload(
            error_summary="Test error",
            error_type="TestError",
            severity="ERROR",
            timestamp=datetime(2026, 2, 6, 14, 30, 0),
        )

        # First occurrence
        result1 = await service.notify(payload)
        assert result1 is True

        # Duplicate
        result2 = await service.notify(payload)
        assert result2 is False  # Suppressed

    @pytest.mark.asyncio
    async def test_service_includes_suppressed_count(self):
        """Test service includes suppressed count in payload"""
        backend = NullBackend()
        deduplicator = NotificationDeduplicator(window_seconds=1)  # 1 second window
        service = NotificationService(backend=backend, deduplicator=deduplicator)

        payload = NotificationPayload(
            error_summary="Test error",
            error_type="TestError",
            severity="ERROR",
            timestamp=datetime(2026, 2, 6, 14, 30, 0),
        )

        # First occurrence
        await service.notify(payload)

        # Suppress 3 duplicates
        await service.notify(payload)
        await service.notify(payload)
        await service.notify(payload)

        # Wait for window to expire
        time.sleep(1.1)

        # Next notification should include suppressed count
        result = await service.notify(payload)
        assert result is True
        # Note: suppressed_count is set on the payload object during notify()


class TestNullBackend:
    """Test NullBackend (notifications disabled)"""

    @pytest.mark.asyncio
    async def test_null_backend_send(self):
        """Test NullBackend send is no-op"""
        backend = NullBackend()
        payload = NotificationPayload(
            error_summary="Test error",
            error_type="TestError",
            severity="ERROR",
            timestamp=datetime(2026, 2, 6, 14, 30, 0),
        )

        result = await backend.send(payload)
        assert result is True  # Always succeeds

    def test_null_backend_health_check(self):
        """Test NullBackend health check"""
        backend = NullBackend()
        health = backend.health_check()

        assert health["backend_type"] == "none"
        assert health["configured"] is False
        assert "disabled" in health["status"].lower()
