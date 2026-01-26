"""
Comprehensive unit tests for podcast generation pipeline.
Tests the full flow from job submission to completion, including cancellation.
"""

import os
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from typing import Dict, Any

from api.podcast_service import PodcastService, PodcastGenerationRequest
from api.command_service import CommandService
from open_notebook.domain.artifact import Artifact
from open_notebook.podcasts.models import EpisodeProfile, SpeakerProfile, PodcastEpisode


@pytest.fixture(autouse=True)
def setup_test_env():
    """Set up test environment variables."""
    os.environ.setdefault("SURREAL_URL", "ws://localhost:8000/rpc")
    os.environ.setdefault("SURREAL_USER", "root")
    os.environ.setdefault("SURREAL_PASSWORD", "root")
    os.environ.setdefault("SURREAL_NAMESPACE", "test")
    os.environ.setdefault("SURREAL_DATABASE", "test")


class TestPodcastGenerationPipeline:
    """Test suite for the complete podcast generation pipeline."""

    @pytest.mark.asyncio
    async def test_submit_podcast_generation_job(self):
        """Test submitting a podcast generation job."""
        # Mock episode and speaker profiles
        mock_episode_profile = MagicMock(spec=EpisodeProfile)
        mock_episode_profile.name = "test_episode"
        
        mock_speaker_profile = MagicMock(spec=SpeakerProfile)
        mock_speaker_profile.name = "test_speaker"
        
        # Mock submit_command to return a job ID
        mock_job_id = "command:test_job_123"
        
        with patch("api.podcast_service.EpisodeProfile.get_by_name", new_callable=AsyncMock) as mock_ep_get:
            with patch("api.podcast_service.SpeakerProfile.get_by_name", new_callable=AsyncMock) as mock_sp_get:
                with patch("api.podcast_service.submit_command") as mock_submit:
                    with patch("api.podcast_service.Artifact.create_for_artifact", new_callable=AsyncMock) as mock_artifact:
                        mock_ep_get.return_value = mock_episode_profile
                        mock_sp_get.return_value = mock_speaker_profile
                        mock_submit.return_value = mock_job_id
                        
                        mock_artifact_instance = MagicMock()
                        mock_artifact_instance.id = "artifact:123"
                        mock_artifact.return_value = mock_artifact_instance
                        
                        job_id, artifact_ids = await PodcastService.submit_generation_job(
                            episode_profile_name="test_episode",
                            speaker_profile_name="test_speaker",
                            episode_name="Test Episode",
                            notebook_id="notebook:test",
                            content="Test content for podcast",
                        )
                        
                        assert job_id == mock_job_id
                        assert len(artifact_ids) == 1
                        mock_submit.assert_called_once()
                        mock_artifact.assert_called_once()

    @pytest.mark.asyncio
    async def test_submit_job_with_multiple_notebooks(self):
        """Test submitting a job with multiple notebooks."""
        mock_episode_profile = MagicMock(spec=EpisodeProfile)
        mock_episode_profile.name = "test_episode"
        
        mock_speaker_profile = MagicMock(spec=SpeakerProfile)
        mock_speaker_profile.name = "test_speaker"
        
        mock_job_id = "command:test_job_456"
        
        with patch("api.podcast_service.EpisodeProfile.get_by_name", new_callable=AsyncMock) as mock_ep_get:
            with patch("api.podcast_service.SpeakerProfile.get_by_name", new_callable=AsyncMock) as mock_sp_get:
                with patch("api.podcast_service.submit_command") as mock_submit:
                    with patch("api.podcast_service.Artifact.create_for_artifact", new_callable=AsyncMock) as mock_artifact:
                        mock_ep_get.return_value = mock_episode_profile
                        mock_sp_get.return_value = mock_speaker_profile
                        mock_submit.return_value = mock_job_id
                        
                        mock_artifact_instance = MagicMock()
                        mock_artifact_instance.id = "artifact:123"
                        mock_artifact.return_value = mock_artifact_instance
                        
                        job_id, artifact_ids = await PodcastService.submit_generation_job(
                            episode_profile_name="test_episode",
                            speaker_profile_name="test_speaker",
                            episode_name="Test Episode",
                            notebook_ids=["notebook:1", "notebook:2"],
                            content="Test content",
                        )
                        
                        assert job_id == mock_job_id
                        assert len(artifact_ids) == 2
                        assert mock_artifact.call_count == 2

    @pytest.mark.asyncio
    async def test_get_job_status(self):
        """Test getting job status."""
        mock_status = MagicMock()
        mock_status.status = "running"
        mock_status.result = None
        mock_status.error_message = None
        mock_status.created = "2024-01-01T00:00:00Z"
        mock_status.updated = "2024-01-01T00:01:00Z"
        mock_status.progress = None
        
        with patch("api.podcast_service.get_command_status", new_callable=AsyncMock) as mock_get_status:
            mock_get_status.return_value = mock_status
            
            status = await PodcastService.get_job_status("command:test_job_123")
            
            # Note: get_job_status strips the command: prefix, so returned job_id won't have it
            assert status["job_id"] == "test_job_123"
            assert status["status"] == "running"
            # The service strips command: prefix before calling get_command_status
            mock_get_status.assert_called_once_with("test_job_123")

    @pytest.mark.asyncio
    async def test_cancel_command_job_success(self):
        """Test successfully canceling a command job."""
        mock_cancel_fn = MagicMock(return_value=True)
        
        with patch("api.command_service.surreal_commands") as mock_sc:
            # Mock the cancellation function
            mock_sc.cancel_command_job = mock_cancel_fn
            
            result = await CommandService.cancel_command_job("command:test_job_123")
            
            assert result is True
            mock_cancel_fn.assert_called_once_with("command:test_job_123")

    @pytest.mark.asyncio
    async def test_cancel_command_job_not_supported(self):
        """Test canceling when cancellation is not supported."""
        with patch("api.command_service.surreal_commands") as mock_sc:
            # Make getattr return None for all cancellation function names
            mock_sc.configure_mock(**{
                "cancel_command_job": None,
                "cancel_command": None,
                "cancel_job": None,
                "stop_command": None,
                "stop_job": None,
                "abort_command": None,
                "abort_job": None,
            })
            # Override getattr to return None for any attribute
            type(mock_sc).__getattr__ = lambda self, name: None
            
            result = await CommandService.cancel_command_job("command:test_job_123")
            
            # Should return False when cancellation is not supported
            assert result is False

    @pytest.mark.asyncio
    async def test_cancel_command_job_async(self):
        """Test canceling with async cancellation function."""
        async def async_cancel(job_id: str):
            return True
        
        mock_cancel_fn = AsyncMock(side_effect=async_cancel)
        
        with patch("api.command_service.surreal_commands") as mock_sc:
            mock_sc.cancel_command_job = mock_cancel_fn
            
            result = await CommandService.cancel_command_job("command:test_job_123")
            
            assert result is True
            mock_cancel_fn.assert_called_once_with("command:test_job_123")

    @pytest.mark.asyncio
    async def test_submit_job_missing_content(self):
        """Test submitting a job without content raises error."""
        from fastapi import HTTPException
        
        mock_episode_profile = MagicMock(spec=EpisodeProfile)
        mock_episode_profile.name = "test_episode"
        
        mock_speaker_profile = MagicMock(spec=SpeakerProfile)
        mock_speaker_profile.name = "test_speaker"
        
        with patch("api.podcast_service.EpisodeProfile.get_by_name", new_callable=AsyncMock) as mock_ep_get:
            with patch("api.podcast_service.SpeakerProfile.get_by_name", new_callable=AsyncMock) as mock_sp_get:
                mock_ep_get.return_value = mock_episode_profile
                mock_sp_get.return_value = mock_speaker_profile
                
                # The service wraps ValueError in HTTPException
                with pytest.raises(HTTPException) as exc_info:
                    await PodcastService.submit_generation_job(
                        episode_profile_name="test_episode",
                        speaker_profile_name="test_speaker",
                        episode_name="Test Episode",
                        content=None,
                        notebook_id=None,
                    )
                assert "Content is required" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_submit_job_invalid_episode_profile(self):
        """Test submitting a job with invalid episode profile."""
        from fastapi import HTTPException
        
        with patch("api.podcast_service.EpisodeProfile.get_by_name", new_callable=AsyncMock) as mock_ep_get:
            mock_ep_get.return_value = None
            
            # The service wraps ValueError in HTTPException
            with pytest.raises(HTTPException) as exc_info:
                await PodcastService.submit_generation_job(
                    episode_profile_name="nonexistent",
                    speaker_profile_name="test_speaker",
                    episode_name="Test Episode",
                    content="Test content",
                )
            assert "Episode profile" in str(exc_info.value.detail)
            assert "not found" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_submit_job_invalid_speaker_profile(self):
        """Test submitting a job with invalid speaker profile."""
        from fastapi import HTTPException
        
        mock_episode_profile = MagicMock(spec=EpisodeProfile)
        mock_episode_profile.name = "test_episode"
        
        with patch("api.podcast_service.EpisodeProfile.get_by_name", new_callable=AsyncMock) as mock_ep_get:
            with patch("api.podcast_service.SpeakerProfile.get_by_name", new_callable=AsyncMock) as mock_sp_get:
                mock_ep_get.return_value = mock_episode_profile
                mock_sp_get.return_value = None
                
                # The service wraps ValueError in HTTPException
                with pytest.raises(HTTPException) as exc_info:
                    await PodcastService.submit_generation_job(
                        episode_profile_name="test_episode",
                        speaker_profile_name="nonexistent",
                        episode_name="Test Episode",
                        content="Test content",
                    )
                assert "Speaker profile" in str(exc_info.value.detail)
                assert "not found" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_artifact_creation_with_job_id(self):
        """Test that artifacts are created with job ID as placeholder."""
        mock_episode_profile = MagicMock(spec=EpisodeProfile)
        mock_episode_profile.name = "test_episode"
        
        mock_speaker_profile = MagicMock(spec=SpeakerProfile)
        mock_speaker_profile.name = "test_speaker"
        
        mock_job_id = "command:test_job_789"
        
        with patch("api.podcast_service.EpisodeProfile.get_by_name", new_callable=AsyncMock) as mock_ep_get:
            with patch("api.podcast_service.SpeakerProfile.get_by_name", new_callable=AsyncMock) as mock_sp_get:
                with patch("api.podcast_service.submit_command") as mock_submit:
                    with patch("api.podcast_service.Artifact.create_for_artifact", new_callable=AsyncMock) as mock_artifact:
                        mock_ep_get.return_value = mock_episode_profile
                        mock_sp_get.return_value = mock_speaker_profile
                        mock_submit.return_value = mock_job_id
                        
                        mock_artifact_instance = MagicMock()
                        mock_artifact_instance.id = "artifact:456"
                        mock_artifact.return_value = mock_artifact_instance
                        
                        job_id, artifact_ids = await PodcastService.submit_generation_job(
                            episode_profile_name="test_episode",
                            speaker_profile_name="test_speaker",
                            episode_name="Test Episode",
                            notebook_id="notebook:test",
                            content="Test content",
                        )
                        
                        # Verify artifact was created with job_id as artifact_id
                        call_args = mock_artifact.call_args
                        assert call_args[1]["artifact_id"] == mock_job_id
                        assert call_args[1]["artifact_type"] == "podcast"
                        assert call_args[1]["title"] == "Test Episode"
                        assert call_args[1]["notebook_id"] == "notebook:test"


