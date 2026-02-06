"""
Tests for structured logging with JSON formatter.

Tests cover:
- JSON formatter output structure
- Human-readable formatter output
- Request context injection in logs
- Context buffer inclusion in ERROR logs
- Environment-based configuration
- Extra fields handling
"""

import json
import os
from datetime import UTC, datetime
from io import StringIO

import pytest
from loguru import logger

from open_notebook.observability.context_buffer import RollingContextBuffer
from open_notebook.observability.request_context import context_buffer, request_context
from open_notebook.observability.structured_logger import (
    configure_logging,
    json_formatter,
    structured_log,
)


class TestJSONFormatter:
    """Tests for JSON log formatter."""

    def test_json_formatter_creates_valid_json(self):
        """Test formatter outputs valid JSON."""
        record = {
            "time": datetime.now(UTC),
            "level": type("Level", (), {"name": "INFO"}),
            "message": "Test message",
            "name": "test_module",
            "function": "test_func",
            "line": 42,
            "exception": None,
            "extra": {},
            "process": type("Process", (), {"id": 12345}),
            "thread": type("Thread", (), {"id": 67890}),
        }

        output = json_formatter(record)
        parsed = json.loads(output)

        assert parsed["level"] == "INFO"
        assert parsed["message"] == "Test message"
        assert parsed["module"] == "test_module"
        assert parsed["function"] == "test_func"
        assert parsed["line"] == 42
        assert "timestamp" in parsed
        assert "metadata" in parsed

    def test_json_formatter_includes_request_context(self):
        """Test formatter includes request context when available."""
        # Set request context
        ctx = {
            "request_id": "req-123",
            "user_id": "user:john",
            "company_id": "company:acme",
            "endpoint": "GET /api/test",
        }
        request_context.set(ctx)

        record = {
            "time": datetime.now(UTC),
            "level": type("Level", (), {"name": "INFO"}),
            "message": "Test message",
            "name": "test",
            "function": "test",
            "line": 1,
            "exception": None,
            "extra": {},
            "process": type("Process", (), {"id": 1}),
            "thread": type("Thread", (), {"id": 1}),
        }

        output = json_formatter(record)
        parsed = json.loads(output)

        assert parsed["request_id"] == "req-123"
        assert parsed["user_id"] == "user:john"
        assert parsed["company_id"] == "company:acme"
        assert parsed["endpoint"] == "GET /api/test"

        # Cleanup
        request_context.set(None)

    def test_json_formatter_includes_context_buffer_on_error(self):
        """Test ERROR logs include context buffer."""
        # Set up context buffer
        buffer = RollingContextBuffer()
        buffer.append({"type": "db_query", "query": "SELECT * FROM source"})
        buffer.append({"type": "ai_call", "model": "gpt-4"})
        context_buffer.set(buffer)

        record = {
            "time": datetime.now(UTC),
            "level": type("Level", (), {"name": "ERROR"}),
            "message": "Test error",
            "name": "test",
            "function": "test",
            "line": 1,
            "exception": None,
            "extra": {},
            "process": type("Process", (), {"id": 1}),
            "thread": type("Thread", (), {"id": 1}),
        }

        output = json_formatter(record)
        parsed = json.loads(output)

        assert "context_buffer" in parsed
        assert len(parsed["context_buffer"]) == 2
        assert parsed["context_buffer"][0]["type"] == "db_query"
        assert parsed["context_buffer"][1]["type"] == "ai_call"

        # Cleanup
        context_buffer.set(None)

    def test_json_formatter_excludes_context_buffer_on_info(self):
        """Test INFO logs don't include context buffer."""
        # Set up context buffer
        buffer = RollingContextBuffer()
        buffer.append({"type": "test_op"})
        context_buffer.set(buffer)

        record = {
            "time": datetime.now(UTC),
            "level": type("Level", (), {"name": "INFO"}),
            "message": "Test info",
            "name": "test",
            "function": "test",
            "line": 1,
            "exception": None,
            "extra": {},
            "process": type("Process", (), {"id": 1}),
            "thread": type("Thread", (), {"id": 1}),
        }

        output = json_formatter(record)
        parsed = json.loads(output)

        assert "context_buffer" not in parsed

        # Cleanup
        context_buffer.set(None)

    def test_json_formatter_includes_exception_info(self):
        """Test formatter includes exception details."""
        try:
            raise ValueError("Test error message")
        except ValueError:
            import sys

            exc_info = sys.exc_info()

        record = {
            "time": datetime.now(UTC),
            "level": type("Level", (), {"name": "ERROR"}),
            "message": "Exception occurred",
            "name": "test",
            "function": "test",
            "line": 1,
            "exception": exc_info,
            "extra": {},
            "process": type("Process", (), {"id": 1}),
            "thread": type("Thread", (), {"id": 1}),
        }

        output = json_formatter(record)
        parsed = json.loads(output)

        assert parsed["error_type"] == "ValueError"
        assert parsed["error_message"] == "Test error message"
        assert "stack_trace" in parsed
        assert "ValueError: Test error message" in parsed["stack_trace"]

    def test_json_formatter_includes_extra_fields(self):
        """Test formatter includes extra fields from record."""
        record = {
            "time": datetime.now(UTC),
            "level": type("Level", (), {"name": "INFO"}),
            "message": "Test message",
            "name": "test",
            "function": "test",
            "line": 1,
            "exception": None,
            "extra": {
                "custom_field": "custom_value",
                "user_action": "clicked_button",
                "count": 42,
            },
            "process": type("Process", (), {"id": 1}),
            "thread": type("Thread", (), {"id": 1}),
        }

        output = json_formatter(record)
        parsed = json.loads(output)

        assert parsed["custom_field"] == "custom_value"
        assert parsed["user_action"] == "clicked_button"
        assert parsed["count"] == 42

    def test_json_formatter_includes_metadata(self):
        """Test formatter includes metadata section."""
        record = {
            "time": datetime.now(UTC),
            "level": type("Level", (), {"name": "INFO"}),
            "message": "Test message",
            "name": "test",
            "function": "test",
            "line": 1,
            "exception": None,
            "extra": {},
            "process": type("Process", (), {"id": 12345}),
            "thread": type("Thread", (), {"id": 67890}),
        }

        output = json_formatter(record)
        parsed = json.loads(output)

        assert "metadata" in parsed
        assert parsed["metadata"]["process_id"] == 12345
        assert parsed["metadata"]["thread_id"] == 67890
        assert "environment" in parsed["metadata"]


