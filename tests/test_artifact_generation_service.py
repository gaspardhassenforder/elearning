"""
Unit tests for batch artifact generation service.
"""

import os
import pytest
from unittest.mock import patch, AsyncMock, MagicMock

from api.artifact_generation_service import (
    generate_all_artifacts,
    generate_quiz_artifact,
    generate_summary_artifact,
    generate_podcast_artifact,
    BatchGenerationStatus,
)


@pytest.fixture(autouse=True)
def setup_test_env():
    """Set up test environment variables."""
    os.environ.setdefault("SURREAL_URL", "ws://localhost:8000/rpc")
    os.environ.setdefault("SURREAL_USER", "root")
    os.environ.setdefault("SURREAL_PASSWORD", "root")
    os.environ.setdefault("SURREAL_NAMESPACE", "test")
    os.environ.setdefault("SURREAL_DATABASE", "test")


class TestBatchGenerationStatus:
    """Test suite for BatchGenerationStatus class."""

    def test_batch_status_initialization(self):
        """Test that BatchGenerationStatus initializes correctly."""
        status = BatchGenerationStatus()
        assert status.quiz_status == "pending"
        assert status.summary_status == "pending"
        assert status.transformations_status == "pending"
        assert status.podcast_status == "pending"
        assert status.quiz_id is None
        assert status.summary_id is None
        assert status.transformation_ids == []
        assert status.podcast_command_id is None

    def test_batch_status_to_dict(self):
        """Test conversion to dictionary."""
        status = BatchGenerationStatus()
        status.quiz_status = "completed"
        status.quiz_id = "quiz:123"

        result = status.to_dict()
        assert result["quiz"]["status"] == "completed"
        assert result["quiz"]["id"] == "quiz:123"
        assert result["summary"]["status"] == "pending"


class TestGenerateQuizArtifact:
    """Test suite for quiz artifact generation."""

    @pytest.mark.asyncio
    async def test_generate_quiz_success(self):
        """Test successful quiz generation."""
        mock_result = {
            "quiz_id": "quiz:abc123",
            "status": "completed",
            "error": None,
        }

        with patch("api.artifact_generation_service.quiz_service.generate_quiz") as mock_gen:
            mock_gen.return_value = mock_result

            status, quiz_id, error = await generate_quiz_artifact("notebook:123")

            assert status == "completed"
            assert quiz_id == "quiz:abc123"
            assert error is None
            mock_gen.assert_called_once_with(notebook_id="notebook:123", num_questions=5)

    @pytest.mark.asyncio
    async def test_generate_quiz_failure(self):
        """Test quiz generation with error."""
        mock_result = {
            "error": "No sources found in notebook",
            "quiz_id": None,
        }

        with patch("api.artifact_generation_service.quiz_service.generate_quiz") as mock_gen:
            mock_gen.return_value = mock_result

            status, quiz_id, error = await generate_quiz_artifact("notebook:123")

            assert status == "error"
            assert quiz_id is None
            assert "No sources found" in error

    @pytest.mark.asyncio
    async def test_generate_quiz_exception(self):
        """Test quiz generation with exception."""
        with patch("api.artifact_generation_service.quiz_service.generate_quiz") as mock_gen:
            mock_gen.side_effect = Exception("Database connection failed")

            status, quiz_id, error = await generate_quiz_artifact("notebook:123")

            assert status == "error"
            assert quiz_id is None
            assert "Database connection failed" in error


class TestGenerateSummaryArtifact:
    """Test suite for summary artifact generation."""

    @pytest.mark.asyncio
    async def test_generate_summary_notebook_not_found(self):
        """Test summary generation with non-existent notebook."""
        with patch("api.artifact_generation_service.Notebook.get") as mock_get:
            mock_get.return_value = None

            status, summary_id, error = await generate_summary_artifact("notebook:notfound")

            assert status == "error"
            assert summary_id is None
            assert "Notebook not found" in error

    @pytest.mark.asyncio
    async def test_generate_summary_no_sources(self):
        """Test summary generation with no sources."""
        mock_notebook = MagicMock()
        mock_notebook.id = "notebook:123"
        mock_notebook.name = "Test Notebook"

        with patch("api.artifact_generation_service.Notebook.get") as mock_get, \
             patch("api.artifact_generation_service.repo_query") as mock_query, \
             patch("api.artifact_generation_service.get_or_create_summary_transformation") as mock_txn:
            mock_get.return_value = mock_notebook
            mock_query.return_value = []  # No sources
            mock_txn.return_value = MagicMock(name="summary")

            status, summary_id, error = await generate_summary_artifact("notebook:123")

            assert status == "error"
            assert summary_id is None
            assert "No sources found" in error


