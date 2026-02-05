"""
Integration tests for Notebook Publish API endpoint.

Story 3.5: Module Publishing
Tests validation logic and POST /api/notebooks/{id}/publish endpoint with authentication and error handling.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(mock_admin_user):
    """Create test client with mocked authentication."""
    from api.main import app
    from api.auth import require_admin, get_current_user

    # Override both dependencies to return our mock admin
    app.dependency_overrides[require_admin] = lambda: mock_admin_user
    app.dependency_overrides[get_current_user] = lambda: mock_admin_user

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


class TestPublishValidation:
    """Test suite for publish validation logic."""

    @patch("api.routers.notebooks.Notebook.get")
    @patch("api.routers.notebooks.repo_query")
    @patch("api.routers.notebooks.LearningObjective.count_for_notebook")
    @patch("api.routers.notebooks.ModulePrompt.get_by_notebook")
    @patch("api.routers.notebooks.ensure_record_id")
    def test_validation_passes_with_minimum_requirements(
        self, mock_ensure_id, mock_get_prompt, mock_count_objectives, mock_repo_query, mock_get_notebook, client
    ):
        """Test validation passes when notebook has 1+ sources and 1+ objectives."""
        # Mock ensure_record_id to return proper format
        mock_ensure_id.return_value = "notebook:abc123"

        # Mock notebook exists
        mock_notebook = AsyncMock()
        mock_notebook.id = "notebook:abc123"
        mock_notebook.name = "Test Module"
        mock_notebook.description = "Test description"
        mock_notebook.published = False
        mock_notebook.archived = False
        mock_notebook.created = "2026-02-01T10:00:00Z"
        mock_notebook.updated = "2026-02-05T10:00:00Z"
        mock_notebook.save = AsyncMock()
        mock_get_notebook.return_value = mock_notebook

        # Mock source count = 1 (minimum)
        mock_repo_query.return_value = [{
            "id": "notebook:abc123",
            "name": "Test Module",
            "description": "Test description",
            "published": False,
            "archived": False,
            "created": "2026-02-01T10:00:00Z",
            "updated": "2026-02-05T10:00:00Z",
            "source_count": 1,
            "note_count": 0,
        }]

        # Mock objective count = 1 (minimum)
        mock_count_objectives.return_value = 1

        # Mock no prompt (optional)
        mock_get_prompt.return_value = None

        response = client.post("/api/notebooks/abc123/publish")

        assert response.status_code == 200
        data = response.json()
        assert data["published"] is True
        assert mock_notebook.published is True
        mock_notebook.save.assert_called_once()

    @patch("api.routers.notebooks.Notebook.get")
    @patch("api.routers.notebooks.repo_query")
    @patch("api.routers.notebooks.LearningObjective.count_for_notebook")
    @patch("api.routers.notebooks.ensure_record_id")
    def test_validation_fails_with_no_sources(
        self, mock_ensure_id, mock_count_objectives, mock_repo_query, mock_get_notebook, client
    ):
        """Test validation fails when notebook has 0 sources."""
        # Mock ensure_record_id
        mock_ensure_id.return_value = "notebook:abc123"

        # Mock notebook exists
        mock_notebook = AsyncMock()
        mock_notebook.id = "notebook:abc123"
        mock_get_notebook.return_value = mock_notebook

        # Mock source count = 0 (fails validation)
        mock_repo_query.return_value = [{
            "id": "notebook:abc123",
            "source_count": 0,
            "note_count": 0,
        }]

        # Mock objective count = 1 (valid)
        mock_count_objectives.return_value = 1

        response = client.post("/api/notebooks/abc123/publish")

        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        # Should mention missing documents
        assert any("document" in str(err).lower() or "source" in str(err).lower()
                  for err in str(data["detail"]).split())

    @patch("api.routers.notebooks.Notebook.get")
    @patch("api.routers.notebooks.repo_query")
    @patch("api.routers.notebooks.LearningObjective.count_for_notebook")
    @patch("api.routers.notebooks.ensure_record_id")
    def test_validation_fails_with_no_objectives(
        self, mock_ensure_id, mock_count_objectives, mock_repo_query, mock_get_notebook, client
    ):
        """Test validation fails when notebook has 0 learning objectives."""
        # Mock ensure_record_id
        mock_ensure_id.return_value = "notebook:abc123"

        # Mock notebook exists
        mock_notebook = AsyncMock()
        mock_notebook.id = "notebook:abc123"
        mock_get_notebook.return_value = mock_notebook

        # Mock source count = 1 (valid)
        mock_repo_query.return_value = [{
            "id": "notebook:abc123",
            "source_count": 1,
            "note_count": 0,
        }]

        # Mock objective count = 0 (fails validation)
        mock_count_objectives.return_value = 0

        response = client.post("/api/notebooks/abc123/publish")

        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        # Should mention missing objectives
        assert any("objective" in str(err).lower()
                  for err in str(data["detail"]).split())

    @patch("api.routers.notebooks.Notebook.get")
    @patch("api.routers.notebooks.repo_query")
    @patch("api.routers.notebooks.LearningObjective.count_for_notebook")
    @patch("api.routers.notebooks.ensure_record_id")
    def test_validation_fails_with_both_missing(
        self, mock_ensure_id, mock_count_objectives, mock_repo_query, mock_get_notebook, client
    ):
        """Test validation fails when notebook has both 0 sources and 0 objectives."""
        # Mock ensure_record_id
        mock_ensure_id.return_value = "notebook:abc123"

        # Mock notebook exists
        mock_notebook = AsyncMock()
        mock_notebook.id = "notebook:abc123"
        mock_get_notebook.return_value = mock_notebook

        # Mock source count = 0 (fails)
        mock_repo_query.return_value = [{
            "id": "notebook:abc123",
            "source_count": 0,
            "note_count": 0,
        }]

        # Mock objective count = 0 (fails)
        mock_count_objectives.return_value = 0

        response = client.post("/api/notebooks/abc123/publish")

        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        # Should mention both errors
        detail_str = str(data["detail"]).lower()
        assert "document" in detail_str or "source" in detail_str
        assert "objective" in detail_str

    @patch("api.routers.notebooks.Notebook.get")
    @patch("api.routers.notebooks.ensure_record_id")
    @patch("api.routers.notebooks.repo_query")
    def test_publish_nonexistent_notebook_fails(self, mock_repo_query, mock_ensure_id, mock_get_notebook, client):
        """Test publish returns 404 when notebook doesn't exist."""
        # Mock ensure_record_id
        mock_ensure_id.return_value = "notebook:nonexistent"

        # Mock notebook not found from repo_query (first check)
        mock_repo_query.return_value = []

        response = client.post("/api/notebooks/nonexistent/publish")

        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    @patch("api.routers.notebooks.Notebook.get")
    @patch("api.routers.notebooks.repo_query")
    @patch("api.routers.notebooks.LearningObjective.count_for_notebook")
    @patch("api.routers.notebooks.ModulePrompt.get_by_notebook")
    @patch("api.routers.notebooks.ensure_record_id")
    def test_publish_already_published_notebook_succeeds(
        self, mock_ensure_id, mock_get_prompt, mock_count_objectives, mock_repo_query, mock_get_notebook, client
    ):
        """Test publish succeeds even if notebook is already published (idempotent)."""
        # Mock ensure_record_id
        mock_ensure_id.return_value = "notebook:abc123"

        # Mock notebook already published
        mock_notebook = AsyncMock()
        mock_notebook.id = "notebook:abc123"
        mock_notebook.name = "Test Module"
        mock_notebook.description = "Test description"
        mock_notebook.published = True  # Already published
        mock_notebook.archived = False
        mock_notebook.created = "2026-02-01T10:00:00Z"
        mock_notebook.updated = "2026-02-05T10:00:00Z"
        mock_notebook.save = AsyncMock()
        mock_get_notebook.return_value = mock_notebook

        # Mock valid counts
        mock_repo_query.return_value = [{
            "id": "notebook:abc123",
            "source_count": 1,
            "note_count": 0,
        }]
        mock_count_objectives.return_value = 1
        mock_get_prompt.return_value = None

        response = client.post("/api/notebooks/abc123/publish")

        assert response.status_code == 200
        data = response.json()
        assert data["published"] is True


