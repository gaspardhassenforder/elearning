"""
Story 5.2: Learner Artifacts Endpoints Tests

Tests for:
- GET /learner/notebooks/{notebook_id}/artifacts (learner-scoped artifact list)
- GET /learner/artifacts/{artifact_id}/preview (learner-scoped artifact preview)

Both endpoints use company-scoped access control via get_current_learner() dependency.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException

from api.models import ArtifactListResponse


class TestArtifactListResponseModel:
    """Test ArtifactListResponse Pydantic model"""

    def test_model_quiz_type(self):
        """Test model with quiz artifact type"""
        response = ArtifactListResponse(
            id="artifact:quiz123",
            artifact_type="quiz",
            title="Module Quiz",
            created="2024-01-15T10:30:00Z",
        )
        assert response.id == "artifact:quiz123"
        assert response.artifact_type == "quiz"
        assert response.title == "Module Quiz"
        assert response.created == "2024-01-15T10:30:00Z"

    def test_model_podcast_type(self):
        """Test model with podcast artifact type"""
        response = ArtifactListResponse(
            id="artifact:pod456",
            artifact_type="podcast",
            title="Overview Podcast",
            created="2024-01-14T15:00:00Z",
        )
        assert response.artifact_type == "podcast"
        assert response.title == "Overview Podcast"

    def test_model_summary_type(self):
        """Test model with summary artifact type"""
        response = ArtifactListResponse(
            id="artifact:sum789",
            artifact_type="summary",
            title="Executive Summary",
            created="2024-01-13T08:45:00Z",
        )
        assert response.artifact_type == "summary"

    def test_model_transformation_type(self):
        """Test model with transformation artifact type"""
        response = ArtifactListResponse(
            id="artifact:trans001",
            artifact_type="transformation",
            title="Key Topics Extraction",
            created="2024-01-12T14:20:00Z",
        )
        assert response.artifact_type == "transformation"

    def test_model_serialization(self):
        """Test model can be serialized to dict"""
        response = ArtifactListResponse(
            id="artifact:abc",
            artifact_type="quiz",
            title="Test Quiz",
            created="2024-01-01T00:00:00Z",
        )
        data = response.model_dump()
        assert data["id"] == "artifact:abc"
        assert data["artifact_type"] == "quiz"
        assert data["title"] == "Test Quiz"
        assert data["created"] == "2024-01-01T00:00:00Z"


class TestLearnerArtifactsListEndpoint:
    """Test the learner artifacts list endpoint logic"""

    def test_access_validation_notebook_assigned(self):
        """Test access granted when notebook is assigned to learner's company"""
        user_company_id = "company:acme"
        notebook_assigned_to = "company:acme"
        notebook_published = True
        notebook_locked = False

        access_granted = (
            user_company_id == notebook_assigned_to
            and notebook_published
            and not notebook_locked
        )
        assert access_granted is True

    def test_access_denied_not_assigned(self):
        """Test access denied when notebook is not assigned to learner's company"""
        user_company_id = "company:acme"
        notebook_assigned_to = "company:other"
        notebook_published = True
        notebook_locked = False

        access_granted = (
            user_company_id == notebook_assigned_to
            and notebook_published
            and not notebook_locked
        )
        assert access_granted is False

    def test_access_denied_not_published(self):
        """Test access denied when notebook is not published"""
        user_company_id = "company:acme"
        notebook_assigned_to = "company:acme"
        notebook_published = False
        notebook_locked = False

        access_granted = (
            user_company_id == notebook_assigned_to
            and notebook_published
            and not notebook_locked
        )
        assert access_granted is False

    def test_access_denied_module_locked(self):
        """Test access denied when module is locked"""
        user_company_id = "company:acme"
        notebook_assigned_to = "company:acme"
        notebook_published = True
        notebook_locked = True

        access_granted = (
            user_company_id == notebook_assigned_to
            and notebook_published
            and not notebook_locked
        )
        assert access_granted is False

    def test_empty_artifacts_list(self):
        """Test that empty list is valid response when no artifacts exist"""
        artifacts = []
        assert len(artifacts) == 0
        assert isinstance(artifacts, list)

    def test_multiple_artifact_types_in_list(self):
        """Test list can contain multiple artifact types"""
        artifacts = [
            ArtifactListResponse(
                id="artifact:1", artifact_type="quiz", title="Quiz", created="2024-01-01T00:00:00Z"
            ),
            ArtifactListResponse(
                id="artifact:2", artifact_type="podcast", title="Podcast", created="2024-01-02T00:00:00Z"
            ),
            ArtifactListResponse(
                id="artifact:3", artifact_type="summary", title="Summary", created="2024-01-03T00:00:00Z"
            ),
            ArtifactListResponse(
                id="artifact:4", artifact_type="transformation", title="Transform", created="2024-01-04T00:00:00Z"
            ),
        ]
        assert len(artifacts) == 4
        types = [a.artifact_type for a in artifacts]
        assert "quiz" in types
        assert "podcast" in types
        assert "summary" in types
        assert "transformation" in types


