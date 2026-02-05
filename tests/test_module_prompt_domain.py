"""
Unit tests for ModulePrompt domain model.

Story 3.4: AI Teacher Prompt Configuration
Tests validation, business logic, and RecordID coercion.
"""

from unittest.mock import AsyncMock, patch

import pytest

from open_notebook.domain.module_prompt import ModulePrompt
from open_notebook.exceptions import DatabaseOperationError


class TestModulePromptValidation:
    """Test suite for ModulePrompt field validation."""

    def test_module_prompt_creation(self):
        """Test basic ModulePrompt creation with valid fields."""
        prompt = ModulePrompt(
            notebook_id="notebook:abc123",
            system_prompt="Focus on logistics applications",
            updated_by="user:admin1"
        )
        assert prompt.notebook_id == "notebook:abc123"
        assert prompt.system_prompt == "Focus on logistics applications"
        assert prompt.updated_by == "user:admin1"

    def test_module_prompt_optional_system_prompt(self):
        """Test system_prompt can be None (optional configuration)."""
        prompt = ModulePrompt(
            notebook_id="notebook:abc123",
            system_prompt=None,
            updated_by="user:admin1"
        )
        assert prompt.system_prompt is None

    def test_notebook_id_coercion(self):
        """Test notebook_id is coerced to RecordID format."""
        # Without prefix
        prompt1 = ModulePrompt(
            notebook_id="abc123",
            system_prompt="Test",
            updated_by="user:admin1"
        )
        assert prompt1.notebook_id == "notebook:abc123"

        # With prefix (no change)
        prompt2 = ModulePrompt(
            notebook_id="notebook:xyz789",
            system_prompt="Test",
            updated_by="user:admin1"
        )
        assert prompt2.notebook_id == "notebook:xyz789"

    def test_updated_by_coercion(self):
        """Test updated_by is coerced to user RecordID format."""
        # Without prefix
        prompt1 = ModulePrompt(
            notebook_id="notebook:abc123",
            system_prompt="Test",
            updated_by="admin1"
        )
        assert prompt1.updated_by == "user:admin1"

        # With prefix (no change)
        prompt2 = ModulePrompt(
            notebook_id="notebook:abc123",
            system_prompt="Test",
            updated_by="user:admin2"
        )
        assert prompt2.updated_by == "user:admin2"

    def test_needs_embedding_returns_false(self):
        """Test module prompts are not searchable."""
        prompt = ModulePrompt(
            notebook_id="notebook:abc123",
            system_prompt="Test",
            updated_by="user:admin1"
        )
        assert prompt.needs_embedding() is False