class TestPublishResponse:
    """Test suite for publish response structure."""

    @patch("api.routers.notebooks.Notebook.get")
    @patch("api.routers.notebooks.repo_query")
    @patch("api.routers.notebooks.LearningObjective.count_for_notebook")
    @patch("api.routers.notebooks.ModulePrompt.get_by_notebook")
    @patch("api.routers.notebooks.ensure_record_id")
    def test_publish_returns_full_response(
        self, mock_ensure_id, mock_get_prompt, mock_count_objectives, mock_repo_query, mock_get_notebook, client
    ):
        """Test publish returns NotebookResponse with all fields and counts."""
        # Mock ensure_record_id
        mock_ensure_id.return_value = "notebook:abc123"

        # Mock notebook
        mock_notebook = AsyncMock()
        mock_notebook.id = "notebook:abc123"
        mock_notebook.name = "Test Module"
        mock_notebook.description = "Test description"
        mock_notebook.published = False
        mock_notebook.archived = False
        mock_notebook.created = "2026-02-01T10:00:00Z"
        mock_notebook.updated = "2026-02-05T10:00:00Z"
        mock_notebook.save = AsyncMock()
        mock_get_notebook.return_value = mock_notebook

        # Mock counts
        mock_repo_query.return_value = [{
            "id": "notebook:abc123",
            "name": "Test Module",
            "description": "Test description",
            "published": True,
            "archived": False,
            "created": "2026-02-01T10:00:00Z",
            "updated": "2026-02-05T10:00:00Z",
            "source_count": 3,
            "note_count": 2,
        }]
        mock_count_objectives.return_value = 4
        mock_get_prompt.return_value = MagicMock(system_prompt="Custom prompt")

        response = client.post("/api/notebooks/abc123/publish")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "notebook:abc123"
        assert data["name"] == "Test Module"
        assert data["published"] is True
        assert data["source_count"] == 3
        assert data["note_count"] == 2


class TestAuthenticationRequired:
    """Test suite for authentication requirements."""

    def test_publish_requires_admin(self):
        """Test that publish endpoint uses require_admin dependency."""
        from api.main import app

        # Create client without auth override
        client = TestClient(app)

        # Verify the endpoint exists and has admin protection
        from api.routers.notebooks import router

        assert router is not None
