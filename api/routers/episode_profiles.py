from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException
from loguru import logger
from pydantic import BaseModel, Field

from api.auth import get_current_user, require_admin
from api.podcast_unified_service import (
    create_unified_podcast_profile,
    delete_episode_profile_with_managed_speaker,
    duplicate_episode_profile_with_speaker_clone,
    update_unified_podcast_profile,
)
from open_notebook.exceptions import NotFoundError
from open_notebook.podcasts.models import EpisodeProfile

router = APIRouter()


class EpisodeProfileResponse(BaseModel):
    id: str
    name: str
    description: str
    speaker_config: str
    outline_provider: str
    outline_model: str
    transcript_provider: str
    transcript_model: str
    default_briefing: str
    num_segments: int


def _to_episode_response(profile: EpisodeProfile) -> EpisodeProfileResponse:
    return EpisodeProfileResponse(
        id=str(profile.id),
        name=profile.name,
        description=profile.description or "",
        speaker_config=profile.speaker_config,
        outline_provider=profile.outline_provider,
        outline_model=profile.outline_model,
        transcript_provider=profile.transcript_provider,
        transcript_model=profile.transcript_model,
        default_briefing=profile.default_briefing,
        num_segments=profile.num_segments,
    )


@router.get("/episode-profiles", response_model=List[EpisodeProfileResponse])
async def list_episode_profiles(_user=Depends(get_current_user)):
    """List all available episode profiles"""
    try:
        profiles = await EpisodeProfile.get_all(order_by="name asc")
        return [_to_episode_response(profile) for profile in profiles]

    except Exception as e:
        logger.error("Failed to fetch episode profiles: {}", str(e))
        raise HTTPException(
            status_code=500, detail="Failed to fetch episode profiles"
        )


@router.get("/episode-profiles/{profile_name}", response_model=EpisodeProfileResponse)
async def get_episode_profile(profile_name: str, _user=Depends(get_current_user)):
    """Get a specific episode profile by name"""
    try:
        profile = await EpisodeProfile.get_by_name(profile_name)

        if not profile:
            raise HTTPException(
                status_code=404, detail=f"Episode profile '{profile_name}' not found"
            )

        return _to_episode_response(profile)

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to fetch episode profile '{}': {}", profile_name, str(e))
        raise HTTPException(
            status_code=500, detail="Failed to fetch episode profile"
        )


class UnifiedPodcastProfilePayload(BaseModel):
    """Wizard unique : intervenants + format épisode (TTS/LLM imposés côté serveur)."""

    name: str = Field(..., description="Unique episode profile name")
    description: str = Field("", description="Profile description")
    speakers: List[Dict[str, Any]] = Field(
        ..., description="Speaker voice configs (name, voice_id, backstory, personality)"
    )
    default_briefing: str = Field(..., description="Default briefing template")
    num_segments: int = Field(default=5, ge=3, le=20, description="Number of podcast segments")


@router.post("/episode-profiles/unified", response_model=EpisodeProfileResponse)
async def create_unified_episode_profile(
    payload: UnifiedPodcastProfilePayload, _admin=Depends(require_admin)
):
    """Create episode profile + managed speaker profile (single wizard)."""
    try:
        profile, _ = await create_unified_podcast_profile(
            name=payload.name,
            description=payload.description,
            speakers=payload.speakers,
            default_briefing=payload.default_briefing,
            num_segments=payload.num_segments,
        )
        return _to_episode_response(profile)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to create unified episode profile: {}", str(e))
        raise HTTPException(
            status_code=500, detail="Failed to create unified episode profile"
        )


@router.put("/episode-profiles/{profile_id}/unified", response_model=EpisodeProfileResponse)
async def update_unified_episode_profile(
    profile_id: str,
    payload: UnifiedPodcastProfilePayload,
    _admin=Depends(require_admin),
):
    """Update episode + linked speaker (same wizard payload)."""
    try:
        profile, _ = await update_unified_podcast_profile(
            profile_id,
            name=payload.name,
            description=payload.description,
            speakers=payload.speakers,
            default_briefing=payload.default_briefing,
            num_segments=payload.num_segments,
        )
        return _to_episode_response(profile)
    except NotFoundError:
        raise HTTPException(
            status_code=404, detail=f"Episode profile '{profile_id}' not found"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to update unified episode profile: {}", str(e))
        raise HTTPException(
            status_code=500, detail="Failed to update unified episode profile"
        )


@router.delete("/episode-profiles/{profile_id}")
async def delete_episode_profile(profile_id: str, _admin=Depends(require_admin)):
    """Delete an episode profile (et le speaker géré par le wizard si couplé)."""
    try:
        await delete_episode_profile_with_managed_speaker(profile_id)
        return {"message": "Episode profile deleted successfully"}
    except NotFoundError:
        raise HTTPException(
            status_code=404, detail=f"Episode profile '{profile_id}' not found"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to delete episode profile: {}", str(e))
        raise HTTPException(
            status_code=500, detail="Failed to delete episode profile"
        )


@router.post(
    "/episode-profiles/{profile_id}/duplicate", response_model=EpisodeProfileResponse
)
async def duplicate_episode_profile(profile_id: str, _admin=Depends(require_admin)):
    """Duplicate an episode profile (clone du pack voix lié)."""
    try:
        duplicate, _ = await duplicate_episode_profile_with_speaker_clone(profile_id)
        return _to_episode_response(duplicate)
    except NotFoundError:
        raise HTTPException(
            status_code=404, detail=f"Episode profile '{profile_id}' not found"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to duplicate episode profile: {}", str(e))
        raise HTTPException(
            status_code=500, detail="Failed to duplicate episode profile"
        )
