"""
Tests for database and service instrumentation.

Tests cover:
- DB query logging with timing
- Service call logging
- Graph invocation logging
- External API call logging
- Parameter sanitization
"""

import pytest

from open_notebook.observability.context_buffer import RollingContextBuffer
from open_notebook.observability.db_instrumentation import (
    log_db_query,
    log_external_api_call,
    log_graph_invocation,
    log_service_call,
)
from open_notebook.observability.request_context import context_buffer


class TestDBInstrumentation:
    """Tests for database query logging."""

    def test_log_db_query_basic(self):
        """Test basic DB query logging."""
        buffer = RollingContextBuffer()
        context_buffer.set(buffer)

        log_db_query(
            "SELECT * FROM notebook WHERE id = $id",
            {"id": "notebook:123"},
            result_count=5,
            duration_ms=45.3,
        )

        stored_buffer = context_buffer.get()
        operations = stored_buffer.peek()

        assert len(operations) == 1
        assert operations[0]["type"] == "db_query"
        assert "SELECT * FROM notebook" in operations[0]["details"]["query"]
        assert operations[0]["details"]["param_id"] == "notebook:123"  # Flattened with param_ prefix
        assert operations[0]["details"]["result_count"] == 5
        assert operations[0]["duration_ms"] == 45.3

        # Cleanup
        context_buffer.set(None)

    def test_log_db_query_sanitizes_sensitive_params(self):
        """Test sensitive parameters are redacted."""
        buffer = RollingContextBuffer()
        context_buffer.set(buffer)

        log_db_query(
            "UPDATE user SET password = $password WHERE id = $id",
            {"id": "user:123", "password": "secret123"},
        )

        stored_buffer = context_buffer.get()
        operations = stored_buffer.peek()

        assert operations[0]["details"]["param_password"] == "***REDACTED***"  # Flattened
        assert operations[0]["details"]["param_id"] == "user:123"

        # Cleanup
        context_buffer.set(None)

    def test_log_db_query_truncates_long_queries(self):
        """Test long queries are truncated."""
        buffer = RollingContextBuffer()
        context_buffer.set(buffer)

        long_query = "SELECT " + ", ".join([f"field_{i}" for i in range(200)])
        log_db_query(long_query)

        stored_buffer = context_buffer.get()
        operations = stored_buffer.peek()

        assert len(operations[0]["details"]["query"]) <= 500

        # Cleanup
        context_buffer.set(None)


class TestServiceInstrumentation:
    """Tests for service call logging."""

    def test_log_service_call(self):
        """Test service operation logging."""
        buffer = RollingContextBuffer()
        context_buffer.set(buffer)

        log_service_call(
            "learner_chat",
            "send_message",
            notebook_id="notebook:123",
            message_length=150,
        )

        stored_buffer = context_buffer.get()
        operations = stored_buffer.peek()

        assert len(operations) == 1
        assert operations[0]["type"] == "service_call"
        assert operations[0]["details"]["service"] == "learner_chat"
        assert operations[0]["details"]["operation"] == "send_message"
        assert operations[0]["details"]["notebook_id"] == "notebook:123"
        assert operations[0]["details"]["message_length"] == 150

        # Cleanup
        context_buffer.set(None)


class TestGraphInstrumentation:
    """Tests for graph invocation logging."""

    def test_log_graph_invocation(self):
        """Test LangGraph invocation logging."""
        buffer = RollingContextBuffer()
        context_buffer.set(buffer)

        log_graph_invocation(
            "chat",
            {"message": "Hello, how are you?", "user_id": "user:123"},
            notebook_id="notebook:456",
        )

        stored_buffer = context_buffer.get()
        operations = stored_buffer.peek()

        assert len(operations) == 1
        assert operations[0]["type"] == "graph_invocation"
        assert operations[0]["details"]["graph"] == "chat"
        assert operations[0]["details"]["input_message"] == "Hello, how are you?"  # Flattened with input_ prefix
        assert operations[0]["details"]["input_user_id"] == "user:123"
        assert operations[0]["details"]["notebook_id"] == "notebook:456"

        # Cleanup
        context_buffer.set(None)

    def test_log_graph_invocation_truncates_long_inputs(self):
        """Test long input strings are truncated."""
        buffer = RollingContextBuffer()
        context_buffer.set(buffer)

        long_message = "x" * 500
        log_graph_invocation("chat", {"message": long_message})

        stored_buffer = context_buffer.get()
        operations = stored_buffer.peek()

        assert len(operations[0]["details"]["input_message"]) == 200  # Flattened

        # Cleanup
        context_buffer.set(None)


class TestExternalAPIInstrumentation:
    """Tests for external API call logging."""

    def test_log_external_api_call(self):
        """Test external API call logging."""
        buffer = RollingContextBuffer()
        context_buffer.set(buffer)

        log_external_api_call(
            "openai",
            "chat_completion",
            duration_ms=1250.5,
            model="gpt-4",
            tokens=150,
        )

        stored_buffer = context_buffer.get()
        operations = stored_buffer.peek()

        assert len(operations) == 1
        assert operations[0]["type"] == "external_api_call"
        assert operations[0]["details"]["provider"] == "openai"
        assert operations[0]["details"]["operation"] == "chat_completion"
        assert operations[0]["details"]["model"] == "gpt-4"
        assert operations[0]["details"]["tokens"] == 150
        assert operations[0]["duration_ms"] == 1250.5

        # Cleanup
        context_buffer.set(None)


class TestInstrumentationIntegration:
    """Integration tests for combined instrumentation."""

    def test_multiple_operations_logged(self):
        """Test multiple operations are logged in order."""
        buffer = RollingContextBuffer()
        context_buffer.set(buffer)

        # Simulate a request flow
        log_service_call("learner_chat", "send_message", notebook_id="notebook:123")
        log_db_query("SELECT * FROM notebook WHERE id = $id", {"id": "notebook:123"})
        log_graph_invocation("chat", {"message": "Hello"})
        log_external_api_call("openai", "chat_completion", duration_ms=1200)

        stored_buffer = context_buffer.get()
        operations = stored_buffer.peek()

        assert len(operations) == 4
        assert operations[0]["type"] == "service_call"
        assert operations[1]["type"] == "db_query"
        assert operations[2]["type"] == "graph_invocation"
        assert operations[3]["type"] == "external_api_call"

        # Cleanup
        context_buffer.set(None)
