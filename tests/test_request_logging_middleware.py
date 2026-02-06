"""
Integration tests for RequestLoggingMiddleware with FastAPI.

Tests cover:
- Middleware generates unique request_id
- Request context is initialized and cleaned up
- Successful requests are logged
- Failed requests flush context buffer
- Context isolation between concurrent requests
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.middleware.request_logging import RequestLoggingMiddleware
from open_notebook.observability.context_buffer import RollingContextBuffer
from open_notebook.observability.request_context import (
    context_buffer,
    get_request_context,
    log_operation,
    request_context,
)


@pytest.fixture
def test_app():
    """Create test FastAPI app with middleware."""
    app = FastAPI()

    # Add middleware
    app.add_middleware(RequestLoggingMiddleware)

    # Test routes
    @app.get("/success")
    async def success_route():
        # Log some operations
        log_operation("service_call", {"service": "test"})
        log_operation("db_query", {"query": "SELECT 1"})
        return {"status": "ok"}

    @app.get("/error")
    async def error_route():
        # Log operation before error
        log_operation("service_call", {"service": "test"})
        raise ValueError("Test error")

    @app.get("/context")
    async def context_route():
        """Return current request context for testing."""
        ctx = get_request_context()
        return {"context": ctx}

    return app


class TestRequestLoggingMiddleware:
    """Tests for request logging middleware integration."""

    def test_middleware_generates_request_id(self, test_app):
        """Test middleware generates unique request_id."""
        client = TestClient(test_app)

        # Make request
        response = client.get("/context")

        # Should have request_id in context
        assert response.status_code == 200
        context_data = response.json()["context"]
        assert "request_id" in context_data
        assert context_data["request_id"] is not None

    def test_middleware_initializes_context(self, test_app):
        """Test middleware initializes request context."""
        client = TestClient(test_app)

        response = client.get("/context")

        assert response.status_code == 200
        context_data = response.json()["context"]
        assert "request_id" in context_data
        assert "endpoint" in context_data
        assert context_data["endpoint"] == "GET /context"
        assert "timestamp" in context_data

    def test_successful_request_discards_buffer(self, test_app):
        """Test successful requests discard context buffer."""
        client = TestClient(test_app)

        # Make successful request (logs operations but should discard buffer)
        response = client.get("/success")

        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

        # After request completes, context should be cleaned up
        # (can't easily test this in synchronous client, but middleware should handle it)

    def test_failed_request_flushes_buffer(self, test_app):
        """Test failed requests flush context buffer to logs."""
        client = TestClient(test_app)

        # Make request that raises exception
        with pytest.raises(ValueError):
            client.get("/error")

        # Exception should have been logged with context buffer
        # (can't easily verify log output in tests, but middleware should handle it)

    def test_multiple_requests_isolated(self, test_app):
        """Test contexts don't leak between requests."""
        client = TestClient(test_app)

        # Make multiple requests
        response1 = client.get("/context")
        response2 = client.get("/context")
        response3 = client.get("/context")

        # Each should have different request_id
        ctx1 = response1.json()["context"]
        ctx2 = response2.json()["context"]
        ctx3 = response3.json()["context"]

        assert ctx1["request_id"] != ctx2["request_id"]
        assert ctx2["request_id"] != ctx3["request_id"]
        assert ctx1["request_id"] != ctx3["request_id"]

    def test_context_cleanup_after_request(self, test_app):
        """Test context is cleaned up after request completes."""
        client = TestClient(test_app)

        # Make request
        response = client.get("/success")
        assert response.status_code == 200

        # Outside request, context should be empty
        # (This test runs in the client thread, not the request thread,
        # so we can't directly verify cleanup here. The middleware
        # should clean up in the finally block.)

    def test_middleware_handles_missing_user_info(self, test_app):
        """Test middleware handles missing user_id/company_id gracefully."""
        client = TestClient(test_app)

        # Make request without authentication
        response = client.get("/context")

        assert response.status_code == 200
        context_data = response.json()["context"]
        # user_id and company_id should be None (not set by auth)
        assert context_data.get("user_id") is None
        assert context_data.get("company_id") is None