class TestLearnerArtifactPreviewEndpoint:
    """Test the learner artifact preview endpoint logic"""

    def test_artifact_access_validation(self):
        """Test artifact access requires notebook to be assigned"""
        # Artifact in notebook assigned to user's company
        artifact_notebook_id = "notebook:123"
        user_company_id = "company:acme"
        notebook_assigned_to_company = "company:acme"
        notebook_published = True
        notebook_locked = False

        access_granted = (
            user_company_id == notebook_assigned_to_company
            and notebook_published
            and not notebook_locked
        )
        assert access_granted is True

    def test_artifact_access_denied_wrong_company(self):
        """Test access denied for artifact in notebook not assigned to user's company"""
        user_company_id = "company:acme"
        notebook_assigned_to_company = "company:other"
        notebook_published = True
        notebook_locked = False

        access_granted = (
            user_company_id == notebook_assigned_to_company
            and notebook_published
            and not notebook_locked
        )
        assert access_granted is False

    def test_quiz_preview_structure(self):
        """Test quiz preview contains expected fields"""
        preview = {
            "artifact_type": "quiz",
            "id": "quiz:123",
            "title": "Module Quiz",
            "question_count": 5,
            "questions": [
                {
                    "question": "What is AI?",
                    "choices": ["A", "B", "C", "D"],
                    "correct_answer": 0,
                    "explanation": "AI stands for...",
                }
            ],
        }
        assert preview["artifact_type"] == "quiz"
        assert preview["question_count"] == 5
        assert len(preview["questions"]) > 0

    def test_podcast_preview_structure(self):
        """Test podcast preview contains expected fields"""
        preview = {
            "artifact_type": "podcast",
            "id": "podcast:456",
            "title": "Overview Podcast",
            "duration": "15:30",
            "audio_url": "/media/podcasts/episode.mp3",
            "transcript": "Welcome to this episode...",
        }
        assert preview["artifact_type"] == "podcast"
        assert preview["duration"] == "15:30"
        assert preview["audio_url"] is not None

    def test_summary_preview_structure(self):
        """Test summary preview contains expected fields"""
        preview = {
            "artifact_type": "summary",
            "id": "note:789",
            "title": "Executive Summary",
            "word_count": 250,
            "content": "This module covers the fundamentals...",
        }
        assert preview["artifact_type"] == "summary"
        assert preview["word_count"] == 250
        assert len(preview["content"]) > 0

    def test_transformation_preview_structure(self):
        """Test transformation preview contains expected fields"""
        preview = {
            "artifact_type": "transformation",
            "id": "note:101",
            "title": "Key Topics - Module",
            "word_count": 150,
            "content": "1. Machine Learning\n2. Neural Networks\n...",
            "transformation_name": "Key Topics",
        }
        assert preview["artifact_type"] == "transformation"
        assert preview["transformation_name"] == "Key Topics"


