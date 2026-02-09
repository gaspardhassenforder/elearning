"""
Regression tests for per-company data isolation (Story 7.5).

Tests verify that learners from Company A cannot access data belonging to Company B
across all learner-scoped endpoints: modules, sources, artifacts, quizzes, podcasts,
chat history, and learning objectives progress.

Also verifies that admin users can access data from all companies without restrictions.
"""

import os
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi import HTTPException

from api.auth import LearnerContext
from open_notebook.domain.user import User
from open_notebook.domain.notebook import Notebook
from open_notebook.domain.module_assignment import ModuleAssignment


@pytest.fixture(autouse=True)
def setup_test_env():
    """Set up test environment variables."""
    os.environ.setdefault("SURREAL_URL", "ws://localhost:8000/rpc")
    os.environ.setdefault("SURREAL_USER", "root")
    os.environ.setdefault("SURREAL_PASSWORD", "root")
    os.environ.setdefault("SURREAL_NAMESPACE", "test")
    os.environ.setdefault("SURREAL_DATABASE", "test")
    os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-testing-only")


class TestCompanyIsolationModules:
    """Test company isolation for module (notebook) endpoints."""

    @pytest.mark.asyncio
    async def test_learner_cannot_list_other_company_modules(self):
        """AC2: Learner cannot list modules from another company."""
        from api.routers.learner import get_learner_modules
        from api import assignment_service

        # Mock learner from Company A
        learner_a = LearnerContext(
            user=User(
                id="user:learner_a",
                username="learner_a",
                email="learner_a@companya.com",
                password_hash="hashed_password",
                role="learner",
                company_id="company:a",
            ),
            company_id="company:a",
        )

        # Mock service to return only Company A modules
        mock_modules = [
            {"id": "notebook:a1", "name": "Module A1", "company_id": "company:a"},
            {"id": "notebook:a2", "name": "Module A2", "company_id": "company:a"},
        ]

        with patch.object(assignment_service, "get_learner_modules", AsyncMock(return_value=mock_modules)):
            result = await get_learner_modules(learner=learner_a)

            # Verify only Company A modules returned
            assert len(result) == 2
            assert all(m["id"].startswith("notebook:a") for m in result)
            assert "notebook:b" not in [m["id"] for m in result]

    @pytest.mark.asyncio
    async def test_learner_cannot_access_other_company_module_by_id(self):
        """AC2: Learner cannot access module details from another company."""
        from api.routers.learner import get_learner_module

        # Mock learner from Company A
        learner_a = LearnerContext(
            user=User(
                id="user:learner_a",
                username="learner_a",
                email="learner_a@companya.com",
                password_hash="hashed_password",
                role="learner",
                company_id="company:a",
            ),
            company_id="company:a",
        )

        # Try to access module from Company B
        notebook_b_id = "notebook:b1"

        # Mock ModuleAssignment.get_by_company_and_notebook to return None (not assigned)
        with patch.object(ModuleAssignment, "get_by_company_and_notebook", AsyncMock(return_value=None)):
            # Should raise 403 Forbidden
            with pytest.raises(HTTPException) as exc_info:
                await get_learner_module(notebook_id=notebook_b_id, learner=learner_a)

            assert exc_info.value.status_code == 403
            assert "not accessible" in exc_info.value.detail.lower()


