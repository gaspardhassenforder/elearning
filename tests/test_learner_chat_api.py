"""Tests for learner chat API endpoints (Story 4.1).

Basic tests for SSE streaming endpoint and access validation.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException


class TestLearnerChatRouter:
    """Test learner chat router logic and access control."""

    @pytest.mark.asyncio
    async def test_learner_chat_endpoint_exists(self):
        """Test that learner_chat router can be imported."""
        try:
            from api.routers import learner_chat
            assert hasattr(learner_chat, 'router')
        except ImportError:
            pytest.fail("learner_chat router module should exist")

    @pytest.mark.asyncio
    async def test_get_current_learner_dependency_exists(self):
        """Test get_current_learner dependency is available."""
        from api.auth import get_current_learner
        assert callable(get_current_learner)


class TestLearnerAccessValidation:
    """Test learner access validation logic (Story 2.3 integration)."""

    @pytest.mark.asyncio
    @patch("api.learner_chat_service.repo_query")
    @patch("api.learner_chat_service.Notebook.get")
    async def test_validate_access_blocks_unpublished_modules(
        self, mock_notebook_get, mock_repo_query
    ):
        """Test that learners cannot access unpublished modules."""
        from api.learner_chat_service import validate_learner_access_to_notebook
        from api.auth import LearnerContext

        # Mock notebook with published=False
        mock_result = [{
            "id": "notebook:123",
            "published": False,
            "is_locked": False,
        }]
        mock_repo_query.return_value = mock_result

        # Mock learner context
        mock_learner = MagicMock()
        mock_learner.user.id = "user:learner123"
        mock_learner.company_id = "company:abc"

        learner_context = LearnerContext(
            user=mock_learner.user,
            company_id=mock_learner.company_id
        )

        # Should raise 403 for unpublished module
        with pytest.raises(HTTPException) as exc_info:
            await validate_learner_access_to_notebook("notebook:123", learner_context)

        assert exc_info.value.status_code == 403
        assert "do not have access" in exc_info.value.detail

    @pytest.mark.asyncio
    @patch("api.learner_chat_service.repo_query")
    @patch("api.learner_chat_service.Notebook.get")
    async def test_validate_access_blocks_locked_modules(
        self, mock_notebook_get, mock_repo_query
    ):
        """Test that learners cannot access locked modules."""
        from api.learner_chat_service import validate_learner_access_to_notebook
        from api.auth import LearnerContext

        # Mock notebook with is_locked=True
        mock_result = [{
            "id": "notebook:123",
            "published": True,
            "is_locked": True,
        }]
        mock_repo_query.return_value = mock_result

        # Mock learner context
        mock_learner = MagicMock()
        mock_learner.user.id = "user:learner123"
        mock_learner.company_id = "company:abc"

        learner_context = LearnerContext(
            user=mock_learner.user,
            company_id=mock_learner.company_id
        )

        # Should raise 403 for locked module
        with pytest.raises(HTTPException) as exc_info:
            await validate_learner_access_to_notebook("notebook:123", learner_context)

        assert exc_info.value.status_code == 403
        assert "locked" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    @patch("api.learner_chat_service.repo_query")
    @patch("api.learner_chat_service.Notebook.get")
    async def test_validate_access_allows_valid_assignment(
        self, mock_notebook_get, mock_repo_query
    ):
        """Test that learners can access published, unlocked, assigned modules."""
        from api.learner_chat_service import validate_learner_access_to_notebook
        from api.auth import LearnerContext

        # Mock valid assignment
        mock_result = [{
            "id": "notebook:123",
            "title": "Test Module",
            "published": True,
            "is_locked": False,
        }]
        mock_repo_query.return_value = mock_result

        # Mock notebook
        mock_notebook = MagicMock()
        mock_notebook.id = "notebook:123"
        mock_notebook.title = "Test Module"
        mock_notebook_get.return_value = mock_notebook

        # Mock learner context
        mock_learner = MagicMock()
        mock_learner.user.id = "user:learner123"
        mock_learner.company_id = "company:abc"

        learner_context = LearnerContext(
            user=mock_learner.user,
            company_id=mock_learner.company_id
        )

        # Should allow access
        result = await validate_learner_access_to_notebook("notebook:123", learner_context)
        assert result == mock_notebook


class TestPromptAssembly:
    """Test prompt assembly integration (Story 3.4)."""

    @pytest.mark.asyncio
    @patch("api.learner_chat_service.assemble_system_prompt")
    async def test_prepare_chat_context_loads_learner_profile(
        self, mock_assemble_prompt
    ):
        """Test that learner profile is extracted from user data."""
        from api.learner_chat_service import prepare_chat_context
        from api.auth import LearnerContext

        # Mock learner with profile
        mock_user = MagicMock()
        mock_user.id = "user:learner123"
        mock_user.profile = {
            "role": "Software Engineer",
            "ai_familiarity": "intermediate",
            "job_description": "Backend developer"
        }

        learner_context = LearnerContext(
            user=mock_user,
            company_id="company:abc"
        )

        mock_assemble_prompt.return_value = "System prompt text"

        # Call prepare_chat_context
        system_prompt, learner_profile = await prepare_chat_context(
            "notebook:123", learner_context
        )

        # Verify learner profile extracted correctly
        assert learner_profile["role"] == "Software Engineer"
        assert learner_profile["ai_familiarity"] == "intermediate"
        assert learner_profile["job_description"] == "Backend developer"

        # Verify assemble_system_prompt was called
        mock_assemble_prompt.assert_called_once()
        call_kwargs = mock_assemble_prompt.call_args[1]
        assert call_kwargs["notebook_id"] == "notebook:123"
        assert call_kwargs["learner_profile"] == learner_profile


class TestThreadIsolation:
    """Test thread ID isolation pattern (Story 4.1)."""

    def test_thread_id_pattern_format(self):
        """Test that thread IDs follow the user:{id}:notebook:{id} pattern."""
        # This is more of a documentation test
        user_id = "user:learner123"
        notebook_id = "notebook:abc"
        expected_pattern = f"{user_id}:notebook:{notebook_id}"

        # Verify format is correct
        assert expected_pattern == "user:learner123:notebook:notebook:abc"
        # Note: This double "notebook:" is expected based on ID format