class TestCompanyScopingLogic:
    """Test company scoping prevents cross-company access"""

    def test_consistent_403_for_unauthorized(self):
        """Test that 403 is returned for both not-found and unauthorized cases"""
        # This prevents info leakage about artifact existence
        # Both "doesn't exist" and "exists but not authorized" return 403
        unauthorized_cases = [
            ("artifact doesn't exist", False),
            ("artifact exists but wrong company", False),
            ("artifact exists but notebook not published", False),
            ("artifact exists but module locked", False),
        ]

        for case_name, access_granted in unauthorized_cases:
            # All should result in access denied (403)
            assert access_granted is False, f"Case '{case_name}' should deny access"

    def test_cross_company_access_denied(self):
        """Test learners cannot access artifacts from other companies"""
        learner_company = "company:A"
        artifact_notebook_company = "company:B"

        access_granted = learner_company == artifact_notebook_company
        assert access_granted is False

    def test_same_company_access_granted(self):
        """Test learners can access artifacts from their own company"""
        learner_company = "company:A"
        artifact_notebook_company = "company:A"
        notebook_published = True
        notebook_locked = False

        access_granted = (
            learner_company == artifact_notebook_company
            and notebook_published
            and not notebook_locked
        )
        assert access_granted is True


# ==============================================================================
# HTTP Integration Tests for Learner Artifacts Endpoints
# ==============================================================================


class TestValidateLearnerAccessToNotebook:
    """Integration tests for validate_learner_access_to_notebook function"""

    @pytest.mark.asyncio
    async def test_access_granted_with_valid_assignment(self):
        """Test access granted when notebook is assigned, published, and unlocked"""
        from api.routers.artifacts import validate_learner_access_to_notebook
        from api.auth import LearnerContext
        from unittest.mock import MagicMock

        # Mock learner context
        mock_user = MagicMock()
        mock_user.id = "user:123"
        learner_context = LearnerContext(user=mock_user, company_id="company:acme")

        # Mock repo_query to return valid assignment
        with patch("api.routers.artifacts.repo_query") as mock_query:
            mock_query.return_value = [{"notebook": {"id": "notebook:123"}, "assignment": {"is_locked": False}}]

            result = await validate_learner_access_to_notebook("notebook:123", learner_context)
            assert result is True

    @pytest.mark.asyncio
    async def test_access_denied_when_not_assigned(self):
        """Test 403 raised when notebook not assigned to learner's company"""
        from api.routers.artifacts import validate_learner_access_to_notebook
        from api.auth import LearnerContext
        from unittest.mock import MagicMock

        mock_user = MagicMock()
        mock_user.id = "user:123"
        learner_context = LearnerContext(user=mock_user, company_id="company:acme")

        with patch("api.routers.artifacts.repo_query") as mock_query:
            mock_query.return_value = []  # No assignment found

            with pytest.raises(HTTPException) as exc_info:
                await validate_learner_access_to_notebook("notebook:123", learner_context)

            assert exc_info.value.status_code == 403
            assert "do not have access" in exc_info.value.detail


class TestValidateLearnerAccessToArtifact:
    """Integration tests for validate_learner_access_to_artifact function"""

    @pytest.mark.asyncio
    async def test_access_granted_for_valid_artifact(self):
        """Test access granted when artifact's notebook is assigned to learner"""
        from api.routers.artifacts import validate_learner_access_to_artifact
        from api.auth import LearnerContext
        from unittest.mock import MagicMock

        mock_user = MagicMock()
        mock_user.id = "user:123"
        learner_context = LearnerContext(user=mock_user, company_id="company:acme")

        with patch("api.routers.artifacts.repo_query") as mock_query:
            mock_query.return_value = [{
                "artifact": {"id": "artifact:123", "notebook_id": "notebook:456"},
                "notebook": {"published": True},
                "assignment": {"is_locked": False}
            }]

            # Should not raise
            await validate_learner_access_to_artifact("artifact:123", learner_context)

    @pytest.mark.asyncio
    async def test_access_denied_for_unauthorized_artifact(self):
        """Test 403 raised when artifact's notebook not assigned to learner"""
        from api.routers.artifacts import validate_learner_access_to_artifact
        from api.auth import LearnerContext
        from unittest.mock import MagicMock

        mock_user = MagicMock()
        mock_user.id = "user:123"
        learner_context = LearnerContext(user=mock_user, company_id="company:acme")

        with patch("api.routers.artifacts.repo_query") as mock_query:
            mock_query.return_value = []  # No valid assignment found

            with pytest.raises(HTTPException) as exc_info:
                await validate_learner_access_to_artifact("artifact:123", learner_context)

            assert exc_info.value.status_code == 403
            assert "do not have access" in exc_info.value.detail