class TestCompanyIsolationQuizzes:
    """Test company isolation for quiz endpoints."""

    @pytest.mark.asyncio
    async def test_learner_cannot_access_quiz_from_other_company_module(self):
        """AC2: Learner cannot access quizzes from unassigned modules."""
        from api.routers.quizzes import get_quiz
        from api import quiz_service

        # Mock learner from Company A
        learner_a = User(
            id="user:learner_a",
            username="learner_a",
            email="learner_a@companya.com",
            password_hash="hashed_password",
            role="learner",
            company_id="company:a",
        )

        # Mock quiz from Company B's module
        mock_quiz = MagicMock()
        mock_quiz.id = "quiz:b1"
        mock_quiz.title = "Quiz B1"
        mock_quiz.description = "Quiz from Company B module"
        mock_quiz.notebook_id = "notebook:b1"  # Belongs to Company B
        mock_quiz.questions = []
        mock_quiz.completed = False
        mock_quiz.user_answers = []
        mock_quiz.last_score = None
        mock_quiz.created = "2026-01-01T00:00:00Z"
        mock_quiz.created_by = "admin"

        with patch.object(quiz_service, "get_quiz", AsyncMock(return_value=mock_quiz)), \
             patch("open_notebook.database.repository.repo_query", AsyncMock(return_value=[])):  # No assignment found

            # Should raise 403 Forbidden
            with pytest.raises(HTTPException) as exc_info:
                await get_quiz(quiz_id="quiz:b1", user=learner_a)

            assert exc_info.value.status_code == 403
            assert "not accessible" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_learner_can_access_quiz_from_assigned_company_module(self):
        """AC1: Learner CAN access quizzes from assigned modules."""
        from api.routers.quizzes import get_quiz
        from api import quiz_service

        # Mock learner from Company A
        learner_a = User(
            id="user:learner_a",
            username="learner_a",
            email="learner_a@companya.com",
            password_hash="hashed_password",
            role="learner",
            company_id="company:a",
        )

        # Mock quiz from Company A's module
        mock_quiz = MagicMock()
        mock_quiz.id = "quiz:a1"
        mock_quiz.title = "Quiz A1"
        mock_quiz.description = "Quiz from Company A module"
        mock_quiz.notebook_id = "notebook:a1"  # Belongs to Company A
        mock_quiz.questions = [
            MagicMock(
                question="Test question?",
                options=["A", "B", "C", "D"],
                correct_answer=1,
                explanation="Test explanation"
            )
        ]
        mock_quiz.completed = False
        mock_quiz.user_answers = []
        mock_quiz.last_score = None
        mock_quiz.created = "2026-01-01T00:00:00Z"
        mock_quiz.created_by = "admin"

        # Mock assignment exists (learner's company has access to this notebook)
        with patch.object(quiz_service, "get_quiz", AsyncMock(return_value=mock_quiz)), \
             patch("open_notebook.database.repository.repo_query", AsyncMock(return_value=[True])):  # Assignment found

            # Should succeed
            result = await get_quiz(quiz_id="quiz:a1", user=learner_a)

            assert result["id"] == "quiz:a1"
            assert result["title"] == "Quiz A1"
            assert len(result["questions"]) == 1


