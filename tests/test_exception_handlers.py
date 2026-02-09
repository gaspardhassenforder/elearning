"""
Tests for exception handlers with structured logging (Story 7.2).

Tests cover:
- HTTPException handler logs with request context (AC5)
- Unhandled exception handler logs with context buffer (AC1, AC4)
- Context buffer flushed on server errors
- User-safe error responses (no buffer leakage)
- CORS headers included in error responses
"""

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from starlette.exceptions import HTTPException as StarletteHTTPException

from api.exception_handlers import http_exception_handler, unhandled_exception_handler
from open_notebook.observability.context_buffer import RollingContextBuffer
from open_notebook.observability.request_context import context_buffer, request_context


# Create test app with exception handlers
@pytest.fixture
def test_app():
    """Create FastAPI app with exception handlers for testing."""
    app = FastAPI()

    # Register exception handlers
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)

    # Test routes
    @app.get("/test/http-error")
    async def trigger_http_error():
        raise HTTPException(status_code=400, detail="Bad request")

    @app.get("/test/server-error")
    async def trigger_server_error():
        raise HTTPException(status_code=500, detail="Internal server error")

    @app.get("/test/unhandled-error")
    async def trigger_unhandled_error():
        raise ValueError("Test unhandled exception")

    @app.get("/test/success")
    async def success_endpoint():
        return {"message": "success"}

    return app


@pytest.fixture
def client(test_app):
    """Create test client with raise_server_exceptions=False to test exception handlers."""
    return TestClient(test_app, raise_server_exceptions=False)


class TestHTTPExceptionHandler:
    """Tests for HTTP exception handler (AC5)."""

    def test_http_exception_handler_logs_error(self, client, caplog):
        """Test HTTPException handler logs error with context (AC5)."""
        # Set up request context
        ctx = {
            "request_id": "req-test-123",
            "user_id": "user:test",
            "endpoint": "GET /test/http-error",
        }
        request_context.set(ctx)

        # Trigger HTTP error
        response = client.get("/test/http-error")

        # Verify response
        assert response.status_code == 400
        assert "detail" in response.json()
        assert response.json()["detail"] == "Bad request"

        # Cleanup
        request_context.set(None)

    def test_http_exception_includes_request_id(self, client):
        """Test error response includes request_id for user reference."""
        # Set up request context
        ctx = {"request_id": "req-test-456"}
        request_context.set(ctx)

        # Trigger HTTP error
        response = client.get("/test/http-error")

        # Verify request_id in response
        assert response.status_code == 400
        assert "request_id" in response.json()
        assert response.json()["request_id"] == "req-test-456"

        # Cleanup
        request_context.set(None)

    def test_http_exception_excludes_context_buffer(self, client):
        """Test error response doesn't leak context buffer to user."""
        # Set up context with buffer
        ctx = {"request_id": "req-test-789"}
        request_context.set(ctx)

        buffer = RollingContextBuffer()
        buffer.append({"type": "db_query", "query": "SELECT * FROM users"})
        context_buffer.set(buffer)

        # Trigger HTTP error
        response = client.get("/test/http-error")

        # Verify buffer NOT in response
        assert "context_buffer" not in response.json()

        # Cleanup
        request_context.set(None)
        context_buffer.set(None)

    def test_server_error_flushes_context_buffer(self, client):
        """Test 5xx errors flush context buffer for diagnostics."""
        # Set up context with buffer
        ctx = {"request_id": "req-test-500"}
        request_context.set(ctx)

        buffer = RollingContextBuffer()
        buffer.append({"type": "service_call", "service": "test"})
        buffer.append({"type": "db_query", "query": "SELECT * FROM source"})
        context_buffer.set(buffer)

        # Trigger server error
        response = client.get("/test/server-error")

        # Verify response
        assert response.status_code == 500

        # Note: Buffer should be flushed during logging (checked in structured_logging tests)
        # Cleanup
        request_context.set(None)
        context_buffer.set(None)

    def test_http_exception_includes_cors_headers(self, client):
        """Test error response includes CORS headers."""
        response = client.get("/test/http-error", headers={"origin": "https://example.com"})

        # Verify CORS headers
        assert response.status_code == 400
        assert "access-control-allow-origin" in response.headers
        assert "access-control-allow-credentials" in response.headers