class TestGeneratePodcastArtifact:
    """Test suite for podcast artifact generation."""

    @pytest.mark.asyncio
    async def test_generate_podcast_notebook_not_found(self):
        """Test podcast generation with non-existent notebook."""
        with patch("api.artifact_generation_service.Notebook.get") as mock_get:
            mock_get.return_value = None

            status, command_id, artifact_ids, error = await generate_podcast_artifact("notebook:notfound")

            assert status == "error"
            assert command_id is None
            assert artifact_ids == []
            assert "Notebook not found" in error

    @pytest.mark.asyncio
    async def test_generate_podcast_success(self):
        """Test successful podcast job submission."""
        mock_notebook = MagicMock()
        mock_notebook.id = "notebook:123"
        mock_notebook.name = "Test Notebook"

        with patch("api.artifact_generation_service.Notebook.get") as mock_get, \
             patch("api.artifact_generation_service.PodcastService.submit_generation_job") as mock_submit:
            mock_get.return_value = mock_notebook
            mock_submit.return_value = ("command:xyz789", ["artifact:p1"])

            status, command_id, artifact_ids, error = await generate_podcast_artifact("notebook:123")

            assert status == "processing"
            assert command_id == "command:xyz789"
            assert len(artifact_ids) == 1
            assert error is None


class TestGenerateAllArtifacts:
    """Test suite for batch artifact generation."""

    @pytest.mark.asyncio
    async def test_generate_all_notebook_not_found(self):
        """Test batch generation with non-existent notebook."""
        with patch("api.artifact_generation_service.Notebook.get") as mock_get:
            mock_get.return_value = None

            status = await generate_all_artifacts("notebook:notfound")

            assert status.quiz_status == "error"
            assert "Notebook not found" in status.quiz_error
            assert status.summary_status == "error"
            assert "Notebook not found" in status.summary_error
            assert status.podcast_status == "error"
            assert "Notebook not found" in status.podcast_error

    @pytest.mark.asyncio
    async def test_generate_all_success(self):
        """Test successful batch generation of all artifacts."""
        mock_notebook = MagicMock()
        mock_notebook.id = "notebook:123"
        mock_notebook.name = "Test Notebook"

        with patch("api.artifact_generation_service.Notebook.get") as mock_get, \
             patch("api.artifact_generation_service.generate_quiz_artifact") as mock_quiz, \
             patch("api.artifact_generation_service.generate_summary_artifact") as mock_summary, \
             patch("api.artifact_generation_service.generate_podcast_artifact") as mock_podcast:
            mock_get.return_value = mock_notebook
            mock_quiz.return_value = ("completed", "quiz:abc", None)
            mock_summary.return_value = ("completed", "note:def", None)
            mock_podcast.return_value = ("processing", "command:ghi", ["artifact:jkl"], None)

            status = await generate_all_artifacts("notebook:123")

            assert status.quiz_status == "completed"
            assert status.quiz_id == "quiz:abc"
            assert status.quiz_error is None

            assert status.summary_status == "completed"
            assert status.summary_id == "note:def"
            assert status.summary_error is None

            assert status.podcast_status == "processing"
            assert status.podcast_command_id == "command:ghi"
            assert len(status.podcast_artifact_ids) == 1

    @pytest.mark.asyncio
    async def test_generate_all_partial_failure(self):
        """Test batch generation with partial failures (error isolation)."""
        mock_notebook = MagicMock()
        mock_notebook.id = "notebook:123"

        with patch("api.artifact_generation_service.Notebook.get") as mock_get, \
             patch("api.artifact_generation_service.generate_quiz_artifact") as mock_quiz, \
             patch("api.artifact_generation_service.generate_summary_artifact") as mock_summary, \
             patch("api.artifact_generation_service.generate_podcast_artifact") as mock_podcast:
            mock_get.return_value = mock_notebook
            mock_quiz.return_value = ("error", None, "Quiz generation failed")
            mock_summary.return_value = ("completed", "note:def", None)  # Summary succeeds
            mock_podcast.return_value = ("processing", "command:ghi", ["artifact:jkl"], None)

            status = await generate_all_artifacts("notebook:123")

            # Quiz failed
            assert status.quiz_status == "error"
            assert "Quiz generation failed" in status.quiz_error

            # But summary and podcast succeeded
            assert status.summary_status == "completed"
            assert status.podcast_status == "processing"