class TestJobStatusFlow:
    """Test suite for job status tracking and updates."""

    @pytest.mark.asyncio
    async def test_job_status_pending_to_running(self):
        """Test job status progression from pending to running."""
        statuses = [
            {"status": "pending", "result": None},
            {"status": "running", "result": None},
        ]
        
        mock_get_status = AsyncMock(side_effect=[
            MagicMock(status=s["status"], result=s["result"], 
                     error_message=None, created=None, updated=None, progress=None)
            for s in statuses
        ])
        
        with patch("api.podcast_service.get_command_status", mock_get_status):
            # First check - pending
            status1 = await PodcastService.get_job_status("command:test_job")
            assert status1["status"] == "pending"
            
            # Second check - running
            status2 = await PodcastService.get_job_status("command:test_job")
            assert status2["status"] == "running"

    @pytest.mark.asyncio
    async def test_job_status_completed(self):
        """Test job status when completed."""
        mock_status = MagicMock()
        mock_status.status = "completed"
        mock_status.result = {"episode_id": "episode:123", "success": True}
        mock_status.error_message = None
        mock_status.created = "2024-01-01T00:00:00Z"
        mock_status.updated = "2024-01-01T00:05:00Z"
        mock_status.progress = None
        
        with patch("api.podcast_service.get_command_status", new_callable=AsyncMock) as mock_get_status:
            mock_get_status.return_value = mock_status
            
            status = await PodcastService.get_job_status("command:test_job")
            
            assert status["status"] == "completed"
            assert status["result"]["episode_id"] == "episode:123"

    @pytest.mark.asyncio
    async def test_job_status_failed(self):
        """Test job status when failed."""
        mock_status = MagicMock()
        mock_status.status = "failed"
        mock_status.result = None
        mock_status.error_message = "Generation failed: Invalid content"
        mock_status.created = "2024-01-01T00:00:00Z"
        mock_status.updated = "2024-01-01T00:02:00Z"
        mock_status.progress = None
        
        with patch("api.podcast_service.get_command_status", new_callable=AsyncMock) as mock_get_status:
            mock_get_status.return_value = mock_status
            
            status = await PodcastService.get_job_status("command:test_job")
            
            assert status["status"] == "failed"
            assert "Invalid content" in status["error_message"]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
