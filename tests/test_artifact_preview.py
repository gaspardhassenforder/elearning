"""
Unit tests for artifact preview endpoints.
"""

import os
import pytest
from unittest.mock import patch, AsyncMock, MagicMock

from api import artifacts_service


@pytest.fixture(autouse=True)
def setup_test_env():
    """Set up test environment variables."""
    os.environ.setdefault("SURREAL_URL", "ws://localhost:8000/rpc")
    os.environ.setdefault("SURREAL_USER", "root")
    os.environ.setdefault("SURREAL_PASSWORD", "root")
    os.environ.setdefault("SURREAL_NAMESPACE", "test")
    os.environ.setdefault("SURREAL_DATABASE", "test")


class TestGetArtifactPreview:
    """Test suite for artifact preview functionality."""

    @pytest.mark.asyncio
    async def test_get_quiz_preview(self):
        """Test preview for quiz artifact."""
        mock_artifact = MagicMock()
        mock_artifact.id = "artifact:123"
        mock_artifact.artifact_type = "quiz"
        mock_artifact.artifact_id = "quiz:abc"
        mock_artifact.title = "Test Quiz"

        mock_quiz = MagicMock()
        mock_quiz.id = "quiz:abc"
        mock_quiz.title = "Test Quiz"
        mock_quiz.questions = [
            MagicMock(
                question="What is 2+2?",
                choices=["3", "4", "5", "6"],
                correct_answer=1,
                explanation="Basic math"
            )
        ]

        with patch("api.artifacts_service.Artifact.get") as mock_get_artifact, \
             patch("api.artifacts_service.get_artifact_preview_data") as mock_preview:
            mock_get_artifact.return_value = mock_artifact
            mock_preview.return_value = {
                "artifact_type": "quiz",
                "id": "quiz:abc",
                "title": "Test Quiz",
                "question_count": 1,
                "questions": [
                    {
                        "question": "What is 2+2?",
                        "choices": ["3", "4", "5", "6"],
                        "correct_answer": 1,
                        "explanation": "Basic math"
                    }
                ]
            }

            result = await artifacts_service.get_artifact_with_preview("artifact:123")
            assert result["artifact_type"] == "quiz"
            assert result["question_count"] == 1

    @pytest.mark.asyncio
    async def test_get_podcast_preview(self):
        """Test preview for podcast artifact."""
        mock_artifact = MagicMock()
        mock_artifact.id = "artifact:456"
        mock_artifact.artifact_type = "podcast"
        mock_artifact.artifact_id = "podcast:def"
        mock_artifact.title = "Test Podcast"

        with patch("api.artifacts_service.Artifact.get") as mock_get_artifact, \
             patch("api.artifacts_service.get_artifact_preview_data") as mock_preview:
            mock_get_artifact.return_value = mock_artifact
            mock_preview.return_value = {
                "artifact_type": "podcast",
                "id": "podcast:def",
                "title": "Test Podcast",
                "duration": "5:30",
                "audio_url": "/media/podcast.mp3",
                "transcript": "Podcast transcript..."
            }

            result = await artifacts_service.get_artifact_with_preview("artifact:456")
            assert result["artifact_type"] == "podcast"
            assert result["duration"] == "5:30"

    @pytest.mark.asyncio
    async def test_get_summary_preview(self):
        """Test preview for summary artifact."""
        mock_artifact = MagicMock()
        mock_artifact.id = "artifact:789"
        mock_artifact.artifact_type = "summary"
        mock_artifact.artifact_id = "note:ghi"
        mock_artifact.title = "Test Summary"

        with patch("api.artifacts_service.Artifact.get") as mock_get_artifact, \
             patch("api.artifacts_service.get_artifact_preview_data") as mock_preview:
            mock_get_artifact.return_value = mock_artifact
            mock_preview.return_value = {
                "artifact_type": "summary",
                "id": "note:ghi",
                "title": "Test Summary",
                "word_count": 150,
                "content": "This is a test summary content..."
            }

            result = await artifacts_service.get_artifact_with_preview("artifact:789")
            assert result["artifact_type"] == "summary"
            assert result["word_count"] == 150

    @pytest.mark.asyncio
    async def test_get_transformation_preview(self):
        """Test preview for transformation artifact."""
        mock_artifact = MagicMock()
        mock_artifact.id = "artifact:xyz"
        mock_artifact.artifact_type = "transformation"
        mock_artifact.artifact_id = "note:jkl"
        mock_artifact.title = "Test Transformation"

        with patch("api.artifacts_service.Artifact.get") as mock_get_artifact, \
             patch("api.artifacts_service.get_artifact_preview_data") as mock_preview:
            mock_get_artifact.return_value = mock_artifact
            mock_preview.return_value = {
                "artifact_type": "transformation",
                "id": "note:jkl",
                "title": "Test Transformation",
                "word_count": 200,
                "content": "Transformed content...",
                "transformation_name": "simplify"
            }

            result = await artifacts_service.get_artifact_with_preview("artifact:xyz")
            assert result["artifact_type"] == "transformation"
            assert result["transformation_name"] == "simplify"

    @pytest.mark.asyncio
    async def test_artifact_not_found(self):
        """Test preview for non-existent artifact."""
        with patch("api.artifacts_service.Artifact.get") as mock_get:
            mock_get.return_value = None

            result = await artifacts_service.get_artifact_with_preview("artifact:notfound")
            assert result is None