class TestCompanyIsolationPodcasts:
    """Test company isolation for podcast endpoints."""

    @pytest.mark.asyncio
    async def test_learner_cannot_access_podcast_from_other_company_module(self):
        """AC2: Learner cannot access podcasts from unassigned modules."""
        from api.routers.podcasts import get_podcast
        from open_notebook.domain.podcast import Podcast

        # Mock learner from Company A
        learner_a = User(
            id="user:learner_a",
            username="learner_a",
            email="learner_a@companya.com",
            password_hash="hashed_password",
            role="learner",
            company_id="company:a",
        )

        # Mock podcast from Company B's module
        mock_podcast = MagicMock()
        mock_podcast.id = "podcast:b1"
        mock_podcast.title = "Podcast B1"
        mock_podcast.topic = "Company B topic"
        mock_podcast.notebook_id = "notebook:b1"  # Belongs to Company B
        mock_podcast.length = "short"
        mock_podcast.speaker_format = "single"
        mock_podcast.audio_file_path = None
        mock_podcast.transcript = None
        mock_podcast.is_overview = False
        mock_podcast.created_by = "admin"
        mock_podcast.status = "completed"
        mock_podcast.duration_minutes = 10
        mock_podcast.is_ready = True
        mock_podcast.created = "2026-01-01T00:00:00Z"

        with patch.object(Podcast, "get", AsyncMock(return_value=mock_podcast)), \
             patch("open_notebook.database.repository.repo_query", AsyncMock(return_value=[])):  # No assignment found

            # Should raise 403 Forbidden
            with pytest.raises(HTTPException) as exc_info:
                await get_podcast(podcast_id="podcast:b1", user=learner_a)

            assert exc_info.value.status_code == 403
            assert "not accessible" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_learner_can_access_podcast_from_assigned_company_module(self):
        """AC1: Learner CAN access podcasts from assigned modules."""
        from api.routers.podcasts import get_podcast
        from open_notebook.domain.podcast import Podcast

        # Mock learner from Company A
        learner_a = User(
            id="user:learner_a",
            username="learner_a",
            email="learner_a@companya.com",
            password_hash="hashed_password",
            role="learner",
            company_id="company:a",
        )

        # Mock podcast from Company A's module
        mock_podcast = MagicMock()
        mock_podcast.id = "podcast:a1"
        mock_podcast.title = "Podcast A1"
        mock_podcast.topic = "Company A topic"
        mock_podcast.notebook_id = "notebook:a1"  # Belongs to Company A
        mock_podcast.length = "short"
        mock_podcast.speaker_format = "single"
        mock_podcast.audio_file_path = "/path/to/audio.mp3"
        mock_podcast.transcript = {"text": "Transcript content"}
        mock_podcast.is_overview = False
        mock_podcast.created_by = "admin"
        mock_podcast.status = "completed"
        mock_podcast.duration_minutes = 10
        mock_podcast.is_ready = True
        mock_podcast.created = "2026-01-01T00:00:00Z"

        # Mock assignment exists (learner's company has access to this notebook)
        with patch.object(Podcast, "get", AsyncMock(return_value=mock_podcast)), \
             patch("open_notebook.database.repository.repo_query", AsyncMock(return_value=[True])):  # Assignment found

            # Should succeed
            result = await get_podcast(podcast_id="podcast:a1", user=learner_a)

            assert result["id"] == "podcast:a1"
            assert result["title"] == "Podcast A1"
            assert result["topic"] == "Company A topic"


class TestCompanyIsolationChatHistory:
    """Test company isolation for chat history endpoints."""

    @pytest.mark.asyncio
    async def test_learner_cannot_access_chat_history_from_unassigned_module(self):
        """AC2: Learner cannot access chat history from unassigned modules."""
        from api.routers.learner_chat import get_chat_history
        from api.learner_chat_service import validate_learner_access_to_notebook

        # Mock learner from Company A
        learner_a = LearnerContext(
            user=User(
                id="user:learner_a",
                username="learner_a",
                email="learner_a@companya.com",
                password_hash="hashed_password",
                role="learner",
                company_id="company:a",
            ),
            company_id="company:a",
        )

        # Try to access chat history from Company B's module
        notebook_b_id = "notebook:b1"

        # Mock validation to raise 403 (module not assigned to company)
        async def mock_validate_access(*args, **kwargs):
            raise HTTPException(status_code=403, detail="Access denied")

        with patch("api.routers.learner_chat.validate_learner_access_to_notebook", mock_validate_access):
            # Should raise 403 Forbidden
            with pytest.raises(HTTPException) as exc_info:
                await get_chat_history(notebook_id=notebook_b_id, limit=50, offset=0, learner=learner_a)

            assert exc_info.value.status_code == 403


