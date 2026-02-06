"""
Tests for request context management using contextvars.

Tests cover:
- Context isolation between concurrent requests
- Context propagation across await boundaries
- Context cleanup after request completion
- Operation logging to rolling buffer
- Sensitive data sanitization
"""

import asyncio

import pytest

from open_notebook.observability.context_buffer import RollingContextBuffer
from open_notebook.observability.request_context import (
    context_buffer,
    get_request_context,
    log_operation,
    measure_operation,
    request_context,
    sanitize_details,
)


class TestRequestContext:
    """Tests for request context management."""

    def test_get_request_context_returns_empty_when_not_set(self):
        """Test get_request_context returns empty dict when no context set."""
        # Ensure context is clear
        request_context.set(None)

        result = get_request_context()

        assert result == {}

    def test_get_request_context_returns_set_context(self):
        """Test get_request_context returns the set context."""
        ctx = {
            "request_id": "test-123",
            "user_id": "user:john",
            "endpoint": "GET /api/test",
        }
        request_context.set(ctx)

        result = get_request_context()

        assert result == ctx

        # Cleanup
        request_context.set(None)

    @pytest.mark.asyncio
    async def test_context_propagates_across_await(self):
        """Test context survives async boundaries."""
        ctx = {"request_id": "req-456"}
        request_context.set(ctx)

        # Simulate async operation
        await asyncio.sleep(0.01)

        result = get_request_context()
        assert result["request_id"] == "req-456"

        # Cleanup
        request_context.set(None)

    @pytest.mark.asyncio
    async def test_context_isolation_between_concurrent_requests(self):
        """Test contexts don't leak between concurrent requests."""

        async def request_handler(request_id: str):
            """Simulate a request handler."""
            ctx = {"request_id": request_id, "user_id": f"user-{request_id}"}
            request_context.set(ctx)

            # Simulate some work
            await asyncio.sleep(0.01)

            # Verify context is still correct
            result = get_request_context()
            assert result["request_id"] == request_id
            assert result["user_id"] == f"user-{request_id}"

            # Cleanup
            request_context.set(None)

        # Run multiple concurrent requests
        await asyncio.gather(
            request_handler("req-1"),
            request_handler("req-2"),
            request_handler("req-3"),
        )

    def test_context_cleanup_after_request(self):
        """Test context is cleared after request completes."""
        request_context.set({"request_id": "req-789"})
        request_context.set(None)  # Cleanup

        result = get_request_context()
        assert result == {}


class TestLogOperation:
    """Tests for operation logging to rolling buffer."""

    def test_log_operation_appends_to_buffer(self):
        """Test operations are appended to buffer."""
        buffer = RollingContextBuffer(max_size=5)
        context_buffer.set(buffer)

        log_operation("db_query", {"query": "SELECT * FROM source"})
        log_operation("ai_call", {"model": "gpt-4"})

        # Get buffer from contextvar to see operations
        stored_buffer = context_buffer.get()
        operations = stored_buffer.peek()
        assert len(operations) == 2
        assert operations[0]["type"] == "db_query"
        assert operations[1]["type"] == "ai_call"

        # Cleanup
        context_buffer.set(None)

    def test_log_operation_no_op_when_no_buffer(self):
        """Test log_operation does nothing when no buffer set."""
        context_buffer.set(None)

        # Should not raise exception
        log_operation("test_op", {"detail": "value"})

    def test_log_operation_includes_timestamp(self):
        """Test operations include timestamp."""
        buffer = RollingContextBuffer()
        context_buffer.set(buffer)

        log_operation("test_op", {"detail": "value"})

        # Get buffer from contextvar
        stored_buffer = context_buffer.get()
        operations = stored_buffer.peek()
        assert "timestamp" in operations[0]
        assert operations[0]["timestamp"] is not None

        # Cleanup
        context_buffer.set(None)

    def test_log_operation_sanitizes_details(self):
        """Test operation details are sanitized."""
        buffer = RollingContextBuffer()
        context_buffer.set(buffer)

        log_operation(
            "db_query",
            {
                "query": "SELECT * FROM users",
                "password": "secret123",  # Should be redacted
                "long_string": "x" * 300,  # Should be truncated
            },
        )

        # Get buffer from contextvar
        stored_buffer = context_buffer.get()
        operations = stored_buffer.peek()
        assert operations[0]["details"]["password"] == "***REDACTED***"
        assert len(operations[0]["details"]["long_string"]) == 200

        # Cleanup
        context_buffer.set(None)