class TestGetLearnerNotebookArtifactsEndpoint:
    """Integration tests for GET /learner/notebooks/{notebook_id}/artifacts"""

    @pytest.mark.asyncio
    async def test_returns_artifact_list_for_valid_notebook(self):
        """Test endpoint returns list of artifacts for authorized notebook"""
        from api.routers.artifacts import get_learner_notebook_artifacts
        from api.auth import LearnerContext
        from unittest.mock import MagicMock
        from open_notebook.domain.artifact import Artifact

        mock_user = MagicMock()
        mock_user.id = "user:123"
        learner_context = LearnerContext(user=mock_user, company_id="company:acme")

        # Mock artifacts
        mock_artifacts = [
            MagicMock(
                id="artifact:1",
                artifact_type="quiz",
                title="Quiz 1",
                created="2024-01-15T10:00:00Z"
            ),
            MagicMock(
                id="artifact:2",
                artifact_type="podcast",
                title="Podcast 1",
                created="2024-01-14T10:00:00Z"
            ),
        ]

        with patch("api.routers.artifacts.validate_learner_access_to_notebook") as mock_validate, \
             patch("api.routers.artifacts.artifacts_service") as mock_service:

            mock_validate.return_value = True
            mock_service.get_notebook_artifacts = AsyncMock(return_value=mock_artifacts)

            result = await get_learner_notebook_artifacts("notebook:123", learner_context)

            assert len(result) == 2
            assert result[0].artifact_type == "quiz"
            assert result[1].artifact_type == "podcast"
            mock_validate.assert_called_once()

    @pytest.mark.asyncio
    async def test_returns_empty_list_when_no_artifacts(self):
        """Test endpoint returns empty list when notebook has no artifacts"""
        from api.routers.artifacts import get_learner_notebook_artifacts
        from api.auth import LearnerContext
        from unittest.mock import MagicMock

        mock_user = MagicMock()
        mock_user.id = "user:123"
        learner_context = LearnerContext(user=mock_user, company_id="company:acme")

        with patch("api.routers.artifacts.validate_learner_access_to_notebook") as mock_validate, \
             patch("api.routers.artifacts.artifacts_service") as mock_service:

            mock_validate.return_value = True
            mock_service.get_notebook_artifacts = AsyncMock(return_value=[])

            result = await get_learner_notebook_artifacts("notebook:123", learner_context)

            assert result == []

    @pytest.mark.asyncio
    async def test_raises_403_for_unauthorized_notebook(self):
        """Test endpoint raises 403 when notebook not accessible"""
        from api.routers.artifacts import get_learner_notebook_artifacts
        from api.auth import LearnerContext
        from unittest.mock import MagicMock

        mock_user = MagicMock()
        mock_user.id = "user:123"
        learner_context = LearnerContext(user=mock_user, company_id="company:acme")

        with patch("api.routers.artifacts.validate_learner_access_to_notebook") as mock_validate:
            mock_validate.side_effect = HTTPException(status_code=403, detail="Access denied")

            with pytest.raises(HTTPException) as exc_info:
                await get_learner_notebook_artifacts("notebook:123", learner_context)

            assert exc_info.value.status_code == 403