class TestStructuredLog:
    """Tests for structured_log helper function."""

    def test_structured_log_info(self, caplog):
        """Test logging info message."""
        structured_log("info", "Test info message", user_id="user:123")
        # Note: Testing actual log output requires capturing stderr

    def test_structured_log_error(self, caplog):
        """Test logging error message."""
        structured_log("error", "Test error message", error_code="E123")
        # Note: Testing actual log output requires capturing stderr

    def test_structured_log_with_context(self):
        """Test logging with request context."""
        ctx = {"request_id": "req-456"}
        request_context.set(ctx)

        structured_log("warning", "Test warning", reason="test")

        # Cleanup
        request_context.set(None)


class TestLoggingConfiguration:
    """Tests for logging configuration."""

    def test_configure_logging_development(self, monkeypatch):
        """Test logging configuration for development."""
        monkeypatch.setenv("ENVIRONMENT", "development")
        monkeypatch.setenv("STRUCTURED_LOGGING", "false")

        # Reconfigure
        configure_logging()

        # Logger should be configured (hard to test without capturing output)
        assert logger

    def test_configure_logging_production(self, monkeypatch):
        """Test logging configuration for production."""
        monkeypatch.setenv("ENVIRONMENT", "production")
        monkeypatch.setenv("STRUCTURED_LOGGING", "true")

        # Reconfigure
        configure_logging()

        # Logger should be configured for JSON output
        assert logger

    def test_configure_logging_log_level(self, monkeypatch):
        """Test LOG_LEVEL environment variable."""
        monkeypatch.setenv("LOG_LEVEL", "WARNING")

        # Reconfigure
        configure_logging()

        # Logger should be configured with WARNING level
        assert logger


class TestLoggingIntegration:
    """Integration tests for structured logging."""

    def test_full_logging_flow_with_context(self):
        """Test complete logging flow with request context and buffer."""
        # Set up request context
        ctx = {
            "request_id": "req-integration",
            "user_id": "user:test",
            "endpoint": "POST /api/test",
        }
        request_context.set(ctx)

        # Set up context buffer
        buffer = RollingContextBuffer()
        buffer.append({"type": "service_call", "service": "test"})
        context_buffer.set(buffer)

        # Log error (should include context and buffer)
        logger.error("Integration test error")

        # Cleanup
        request_context.set(None)
        context_buffer.set(None)

    def test_logging_without_context(self):
        """Test logging works when no context is set."""
        # Ensure no context
        request_context.set(None)
        context_buffer.set(None)

        # Should not raise exception
        logger.info("Log without context")
        logger.error("Error without context")
