"""
Unit tests for artifact regeneration.
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


class TestRegenerateArtifact:
    """Test suite for artifact regeneration."""

    @pytest.mark.asyncio
    async def test_regenerate_quiz(self):
        """Test regenerating a quiz artifact."""
        mock_artifact = MagicMock()
        mock_artifact.id = "artifact:123"
        mock_artifact.artifact_type = "quiz"
        mock_artifact.artifact_id = "quiz:old123"
        mock_artifact.notebook_id = "notebook:456"
        mock_artifact.title = "Old Quiz"

        with patch("api.artifacts_service.Artifact.get") as mock_get_artifact, \
             patch("api.artifacts_service.delete_artifact") as mock_delete, \
             patch("api.artifact_generation_service.generate_quiz_artifact") as mock_gen_quiz:
            mock_get_artifact.return_value = mock_artifact
            mock_delete.return_value = True
            mock_gen_quiz.return_value = ("completed", "quiz:new456", None)

            result = await artifacts_service.regenerate_artifact("artifact:123")

            assert result["status"] == "completed"
            assert result["new_artifact_id"] == "quiz:new456"
            assert result["artifact_type"] == "quiz"
            mock_delete.assert_called_once_with("artifact:123")

    @pytest.mark.asyncio
    async def test_regenerate_summary(self):
        """Test regenerating a summary artifact."""
        mock_artifact = MagicMock()
        mock_artifact.id = "artifact:789"
        mock_artifact.artifact_type = "summary"
        mock_artifact.artifact_id = "note:old789"
        mock_artifact.notebook_id = "notebook:456"
        mock_artifact.title = "Old Summary"

        with patch("api.artifacts_service.Artifact.get") as mock_get_artifact, \
             patch("api.artifacts_service.delete_artifact") as mock_delete, \
             patch("api.artifact_generation_service.generate_summary_artifact") as mock_gen_summary:
            mock_get_artifact.return_value = mock_artifact
            mock_delete.return_value = True
            mock_gen_summary.return_value = ("completed", "note:new789", None)

            result = await artifacts_service.regenerate_artifact("artifact:789")

            assert result["status"] == "completed"
            assert result["new_artifact_id"] == "note:new789"
            assert result["artifact_type"] == "summary"

    @pytest.mark.asyncio
    async def test_regenerate_podcast(self):
        """Test regenerating a podcast artifact."""
        mock_artifact = MagicMock()
        mock_artifact.id = "artifact:xyz"
        mock_artifact.artifact_type = "podcast"
        mock_artifact.artifact_id = "podcast:oldxyz"
        mock_artifact.notebook_id = "notebook:456"
        mock_artifact.title = "Old Podcast"

        with patch("api.artifacts_service.Artifact.get") as mock_get_artifact, \
             patch("api.artifacts_service.delete_artifact") as mock_delete, \
             patch("api.artifact_generation_service.generate_podcast_artifact") as mock_gen_podcast:
            mock_get_artifact.return_value = mock_artifact
            mock_delete.return_value = True
            mock_gen_podcast.return_value = ("processing", "command:newxyz", ["artifact:newp1"], None)

            result = await artifacts_service.regenerate_artifact("artifact:xyz")

            assert result["status"] == "processing"
            assert result["command_id"] == "command:newxyz"
            assert result["artifact_type"] == "podcast"

    @pytest.mark.asyncio
    async def test_regenerate_artifact_not_found(self):
        """Test regenerating non-existent artifact."""
        with patch("api.artifacts_service.Artifact.get") as mock_get:
            mock_get.return_value = None

            result = await artifacts_service.regenerate_artifact("artifact:notfound")

            assert result["status"] == "error"
            assert "not found" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_regenerate_unsupported_type(self):
        """Test regenerating unsupported artifact type."""
        mock_artifact = MagicMock()
        mock_artifact.id = "artifact:unsupported"
        mock_artifact.artifact_type = "unknown_type"
        mock_artifact.artifact_id = "something:123"
        mock_artifact.notebook_id = "notebook:456"

        with patch("api.artifacts_service.Artifact.get") as mock_get, \
             patch("api.artifacts_service.delete_artifact") as mock_delete:
            mock_get.return_value = mock_artifact
            mock_delete.return_value = True

            result = await artifacts_service.regenerate_artifact("artifact:unsupported")

            assert result["status"] == "error"
            assert "not supported" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_regenerate_deletion_fails(self):
        """Test regeneration when deletion of old artifact fails."""
        mock_artifact = MagicMock()
        mock_artifact.id = "artifact:123"
        mock_artifact.artifact_type = "quiz"
        mock_artifact.artifact_id = "quiz:old123"

        with patch("api.artifacts_service.Artifact.get") as mock_get, \
             patch("api.artifacts_service.delete_artifact") as mock_delete:
            mock_get.return_value = mock_artifact
            mock_delete.return_value = False  # Deletion fails

            result = await artifacts_service.regenerate_artifact("artifact:123")

            assert result["status"] == "error"
            assert "delete" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_regenerate_generation_fails(self):
        """Test regeneration when new generation fails."""
        mock_artifact = MagicMock()
        mock_artifact.id = "artifact:123"
        mock_artifact.artifact_type = "quiz"
        mock_artifact.artifact_id = "quiz:old123"
        mock_artifact.notebook_id = "notebook:456"

        with patch("api.artifacts_service.Artifact.get") as mock_get, \
             patch("api.artifacts_service.delete_artifact") as mock_delete, \
             patch("api.artifact_generation_service.generate_quiz_artifact") as mock_gen:
            mock_get.return_value = mock_artifact
            mock_delete.return_value = True
            mock_gen.return_value = ("error", None, "Generation failed")

            result = await artifacts_service.regenerate_artifact("artifact:123")

            assert result["status"] == "error"
            assert result["error"] == "Generation failed"