class TestModulePromptClassMethods:
    """Test suite for ModulePrompt class methods (database operations)."""

    @pytest.mark.asyncio
    async def test_get_by_notebook_found(self):
        """Test get_by_notebook returns prompt when exists."""
        mock_result = [{
            "id": "module_prompt:1",
            "notebook_id": "notebook:abc123",
            "system_prompt": "Focus on logistics",
            "updated_by": "user:admin1",
            "updated_at": "2026-02-05T10:00:00Z"
        }]

        with patch("open_notebook.domain.module_prompt.repo_query", new_callable=AsyncMock) as mock_query:
            mock_query.return_value = mock_result

            result = await ModulePrompt.get_by_notebook("notebook:abc123")

            assert result is not None
            assert isinstance(result, ModulePrompt)
            assert result.notebook_id == "notebook:abc123"
            assert result.system_prompt == "Focus on logistics"
            mock_query.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_by_notebook_not_found(self):
        """Test get_by_notebook returns None when no prompt exists."""
        with patch("open_notebook.domain.module_prompt.repo_query", new_callable=AsyncMock) as mock_query:
            mock_query.return_value = []

            result = await ModulePrompt.get_by_notebook("notebook:nonexistent")

            assert result is None
            mock_query.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_by_notebook_coerces_id(self):
        """Test get_by_notebook coerces notebook_id to RecordID format."""
        with patch("open_notebook.domain.module_prompt.repo_query", new_callable=AsyncMock) as mock_query:
            mock_query.return_value = []

            await ModulePrompt.get_by_notebook("abc123")

            # Check that query was called with coerced ID
            call_args = mock_query.call_args
            assert call_args[0][1]["notebook_id"] == "notebook:abc123"

    @pytest.mark.asyncio
    async def test_get_by_notebook_database_error(self):
        """Test get_by_notebook raises DatabaseOperationError on failure."""
        with patch("open_notebook.domain.module_prompt.repo_query", new_callable=AsyncMock) as mock_query:
            mock_query.side_effect = Exception("Database connection failed")

            with pytest.raises(DatabaseOperationError):
                await ModulePrompt.get_by_notebook("notebook:abc123")

    @pytest.mark.asyncio
    async def test_create_or_update_creates_new(self):
        """Test create_or_update creates prompt when none exists."""
        with patch("open_notebook.domain.module_prompt.ModulePrompt.get_by_notebook", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = None  # No existing prompt

            with patch("open_notebook.domain.module_prompt.ModulePrompt.save", new_callable=AsyncMock):
                result = await ModulePrompt.create_or_update(
                    notebook_id="notebook:abc123",
                    system_prompt="New prompt",
                    updated_by="user:admin1"
                )

                assert result.notebook_id == "notebook:abc123"
                assert result.system_prompt == "New prompt"
                assert result.updated_by == "user:admin1"
                mock_get.assert_called_once_with("notebook:abc123")

    @pytest.mark.asyncio
    async def test_create_or_update_updates_existing(self):
        """Test create_or_update updates prompt when exists."""
        existing_prompt = ModulePrompt(
            id="module_prompt:1",
            notebook_id="notebook:abc123",
            system_prompt="Old prompt",
            updated_by="user:admin1"
        )

        with patch("open_notebook.domain.module_prompt.ModulePrompt.get_by_notebook", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = existing_prompt

            with patch("open_notebook.domain.module_prompt.ModulePrompt.save", new_callable=AsyncMock):
                result = await ModulePrompt.create_or_update(
                    notebook_id="notebook:abc123",
                    system_prompt="Updated prompt",
                    updated_by="user:admin2"
                )

                assert result.id == "module_prompt:1"
                assert result.system_prompt == "Updated prompt"
                assert result.updated_by == "user:admin2"
                mock_get.assert_called_once_with("notebook:abc123")

    @pytest.mark.asyncio
    async def test_create_or_update_with_none_prompt(self):
        """Test create_or_update accepts None system_prompt (clears prompt)."""
        existing_prompt = ModulePrompt(
            id="module_prompt:1",
            notebook_id="notebook:abc123",
            system_prompt="Old prompt",
            updated_by="user:admin1"
        )

        with patch("open_notebook.domain.module_prompt.ModulePrompt.get_by_notebook", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = existing_prompt

            with patch("open_notebook.domain.module_prompt.ModulePrompt.save", new_callable=AsyncMock):
                result = await ModulePrompt.create_or_update(
                    notebook_id="notebook:abc123",
                    system_prompt=None,
                    updated_by="user:admin1"
                )

                assert result.system_prompt is None

    @pytest.mark.asyncio
    async def test_create_or_update_coerces_ids(self):
        """Test create_or_update coerces notebook_id and updated_by."""
        with patch("open_notebook.domain.module_prompt.ModulePrompt.get_by_notebook", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = None

            with patch("open_notebook.domain.module_prompt.ModulePrompt.save", new_callable=AsyncMock):
                result = await ModulePrompt.create_or_update(
                    notebook_id="abc123",
                    system_prompt="Test",
                    updated_by="admin1"
                )

                assert result.notebook_id == "notebook:abc123"
                assert result.updated_by == "user:admin1"

    @pytest.mark.asyncio
    async def test_delete_by_notebook_deletes_existing(self):
        """Test delete_by_notebook deletes prompt when exists."""
        existing_prompt = ModulePrompt(
            id="module_prompt:1",
            notebook_id="notebook:abc123",
            system_prompt="Test",
            updated_by="user:admin1"
        )

        with patch("open_notebook.domain.module_prompt.ModulePrompt.get_by_notebook", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = existing_prompt

            with patch("open_notebook.domain.module_prompt.repo_query", new_callable=AsyncMock) as mock_query:
                result = await ModulePrompt.delete_by_notebook("notebook:abc123")

                assert result is True
                mock_get.assert_called_once_with("notebook:abc123")
                mock_query.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_by_notebook_returns_false_when_not_found(self):
        """Test delete_by_notebook returns False when no prompt exists."""
        with patch("open_notebook.domain.module_prompt.ModulePrompt.get_by_notebook", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = None

            result = await ModulePrompt.delete_by_notebook("notebook:nonexistent")

            assert result is False
            mock_get.assert_called_once_with("notebook:nonexistent")

    @pytest.mark.asyncio
    async def test_delete_by_notebook_coerces_id(self):
        """Test delete_by_notebook coerces notebook_id to RecordID format."""
        with patch("open_notebook.domain.module_prompt.ModulePrompt.get_by_notebook", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = None

            await ModulePrompt.delete_by_notebook("abc123")

            # Check that get_by_notebook was called with coerced ID
            mock_get.assert_called_once_with("notebook:abc123")

    @pytest.mark.asyncio
    async def test_delete_by_notebook_database_error(self):
        """Test delete_by_notebook raises DatabaseOperationError on failure."""
        existing_prompt = ModulePrompt(
            id="module_prompt:1",
            notebook_id="notebook:abc123",
            system_prompt="Test",
            updated_by="user:admin1"
        )

        with patch("open_notebook.domain.module_prompt.ModulePrompt.get_by_notebook", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = existing_prompt

            with patch("open_notebook.domain.module_prompt.repo_query", new_callable=AsyncMock) as mock_query:
                mock_query.side_effect = Exception("Database error")

                with pytest.raises(DatabaseOperationError):
                    await ModulePrompt.delete_by_notebook("notebook:abc123")
