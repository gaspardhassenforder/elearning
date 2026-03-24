"""Stack podcast imposé (TTS + LLM script) — ne pas exposer au wizard admin."""

# Aligné sur migrations/15.surrealql (Google Gemini)
PODCAST_TTS_PROVIDER = "google"
PODCAST_TTS_MODEL = "gemini-2.5-flash-preview-tts"

PODCAST_OUTLINE_PROVIDER = "google"
PODCAST_OUTLINE_MODEL = "gemini-3-flash-preview"
PODCAST_TRANSCRIPT_PROVIDER = "google"
PODCAST_TRANSCRIPT_MODEL = "gemini-3-flash-preview"

# Profil voix créé par le wizard : un enregistrement speaker_profile par profil épisode
MANAGED_SPEAKER_NAME_SUFFIX = "::__podcast_voices"


def managed_speaker_name_for_episode(episode_name: str) -> str:
    return f"{episode_name.strip()}{MANAGED_SPEAKER_NAME_SUFFIX}"


def is_managed_episode_speaker_pair(episode_name: str, speaker_config: str) -> bool:
    return speaker_config == managed_speaker_name_for_episode(episode_name)