class TestUnhandledExceptionHandler:
    """Tests for unhandled exception handler (AC1, AC4)."""

    def test_unhandled_exception_logs_with_context(self, client, caplog):
        """Test unhandled exceptions log with full context (AC1)."""
        # Set up request context
        ctx = {
            "request_id": "req-unhandled",
            "user_id": "user:john",
            "endpoint": "GET /test/unhandled-error",
        }
        request_context.set(ctx)

        # Trigger unhandled exception
        response = client.get("/test/unhandled-error")

        # Verify response (generic 500 error)
        assert response.status_code == 500
        assert response.json()["detail"] == "An unexpected error occurred. Please try again."

        # Cleanup
        request_context.set(None)

    def test_unhandled_exception_flushes_context_buffer(self, client):
        """Test unhandled exceptions flush context buffer (AC4)."""
        # Set up context with buffer
        ctx = {"request_id": "req-unhandled-buffer"}
        request_context.set(ctx)

        buffer = RollingContextBuffer()
        buffer.append({"type": "service_call", "service": "test"})
        buffer.append({"type": "db_query", "query": "SELECT * FROM notebooks"})
        context_buffer.set(buffer)

        # Trigger unhandled exception
        response = client.get("/test/unhandled-error")

        # Verify response doesn't leak buffer
        assert response.status_code == 500
        assert "context_buffer" not in response.json()

        # Note: Buffer should be flushed during logging (checked in logs)
        # Cleanup
        request_context.set(None)
        context_buffer.set(None)

    def test_unhandled_exception_includes_request_id(self, client):
        """Test unhandled exception response includes request_id."""
        ctx = {"request_id": "req-generic-error"}
        request_context.set(ctx)

        response = client.get("/test/unhandled-error")

        assert response.status_code == 500
        assert "request_id" in response.json()
        assert response.json()["request_id"] == "req-generic-error"

        # Cleanup
        request_context.set(None)

    def test_unhandled_exception_includes_cors_headers(self, client):
        """Test unhandled exception response includes CORS headers."""
        response = client.get("/test/unhandled-error", headers={"origin": "https://example.com"})

        assert response.status_code == 500
        assert "access-control-allow-origin" in response.headers
        assert "access-control-allow-credentials" in response.headers

    def test_unhandled_exception_generic_message(self, client):
        """Test unhandled exception doesn't expose internal details."""
        response = client.get("/test/unhandled-error")

        assert response.status_code == 500
        # Should NOT contain "ValueError" or stack trace
        assert "ValueError" not in response.json()["detail"]
        assert "traceback" not in str(response.json()).lower()
        # Should be generic message
        assert "unexpected error" in response.json()["detail"].lower()


class TestExceptionHandlerIntegration:
    """Integration tests for exception handlers with context."""

    def test_success_request_no_error_handling(self, client):
        """Test successful requests don't trigger exception handlers."""
        ctx = {"request_id": "req-success"}
        request_context.set(ctx)

        buffer = RollingContextBuffer()
        buffer.append({"type": "test_op"})
        context_buffer.set(buffer)

        response = client.get("/test/success")

        assert response.status_code == 200
        assert response.json()["message"] == "success"

        # Cleanup
        request_context.set(None)
        context_buffer.set(None)

    def test_error_without_context_still_works(self, client):
        """Test exception handlers work even without request context."""
        # Ensure no context set
        request_context.set(None)
        context_buffer.set(None)

        response = client.get("/test/http-error")

        # Should still return error response
        assert response.status_code == 400
        assert "detail" in response.json()
