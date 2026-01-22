"""
Unit tests for podcast generation configuration.
Tests Google AI model configuration for podcast profiles.
"""

import os
import pytest
from unittest.mock import patch, MagicMock

from open_notebook.podcasts.models import EpisodeProfile, SpeakerProfile


@pytest.fixture(autouse=True)
def setup_test_env():
    """Set up test environment variables."""
    os.environ.setdefault("SURREAL_URL", "ws://localhost:8000/rpc")
    os.environ.setdefault("SURREAL_USER", "root")
    os.environ.setdefault("SURREAL_PASSWORD", "root")
    os.environ.setdefault("SURREAL_NAMESPACE", "test")
    os.environ.setdefault("SURREAL_DATABASE", "test")


class TestEpisodeProfile:
    """Test suite for Episode Profile model."""

    @pytest.mark.asyncio
    async def test_episode_profile_google_config(self):
        """Test that episode profile supports Google AI configuration."""
        mock_profile_data = {
            "name": "tech_discussion",
            "description": "Technical discussion",
            "speaker_config": "tech_experts",
            "outline_provider": "google",
            "outline_model": "gemini-3-flash-preview",
            "transcript_provider": "google",
            "transcript_model": "gemini-3-flash-preview",
            "default_briefing": "Create an engaging technical discussion",
            "num_segments": 5,
        }

        with patch("open_notebook.podcasts.models.repo_query") as mock_query:
            mock_query.return_value = [mock_profile_data]

            profile = await EpisodeProfile.get_by_name("tech_discussion")
            assert profile is not None
            assert profile.outline_provider == "google"
            assert profile.outline_model == "gemini-3-flash-preview"
            assert profile.transcript_provider == "google"
            assert profile.transcript_model == "gemini-3-flash-preview"

    @pytest.mark.asyncio
    async def test_episode_profile_not_found(self):
        """Test that non-existent profile returns None."""
        with patch("open_notebook.podcasts.models.repo_query") as mock_query:
            mock_query.return_value = []

            profile = await EpisodeProfile.get_by_name("nonexistent")
            assert profile is None


class TestSpeakerProfile:
    """Test suite for Speaker Profile model."""

    @pytest.mark.asyncio
    async def test_speaker_profile_google_tts(self):
        """Test that speaker profile supports Google TTS configuration."""
        mock_profile_data = {
            "name": "tech_experts",
            "description": "Two technical experts",
            "tts_provider": "google",
            "tts_model": "gemini-2.5-flash-preview-tts",
            "speakers": [
                {
                    "name": "Dr. Alex Chen",
                    "voice_id": "Kore",
                    "backstory": "Senior AI researcher",
                    "personality": "Analytical and clear",
                },
                {
                    "name": "Jamie Rodriguez",
                    "voice_id": "Puck",
                    "backstory": "Full-stack engineer",
                    "personality": "Enthusiastic and practical",
                },
            ],
        }

        with patch("open_notebook.podcasts.models.repo_query") as mock_query:
            mock_query.return_value = [mock_profile_data]

            profile = await SpeakerProfile.get_by_name("tech_experts")
            assert profile is not None
            assert profile.tts_provider == "google"
            assert profile.tts_model == "gemini-2.5-flash-preview-tts"
            assert len(profile.speakers) == 2
            assert profile.speakers[0]["voice_id"] == "Kore"
            assert profile.speakers[1]["voice_id"] == "Puck"

    @pytest.mark.asyncio
    async def test_speaker_profile_google_voices(self):
        """Test that Google voices are valid."""
        valid_google_voices = ["Kore", "Puck", "Charon", "Aoede"]
        
        mock_profile_data = {
            "name": "solo_expert",
            "description": "Single expert",
            "tts_provider": "google",
            "tts_model": "gemini-2.5-flash-preview-tts",
            "speakers": [
                {
                    "name": "Professor Sarah Kim",
                    "voice_id": "Kore",
                    "backstory": "Distinguished professor",
                    "personality": "Patient teacher",
                }
            ],
        }

        with patch("open_notebook.podcasts.models.repo_query") as mock_query:
            mock_query.return_value = [mock_profile_data]

            profile = await SpeakerProfile.get_by_name("solo_expert")
            assert profile is not None
            assert profile.speakers[0]["voice_id"] in valid_google_voices


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
