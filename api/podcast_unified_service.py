"""Création / mise à jour couplée episode_profile + speaker_profile (wizard unique)."""

from typing import Any, Dict, List, Optional, Tuple

from fastapi import HTTPException
from loguru import logger

from open_notebook.podcasts.constants import (
    PODCAST_OUTLINE_MODEL,
    PODCAST_OUTLINE_PROVIDER,
    PODCAST_TTS_MODEL,
    PODCAST_TTS_PROVIDER,
    PODCAST_TRANSCRIPT_MODEL,
    PODCAST_TRANSCRIPT_PROVIDER,
    is_managed_episode_speaker_pair,
    managed_speaker_name_for_episode,
)
from open_notebook.podcasts.models import EpisodeProfile, SpeakerProfile


def _validate_speakers(speakers: List[Dict[str, Any]]) -> None:
    if not 1 <= len(speakers) <= 4:
        raise HTTPException(
            status_code=400, detail="Between 1 and 4 speakers are required"
        )
    required = ("name", "voice_id", "backstory", "personality")
    for s in speakers:
        for k in required:
            if k not in s or not str(s.get(k, "")).strip():
                raise HTTPException(
                    status_code=400,
                    detail=f"Each speaker must have non-empty {', '.join(required)}",
                )


async def create_unified_podcast_profile(
    *,
    name: str,
    description: str,
    speakers: List[Dict[str, Any]],
    default_briefing: str,
    num_segments: int,
) -> Tuple[EpisodeProfile, SpeakerProfile]:
    _validate_speakers(speakers)
    episode_name = name.strip()
    if not episode_name:
        raise HTTPException(status_code=400, detail="Profile name is required")

    speaker_key = managed_speaker_name_for_episode(episode_name)
    if await EpisodeProfile.get_by_name(episode_name):
        raise HTTPException(
            status_code=409, detail=f"Episode profile '{episode_name}' already exists"
        )
    if await SpeakerProfile.get_by_name(speaker_key):
        raise HTTPException(
            status_code=409, detail=f"Speaker profile '{speaker_key}' already exists"
        )

    sp = SpeakerProfile(
        name=speaker_key,
        description=description or "",
        tts_provider=PODCAST_TTS_PROVIDER,
        tts_model=PODCAST_TTS_MODEL,
        speakers=speakers,
    )
    await sp.save()

    ep = EpisodeProfile(
        name=episode_name,
        description=description or None,
        speaker_config=speaker_key,
        outline_provider=PODCAST_OUTLINE_PROVIDER,
        outline_model=PODCAST_OUTLINE_MODEL,
        transcript_provider=PODCAST_TRANSCRIPT_PROVIDER,
        transcript_model=PODCAST_TRANSCRIPT_MODEL,
        default_briefing=default_briefing,
        num_segments=num_segments,
    )
    await ep.save()
    logger.info("Created unified podcast profile episode={} speaker={}", episode_name, speaker_key)
    return ep, sp


async def update_unified_podcast_profile(
    profile_id: str,
    *,
    name: str,
    description: str,
    speakers: List[Dict[str, Any]],
    default_briefing: str,
    num_segments: int,
) -> Tuple[EpisodeProfile, SpeakerProfile]:
    _validate_speakers(speakers)
    episode_name = name.strip()
    if not episode_name:
        raise HTTPException(status_code=400, detail="Profile name is required")

    ep = await EpisodeProfile.get(profile_id)
    old_episode_name = ep.name
    old_speaker_key = ep.speaker_config

    speaker = await SpeakerProfile.get_by_name(old_speaker_key)
    if not speaker:
        raise HTTPException(
            status_code=400,
            detail=f"Speaker profile '{old_speaker_key}' not found for this episode profile",
        )

    other = await EpisodeProfile.get_by_name(episode_name)
    if other and str(other.id) != str(ep.id):
        raise HTTPException(
            status_code=409, detail=f"Episode profile '{episode_name}' already exists"
        )

    managed = is_managed_episode_speaker_pair(old_episode_name, old_speaker_key)
    new_speaker_key = old_speaker_key

    if managed and episode_name != old_episode_name:
        new_speaker_key = managed_speaker_name_for_episode(episode_name)
        existing = await SpeakerProfile.get_by_name(new_speaker_key)
        if existing and str(existing.id) != str(speaker.id):
            raise HTTPException(
                status_code=409,
                detail=f"Speaker profile '{new_speaker_key}' already exists",
            )
        speaker.name = new_speaker_key

    speaker.description = description or ""
    speaker.tts_provider = PODCAST_TTS_PROVIDER
    speaker.tts_model = PODCAST_TTS_MODEL
    speaker.speakers = speakers
    await speaker.save()

    ep.name = episode_name
    ep.description = description or None
    ep.speaker_config = new_speaker_key
    ep.outline_provider = PODCAST_OUTLINE_PROVIDER
    ep.outline_model = PODCAST_OUTLINE_MODEL
    ep.transcript_provider = PODCAST_TRANSCRIPT_PROVIDER
    ep.transcript_model = PODCAST_TRANSCRIPT_MODEL
    ep.default_briefing = default_briefing
    ep.num_segments = num_segments
    await ep.save()

    logger.info(
        "Updated unified podcast profile id={} episode={} speaker={}",
        profile_id,
        episode_name,
        new_speaker_key,
    )
    return ep, speaker


async def delete_episode_profile_with_managed_speaker(profile_id: str) -> None:
    ep = await EpisodeProfile.get(profile_id)
    speaker_key = ep.speaker_config
    managed = is_managed_episode_speaker_pair(ep.name, speaker_key)
    await ep.delete()
    if managed:
        sp = await SpeakerProfile.get_by_name(speaker_key)
        if sp:
            await sp.delete()
            logger.info("Deleted managed speaker profile {}", speaker_key)


async def duplicate_episode_profile_with_speaker_clone(
    profile_id: str,
) -> Tuple[EpisodeProfile, SpeakerProfile]:
    original = await EpisodeProfile.get(profile_id)
    src_speaker = await SpeakerProfile.get_by_name(original.speaker_config)
    if not src_speaker:
        raise HTTPException(
            status_code=400,
            detail=f"Speaker profile '{original.speaker_config}' not found",
        )

    new_episode_name = f"{original.name} - Copy"
    n = 2
    while await EpisodeProfile.get_by_name(new_episode_name) or await SpeakerProfile.get_by_name(
        managed_speaker_name_for_episode(new_episode_name)
    ):
        new_episode_name = f"{original.name} - Copy ({n})"
        n += 1

    new_speaker_key = managed_speaker_name_for_episode(new_episode_name)

    dup_sp = SpeakerProfile(
        name=new_speaker_key,
        description=src_speaker.description or "",
        tts_provider=PODCAST_TTS_PROVIDER,
        tts_model=PODCAST_TTS_MODEL,
        speakers=list(src_speaker.speakers),
    )
    await dup_sp.save()

    dup_ep = EpisodeProfile(
        name=new_episode_name,
        description=original.description,
        speaker_config=new_speaker_key,
        outline_provider=PODCAST_OUTLINE_PROVIDER,
        outline_model=PODCAST_OUTLINE_MODEL,
        transcript_provider=PODCAST_TRANSCRIPT_PROVIDER,
        transcript_model=PODCAST_TRANSCRIPT_MODEL,
        default_briefing=original.default_briefing,
        num_segments=original.num_segments,
    )
    await dup_ep.save()
    logger.info(
        "Duplicated podcast profile -> episode={} speaker={}",
        new_episode_name,
        new_speaker_key,
    )
    return dup_ep, dup_sp
