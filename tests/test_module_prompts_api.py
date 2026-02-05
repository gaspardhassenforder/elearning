"""
Integration tests for Module Prompts API endpoints.

Story 3.4: AI Teacher Prompt Configuration
Tests GET and PUT endpoints with authentication and error handling.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(mock_admin_user):
    """Create test client with mocked authentication."""
    from api.main import app
    from api.auth import require_admin

    # Override the require_admin dependency to return our mock admin
    app.dependency_overrides[require_admin] = lambda: mock_admin_user

    client = TestClient(app)
    yield client

    # Clean up override
    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def mock_admin_user():
    """Mock admin user for authentication."""
    admin = MagicMock()
    admin.id = "user:admin1"
    admin.role = "admin"
    admin.username = "admin"
    return admin


class TestGetModulePrompt:
    """Test suite for GET /api/notebooks/{id}/prompt endpoint."""

    @patch("api.routers.module_prompts.module_prompt_service.get_module_prompt")
    def test_get_prompt_exists(self, mock_service, client):
        """Test GET returns prompt when exists."""

        # Mock service response
        mock_prompt = MagicMock()
        mock_prompt.id = "module_prompt:1"
        mock_prompt.notebook_id = "notebook:abc123"
        mock_prompt.system_prompt = "Focus on logistics applications"
        mock_prompt.updated_by = "user:admin1"
        mock_prompt.updated_at = "2026-02-05T10:00:00Z"
        mock_service.return_value = mock_prompt

        response = client.get("/api/notebooks/abc123/prompt")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "module_prompt:1"
        assert data["notebook_id"] == "notebook:abc123"
        assert data["system_prompt"] == "Focus on logistics applications"
        assert data["updated_by"] == "user:admin1"

    @patch("api.routers.module_prompts.module_prompt_service.get_module_prompt")
    
    def test_get_prompt_not_found(self, mock_service, client, mock_admin_user):
        """Test GET returns None when prompt doesn't exist."""
        # Mock authentication

        # Mock service response (None)
        mock_service.return_value = None

        response = client.get("/api/notebooks/abc123/prompt")

        assert response.status_code == 200
        assert response.json() is None

    @patch("api.routers.module_prompts.module_prompt_service.get_module_prompt")
    
    def test_get_prompt_notebook_not_found(self, mock_service, client, mock_admin_user):
        """Test GET returns 404 when notebook doesn't exist."""
        # Mock authentication

        # Mock service to raise HTTPException
        from fastapi import HTTPException
        mock_service.side_effect = HTTPException(status_code=404, detail="Notebook not found")

        response = client.get("/api/notebooks/nonexistent/prompt")

        assert response.status_code == 404


class TestUpdateModulePrompt:
    """Test suite for PUT /api/notebooks/{id}/prompt endpoint."""

    @patch("api.routers.module_prompts.module_prompt_service.update_module_prompt")
    
    def test_update_prompt_creates_new(self, mock_service, client, mock_admin_user):
        """Test PUT creates new prompt when none exists."""
        # Mock authentication

        # Mock service response (new prompt)
        mock_prompt = MagicMock()
        mock_prompt.id = "module_prompt:1"
        mock_prompt.notebook_id = "notebook:abc123"
        mock_prompt.system_prompt = "Focus on logistics"
        mock_prompt.updated_by = "user:admin1"
        mock_prompt.updated_at = "2026-02-05T10:00:00Z"
        mock_service.return_value = mock_prompt

        response = client.put(
            "/api/notebooks/abc123/prompt",
            json={"system_prompt": "Focus on logistics"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "module_prompt:1"
        assert data["system_prompt"] == "Focus on logistics"
        assert data["updated_by"] == "user:admin1"

        # Verify service was called with correct params
        mock_service.assert_called_once()
        call_args = mock_service.call_args
        assert call_args[1]["notebook_id"] == "abc123"
        assert call_args[1]["system_prompt"] == "Focus on logistics"
        assert call_args[1]["updated_by"] == "user:admin1"

    @patch("api.routers.module_prompts.module_prompt_service.update_module_prompt")
    
    def test_update_prompt_updates_existing(self, mock_service, client, mock_admin_user):
        """Test PUT updates existing prompt."""
        # Mock authentication

        # Mock service response (updated prompt)
        mock_prompt = MagicMock()
        mock_prompt.id = "module_prompt:1"
        mock_prompt.notebook_id = "notebook:abc123"
        mock_prompt.system_prompt = "Updated focus on supply chain"
        mock_prompt.updated_by = "user:admin1"
        mock_prompt.updated_at = "2026-02-05T11:00:00Z"
        mock_service.return_value = mock_prompt

        response = client.put(
            "/api/notebooks/abc123/prompt",
            json={"system_prompt": "Updated focus on supply chain"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["system_prompt"] == "Updated focus on supply chain"

    @patch("api.routers.module_prompts.module_prompt_service.update_module_prompt")
    
    def test_update_prompt_with_none(self, mock_service, client, mock_admin_user):
        """Test PUT with None system_prompt clears the prompt."""
        # Mock authentication

        # Mock service response (cleared prompt)
        mock_prompt = MagicMock()
        mock_prompt.id = "module_prompt:1"
        mock_prompt.notebook_id = "notebook:abc123"
        mock_prompt.system_prompt = None
        mock_prompt.updated_by = "user:admin1"
        mock_prompt.updated_at = "2026-02-05T11:00:00Z"
        mock_service.return_value = mock_prompt

        response = client.put(
            "/api/notebooks/abc123/prompt",
            json={"system_prompt": None}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["system_prompt"] is None

        # Verify service was called with None
        mock_service.assert_called_once()
        call_args = mock_service.call_args
        assert call_args[1]["system_prompt"] is None

    @patch("api.routers.module_prompts.module_prompt_service.update_module_prompt")
    
    def test_update_prompt_notebook_not_found(self, mock_service, client, mock_admin_user):
        """Test PUT returns 404 when notebook doesn't exist."""
        # Mock authentication

        # Mock service to raise HTTPException
        from fastapi import HTTPException
        mock_service.side_effect = HTTPException(status_code=404, detail="Notebook not found")

        response = client.put(
            "/api/notebooks/nonexistent/prompt",
            json={"system_prompt": "Test"}
        )

        assert response.status_code == 404

    @patch("api.routers.module_prompts.module_prompt_service.update_module_prompt")
    
    def test_update_prompt_database_error(self, mock_service, client, mock_admin_user):
        """Test PUT returns 500 on database error."""
        # Mock authentication

        # Mock service to raise HTTPException
        from fastapi import HTTPException
        mock_service.side_effect = HTTPException(status_code=500, detail="Database error")

        response = client.put(
            "/api/notebooks/abc123/prompt",
            json={"system_prompt": "Test"}
        )

        assert response.status_code == 500


class TestAuthenticationRequired:
    """Test suite for authentication requirements."""

    def test_endpoints_protected_by_admin_dependency(self):
        """Test that endpoints use require_admin dependency."""
        from api.main import app
        from api.routers.module_prompts import router

        # Check that router has require_admin dependency
        assert len(router.dependencies) > 0
        # The test passes because the dependency is configured at router level
        # Individual tests work because we override the dependency in the fixture