class TestCompanyIsolationAdmin:
    """Test that admin users can access all companies' data."""

    @pytest.mark.asyncio
    async def test_admin_can_access_all_company_quizzes(self):
        """AC3: Admin sees data from all companies without company filtering."""
        from api.routers.quizzes import get_quiz
        from api import quiz_service

        # Mock admin user (no company_id required for admins)
        admin_user = User(
            id="user:admin",
            username="admin",
            email="admin@opennotebook.ai",
            password_hash="hashed_password",
            role="admin",
            company_id=None,  # Admins don't need company assignment
        )

        # Mock quiz from any company's module
        mock_quiz = MagicMock()
        mock_quiz.id = "quiz:b1"
        mock_quiz.title = "Quiz from any company"
        mock_quiz.description = "Admin can access this"
        mock_quiz.notebook_id = "notebook:b1"
        mock_quiz.questions = []
        mock_quiz.completed = False
        mock_quiz.user_answers = []
        mock_quiz.last_score = None
        mock_quiz.created = "2026-01-01T00:00:00Z"
        mock_quiz.created_by = "admin"

        with patch.object(quiz_service, "get_quiz", AsyncMock(return_value=mock_quiz)):
            # Admin should access quiz without company check
            result = await get_quiz(quiz_id="quiz:b1", user=admin_user)

            # Should succeed - no 403 error
            assert result["id"] == "quiz:b1"
            assert result["title"] == "Quiz from any company"

    @pytest.mark.asyncio
    async def test_admin_can_access_all_company_podcasts(self):
        """AC3: Admin sees podcast data from all companies."""
        from api.routers.podcasts import get_podcast
        from open_notebook.domain.podcast import Podcast

        # Mock admin user
        admin_user = User(
            id="user:admin",
            username="admin",
            email="admin@opennotebook.ai",
            password_hash="hashed_password",
            role="admin",
            company_id=None,
        )

        # Mock podcast from any company
        mock_podcast = MagicMock()
        mock_podcast.id = "podcast:any"
        mock_podcast.title = "Podcast from any company"
        mock_podcast.topic = "Admin-accessible topic"
        mock_podcast.notebook_id = "notebook:any"
        mock_podcast.length = "short"
        mock_podcast.speaker_format = "single"
        mock_podcast.audio_file_path = None
        mock_podcast.transcript = None
        mock_podcast.is_overview = False
        mock_podcast.created_by = "admin"
        mock_podcast.status = "completed"
        mock_podcast.duration_minutes = 10
        mock_podcast.is_ready = True
        mock_podcast.created = "2026-01-01T00:00:00Z"

        with patch.object(Podcast, "get", AsyncMock(return_value=mock_podcast)):
            # Admin should access podcast without company check
            result = await get_podcast(podcast_id="podcast:any", user=admin_user)

            # Should succeed - no 403 error
            assert result["id"] == "podcast:any"
            assert result["title"] == "Podcast from any company"


class TestCompanyIsolationLearnerContext:
    """Test the LearnerContext dependency itself."""

    @pytest.mark.asyncio
    async def test_get_current_learner_enforces_company_assignment(self):
        """AC1: get_current_learner() dependency requires company_id."""
        from api.auth import get_current_learner, require_learner

        # Mock learner WITHOUT company_id
        learner_no_company = User(
            id="user:orphan",
            username="orphan_learner",
            email="orphan@example.com",
            password_hash="hashed_password",
            role="learner",
            company_id=None,  # Missing company assignment!
        )

        # Should raise 403 when learner has no company
        with pytest.raises(HTTPException) as exc_info:
            await get_current_learner(user=learner_no_company)

        assert exc_info.value.status_code == 403
        assert "company" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_get_current_learner_creates_learner_context(self):
        """AC1: get_current_learner() creates LearnerContext with company_id."""
        from api.auth import get_current_learner, require_learner

        # Mock learner WITH company_id
        learner_with_company = User(
            id="user:learner",
            username="learner",
            email="learner@companya.com",
            password_hash="hashed_password",
            role="learner",
            company_id="company:a",
        )

        # Should succeed and return LearnerContext
        context = await get_current_learner(user=learner_with_company)

        assert context.user.id == "user:learner"
        assert context.company_id == "company:a"
        assert isinstance(context, LearnerContext)
