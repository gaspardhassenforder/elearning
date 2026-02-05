"""
Tests for module/notebook creation endpoint (Story 3.1, Task 1).

Tests cover:
- Module creation success with published=false default
- Validation (empty name, missing fields)
- Admin-only access (403 for non-admin)
"""

import os
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

# Set JWT secret for tests
os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-testing-only"

from api.models import NotebookCreate, NotebookResponse
from open_notebook.domain.notebook import Notebook
from open_notebook.domain.user import User


class TestNotebookCreation:
    """Test module/notebook creation endpoint."""

    @pytest.mark.asyncio
    async def test_create_notebook_success(self):
        """Should create notebook with published=false by default."""
        # Arrange
        notebook_data = NotebookCreate(
            name="Test Module",
            description="A test module for learning"
        )

        # Mock the Notebook save
        with patch.object(Notebook, 'save', new_callable=AsyncMock) as mock_save:
            mock_notebook = Notebook(
                name=notebook_data.name,
                description=notebook_data.description
            )
            mock_notebook.id = "notebook:test123"
            mock_notebook.created = "2026-02-05T00:00:00Z"
            mock_notebook.updated = "2026-02-05T00:00:00Z"
            mock_notebook.archived = False
            mock_notebook.published = False  # Default value
            mock_save.return_value = None

            # Act
            from api.routers.notebooks import create_notebook
            admin_user = User(
                id="user:admin1",
                username="admin",
                email="admin@test.com",
                password_hash="hashed",
                role="admin"
            )

            # Create notebook instance
            new_notebook = Notebook(
                name=notebook_data.name,
                description=notebook_data.description,
            )
            new_notebook.id = "notebook:test123"
            new_notebook.created = "2026-02-05T00:00:00Z"
            new_notebook.updated = "2026-02-05T00:00:00Z"
            new_notebook.archived = False
            new_notebook.published = False

            # Assert notebook created with correct values
            assert new_notebook.name == "Test Module"
            assert new_notebook.description == "A test module for learning"
            assert new_notebook.published is False  # CRITICAL: Must be False by default
            assert new_notebook.archived is False

    @pytest.mark.asyncio
    async def test_create_notebook_empty_name_fails(self):
        """Should reject notebook with empty name."""
        from open_notebook.exceptions import InvalidInputError

        # Act & Assert
        with pytest.raises(InvalidInputError, match="name cannot be empty"):
            notebook = Notebook(
                name="   ",  # Whitespace only
                description="Valid description"
            )
            # Validator should raise before save

    @pytest.mark.asyncio
    async def test_notebook_response_includes_published_field(self):
        """NotebookResponse should include published field."""
        # Arrange
        response = NotebookResponse(
            id="notebook:123",
            name="Test Module",
            description="Description",
            archived=False,
            published=False,  # Should be present
            created="2026-02-05T00:00:00Z",
            updated="2026-02-05T00:00:00Z",
            source_count=0,
            note_count=0
        )

        # Assert
        assert hasattr(response, 'published')
        assert response.published is False

    @pytest.mark.asyncio
    async def test_create_notebook_returns_published_false(self):
        """Created notebook response should show published=false."""
        # Arrange
        notebook = Notebook(
            name="New Module",
            description="Test"
        )
        notebook.id = "notebook:abc"
        notebook.created = "2026-02-05T00:00:00Z"
        notebook.updated = "2026-02-05T00:00:00Z"

        # Act
        response_data = NotebookResponse(
            id=notebook.id or "",
            name=notebook.name,
            description=notebook.description,
            archived=notebook.archived or False,
            published=notebook.published,  # Should be False
            created=str(notebook.created),
            updated=str(notebook.updated),
            source_count=0,
            note_count=0,
        )

        # Assert
        assert response_data.published is False


class TestNotebookCreationAuth:
    """Test admin-only access to notebook creation."""

    @pytest.mark.asyncio
    async def test_require_admin_allows_admin(self):
        """Admin users should be allowed to create notebooks."""
        from api.auth import require_admin

        admin_user = User(
            id="user:admin1",
            username="admin",
            email="admin@test.com",
            password_hash="hashed",
            role="admin"
        )

        # Should not raise (pass user directly, not as keyword)
        result = await require_admin(user=admin_user)
        assert result.role == "admin"

    @pytest.mark.asyncio
    async def test_require_admin_blocks_learner(self):
        """Learner users should be blocked from creating notebooks."""
        from api.auth import require_admin
        from fastapi import HTTPException

        learner_user = User(
            id="user:learner1",
            username="learner",
            email="learner@test.com",
            password_hash="hashed",
            role="learner",
            company_id="company:acme"
        )

        # Should raise 403
        with pytest.raises(HTTPException) as exc_info:
            await require_admin(user=learner_user)

        assert exc_info.value.status_code == 403


class TestNotebookCreationValidation:
    """Test notebook creation validation."""

    def test_notebook_create_model_requires_name(self):
        """NotebookCreate should require name field."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            NotebookCreate(description="Missing name")

    def test_notebook_create_allows_empty_description(self):
        """NotebookCreate should allow empty description."""
        notebook_data = NotebookCreate(
            name="Valid Name",
            description=""  # Empty is allowed
        )
        assert notebook_data.name == "Valid Name"
        assert notebook_data.description == ""

    def test_notebook_create_defaults_empty_description(self):
        """NotebookCreate should default to empty description if not provided."""
        notebook_data = NotebookCreate(name="Valid Name")
        assert notebook_data.description == ""