class TestSanitizeDetails:
    """Tests for sensitive data sanitization."""

    def test_sanitize_removes_sensitive_keys(self):
        """Test sensitive keys are redacted."""
        details = {
            "query": "SELECT * FROM users",
            "password": "secret123",
            "api_token": "abc123",
            "secret_key": "xyz789",
        }

        result = sanitize_details(details)

        assert result["query"] == "SELECT * FROM users"
        assert result["password"] == "***REDACTED***"
        assert result["api_token"] == "***REDACTED***"
        assert result["secret_key"] == "***REDACTED***"

    def test_sanitize_truncates_long_strings(self):
        """Test long strings are truncated to 200 characters."""
        details = {"long_text": "x" * 500}

        result = sanitize_details(details)

        assert len(result["long_text"]) == 200

    def test_sanitize_preserves_primitives(self):
        """Test primitive types are preserved."""
        details = {
            "count": 42,
            "ratio": 3.14,
            "enabled": True,
            "value": None,
        }

        result = sanitize_details(details)

        assert result == details

    def test_sanitize_converts_complex_types(self):
        """Test complex types are converted to strings."""
        details = {
            "obj": {"nested": "value"},
            "list": [1, 2, 3],
        }

        result = sanitize_details(details)

        assert isinstance(result["obj"], str)
        assert isinstance(result["list"], str)


class TestMeasureOperation:
    """Tests for operation timing measurement."""

    def test_measure_operation_logs_duration(self):
        """Test measure_operation logs operation with duration."""
        buffer = RollingContextBuffer()
        context_buffer.set(buffer)

        with measure_operation("test_op", {"detail": "value"}):
            pass  # Simulate work

        # Get buffer from contextvar
        stored_buffer = context_buffer.get()
        operations = stored_buffer.peek()
        assert len(operations) == 1
        assert operations[0]["type"] == "test_op"
        assert operations[0]["duration_ms"] is not None
        assert operations[0]["duration_ms"] >= 0

        # Cleanup
        context_buffer.set(None)

    def test_measure_operation_logs_error_on_exception(self):
        """Test measure_operation logs error when exception occurs."""
        buffer = RollingContextBuffer()
        context_buffer.set(buffer)

        try:
            with measure_operation("test_op", {"detail": "value"}):
                raise ValueError("Test error")
        except ValueError:
            pass

        # Get buffer from contextvar
        stored_buffer = context_buffer.get()
        operations = stored_buffer.peek()
        assert len(operations) == 1
        assert operations[0]["type"] == "test_op_error"
        assert "error" in operations[0]["details"]
        assert operations[0]["details"]["error"] == "Test error"

        # Cleanup
        context_buffer.set(None)


class TestContextBufferIntegration:
    """Integration tests for context buffer with request context."""

    @pytest.mark.asyncio
    async def test_full_request_flow(self):
        """Test complete request flow with context and buffer."""
        # Simulate request start
        ctx = {
            "request_id": "req-integration",
            "user_id": "user:test",
            "endpoint": "POST /api/test",
        }
        request_context.set(ctx)

        buffer = RollingContextBuffer(max_size=50)
        context_buffer.set(buffer)

        # Simulate operations
        log_operation("service_call", {"service": "test_service"})
        await asyncio.sleep(0.01)  # Simulate async work
        log_operation("db_query", {"query": "SELECT * FROM test"}, duration_ms=15.3)

        # Verify context is still correct
        assert get_request_context()["request_id"] == "req-integration"

        # Verify operations logged - get buffer from contextvar
        stored_buffer = context_buffer.get()
        operations = stored_buffer.peek()
        assert len(operations) == 2
        assert operations[0]["type"] == "service_call"
        assert operations[1]["type"] == "db_query"

        # Cleanup
        request_context.set(None)
        context_buffer.set(None)