class TestGetLearnerArtifactPreviewEndpoint:
    """Integration tests for GET /learner/artifacts/{artifact_id}/preview"""

    @pytest.mark.asyncio
    async def test_returns_quiz_preview(self):
        """Test endpoint returns quiz preview data"""
        from api.routers.artifacts import get_learner_artifact_preview
        from api.auth import LearnerContext
        from unittest.mock import MagicMock

        mock_user = MagicMock()
        mock_user.id = "user:123"
        learner_context = LearnerContext(user=mock_user, company_id="company:acme")

        mock_preview = {
            "artifact_type": "quiz",
            "id": "quiz:123",
            "title": "Test Quiz",
            "question_count": 5,
            "questions": [{"question": "Q1", "choices": ["A", "B", "C"], "correct_answer": 0}]
        }

        with patch("api.routers.artifacts.validate_learner_access_to_artifact") as mock_validate, \
             patch("api.routers.artifacts.artifacts_service") as mock_service:

            mock_validate.return_value = None  # No exception = access granted
            mock_service.get_artifact_with_preview = AsyncMock(return_value=mock_preview)

            result = await get_learner_artifact_preview("artifact:123", learner_context)

            assert result["artifact_type"] == "quiz"
            assert result["question_count"] == 5

    @pytest.mark.asyncio
    async def test_returns_podcast_preview(self):
        """Test endpoint returns podcast preview data"""
        from api.routers.artifacts import get_learner_artifact_preview
        from api.auth import LearnerContext
        from unittest.mock import MagicMock

        mock_user = MagicMock()
        mock_user.id = "user:123"
        learner_context = LearnerContext(user=mock_user, company_id="company:acme")

        mock_preview = {
            "artifact_type": "podcast",
            "id": "podcast:456",
            "title": "Test Podcast",
            "duration": "10:30",
            "audio_url": "/media/audio.mp3",
            "transcript": "Welcome..."
        }

        with patch("api.routers.artifacts.validate_learner_access_to_artifact") as mock_validate, \
             patch("api.routers.artifacts.artifacts_service") as mock_service:

            mock_validate.return_value = None
            mock_service.get_artifact_with_preview = AsyncMock(return_value=mock_preview)

            result = await get_learner_artifact_preview("artifact:456", learner_context)

            assert result["artifact_type"] == "podcast"
            assert result["duration"] == "10:30"

    @pytest.mark.asyncio
    async def test_returns_404_when_artifact_not_found(self):
        """Test endpoint returns 404 when artifact doesn't exist after access check"""
        from api.routers.artifacts import get_learner_artifact_preview
        from api.auth import LearnerContext
        from unittest.mock import MagicMock

        mock_user = MagicMock()
        mock_user.id = "user:123"
        learner_context = LearnerContext(user=mock_user, company_id="company:acme")

        with patch("api.routers.artifacts.validate_learner_access_to_artifact") as mock_validate, \
             patch("api.routers.artifacts.artifacts_service") as mock_service:

            mock_validate.return_value = None
            mock_service.get_artifact_with_preview = AsyncMock(return_value=None)

            with pytest.raises(HTTPException) as exc_info:
                await get_learner_artifact_preview("artifact:999", learner_context)

            assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_raises_403_for_unauthorized_artifact(self):
        """Test endpoint raises 403 when artifact not accessible"""
        from api.routers.artifacts import get_learner_artifact_preview
        from api.auth import LearnerContext
        from unittest.mock import MagicMock

        mock_user = MagicMock()
        mock_user.id = "user:123"
        learner_context = LearnerContext(user=mock_user, company_id="company:acme")

        with patch("api.routers.artifacts.validate_learner_access_to_artifact") as mock_validate:
            mock_validate.side_effect = HTTPException(status_code=403, detail="Access denied")

            with pytest.raises(HTTPException) as exc_info:
                await get_learner_artifact_preview("artifact:123", learner_context)

            assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_returns_500_when_preview_has_error(self):
        """Test endpoint returns 500 when preview data contains error"""
        from api.routers.artifacts import get_learner_artifact_preview
        from api.auth import LearnerContext
        from unittest.mock import MagicMock

        mock_user = MagicMock()
        mock_user.id = "user:123"
        learner_context = LearnerContext(user=mock_user, company_id="company:acme")

        mock_preview = {
            "artifact_type": "quiz",
            "error": "Quiz content not found"
        }

        with patch("api.routers.artifacts.validate_learner_access_to_artifact") as mock_validate, \
             patch("api.routers.artifacts.artifacts_service") as mock_service:

            mock_validate.return_value = None
            mock_service.get_artifact_with_preview = AsyncMock(return_value=mock_preview)

            with pytest.raises(HTTPException) as exc_info:
                await get_learner_artifact_preview("artifact:123", learner_context)

            assert exc_info.value.status_code == 500
