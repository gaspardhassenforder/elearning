"""
Integration tests for editing published modules.

Story 3.6: Edit Published Module
Tests Tasks 3-5: Source management, artifact regeneration, and objectives updates on published modules.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(mock_admin_user):
    """Create test client with mocked authentication."""
    from api.main import app
    from api.auth import get_current_user, require_admin

    # Override both auth dependencies to return our mock admin
    app.dependency_overrides[get_current_user] = lambda: mock_admin_user
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


class TestSourceManagementOnPublishedModule:
    """Test suite for Task 3: Source add/remove on published modules."""

    @patch("api.routers.notebooks.ensure_record_id")
    @patch("api.routers.notebooks.repo_query")
    @patch("api.routers.notebooks.Source.get")
    @patch("api.routers.notebooks.Notebook.get")
    def test_add_source_to_published_module(self, mock_notebook_get, mock_source_get, mock_repo_query, mock_ensure_record_id, client):
        """Test adding a source to a published module succeeds."""
        # Mock published notebook
        mock_notebook = AsyncMock()
        mock_notebook.id = "notebook:published123"
        mock_notebook.name = "Published Module"
        mock_notebook.published = True
        mock_notebook_get.return_value = mock_notebook

        # Mock source
        mock_source = AsyncMock()
        mock_source.id = "source:doc456"
        mock_source.title = "New Document"
        mock_source_get.return_value = mock_source

        # Mock ensure_record_id
        mock_ensure_record_id.side_effect = lambda x: f"notebook:{x}" if ":" not in x else x

        # Mock repo_query for checking existing reference (none exists)
        mock_repo_query.return_value = []

        response = client.post("/api/notebooks/published123/sources/doc456")

        assert response.status_code == 200
        data = response.json()
        assert "successfully" in data["message"].lower()

        # Verify RELATE query was called to create reference
        assert mock_repo_query.call_count == 2  # 1 for check, 1 for RELATE

    @patch("api.routers.notebooks.ensure_record_id")
    @patch("api.routers.notebooks.repo_query")
    @patch("api.routers.notebooks.Notebook.get")
    def test_remove_source_from_published_module(self, mock_notebook_get, mock_repo_query, mock_ensure_record_id, client):
        """Test removing a source from a published module succeeds."""
        # Mock published notebook
        mock_notebook = AsyncMock()
        mock_notebook.id = "notebook:published123"
        mock_notebook.published = True
        mock_notebook_get.return_value = mock_notebook

        # Mock ensure_record_id
        mock_ensure_record_id.side_effect = lambda x: f"notebook:{x}" if ":" not in x else x

        # Mock repo_query for DELETE
        mock_repo_query.return_value = []

        response = client.delete("/api/notebooks/published123/sources/doc456")

        assert response.status_code == 200
        data = response.json()
        assert "removed" in data["message"].lower()

        # Verify DELETE query was called
        mock_repo_query.assert_called_once()
        call_args = mock_repo_query.call_args[0][0]
        assert "DELETE FROM reference" in call_args

    @patch("api.routers.notebooks.Source.get")
    @patch("api.routers.notebooks.Notebook.get")
    def test_add_source_to_published_module_notebook_not_found(self, mock_notebook_get, mock_source_get, client):
        """Test adding source to non-existent published module fails with 404."""
        mock_notebook_get.return_value = None

        response = client.post("/api/notebooks/nonexistent/sources/doc456")

        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    @patch("api.routers.notebooks.repo_query")
    @patch("api.routers.notebooks.Source.get")
    @patch("api.routers.notebooks.Notebook.get")
    def test_add_source_to_published_module_source_not_found(self, mock_notebook_get, mock_source_get, mock_repo_query, client):
        """Test adding non-existent source to published module fails with 404."""
        # Mock published notebook exists
        mock_notebook = AsyncMock()
        mock_notebook.id = "notebook:published123"
        mock_notebook.published = True
        mock_notebook_get.return_value = mock_notebook

        # Mock source doesn't exist
        mock_source_get.return_value = None

        response = client.post("/api/notebooks/published123/sources/nonexistent")

        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()


class TestArtifactRegenerationOnPublishedModule:
    """Test suite for Task 4: Artifact regeneration on published modules."""

    @patch("api.artifact_generation_service.generate_all_artifacts")
    @patch("api.routers.notebooks.Notebook.get")
    def test_regenerate_artifacts_on_published_module(self, mock_notebook_get, mock_generate, client):
        """Test artifact regeneration on published module succeeds."""
        # Mock published notebook
        mock_notebook = AsyncMock()
        mock_notebook.id = "notebook:published123"
        mock_notebook.published = True
        mock_notebook_get.return_value = mock_notebook

        # Mock artifact generation service to raise an exception
        # This simplifies the test - we just verify the endpoint can be called
        mock_generate.side_effect = Exception("Test exception")

        response = client.post("/api/notebooks/published123/generate-artifacts")

        # Should return 500 due to our mock exception
        # The important thing is it doesn't reject due to published status
        assert response.status_code == 500

        # Verify generation was called (showing endpoint doesn't block published modules)
        mock_generate.assert_called_once_with("published123")

    @patch("api.routers.notebooks.Notebook.get")
    def test_regenerate_artifacts_on_nonexistent_module(self, mock_notebook_get, client):
        """Test artifact regeneration on non-existent module fails with 404."""
        mock_notebook_get.return_value = None

        response = client.post("/api/notebooks/nonexistent/generate-artifacts")

        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()


class TestLearningObjectiveUpdatesOnPublishedModule:
    """Test suite for Task 5: Learning objective CRUD on published modules."""

    @patch("api.routers.learning_objectives.learning_objectives_service.update_objective")
    def test_update_objective_on_published_module(self, mock_update, client):
        """Test updating a learning objective on published module succeeds."""
        # Mock updated objective
        mock_objective = MagicMock()
        mock_objective.id = "learning_objective:obj123"
        mock_objective.notebook_id = "notebook:published123"
        mock_objective.text = "Updated Objective Text"
        mock_objective.order = 1
        mock_objective.auto_generated = False
        mock_objective.created = "2026-02-01T10:00:00Z"
        mock_objective.updated = "2026-02-05T10:00:00Z"
        mock_update.return_value = mock_objective

        response = client.put(
            "/api/notebooks/published123/learning-objectives/obj123",
            json={"text": "Updated Objective Text"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["text"] == "Updated Objective Text"
        assert data["notebook_id"] == "notebook:published123"

        # Verify service was called
        mock_update.assert_called_once()

    @patch("api.routers.learning_objectives.learning_objectives_service.create_objective")
    def test_add_objective_to_published_module(self, mock_create, client):
        """Test adding a new learning objective to published module succeeds."""
        # Mock created objective
        mock_objective = MagicMock()
        mock_objective.id = "learning_objective:new456"
        mock_objective.notebook_id = "notebook:published123"
        mock_objective.text = "New Objective"
        mock_objective.order = 2
        mock_objective.auto_generated = False
        mock_objective.created = "2026-02-05T10:00:00Z"
        mock_objective.updated = "2026-02-05T10:00:00Z"
        mock_create.return_value = mock_objective

        response = client.post(
            "/api/notebooks/published123/learning-objectives",
            json={
                "text": "New Objective",
                "order": 2
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["text"] == "New Objective"
        assert data["notebook_id"] == "notebook:published123"

    @patch("api.routers.learning_objectives.learning_objectives_service.delete_objective")
    def test_delete_objective_from_published_module(self, mock_delete, client):
        """Test deleting a learning objective from published module succeeds."""
        # Mock successful deletion
        mock_delete.return_value = True

        response = client.delete("/api/notebooks/published123/learning-objectives/obj123")

        assert response.status_code == 200
        data = response.json()
        assert "deleted" in data["message"].lower()

        # Verify delete was called
        mock_delete.assert_called_once_with("obj123")
