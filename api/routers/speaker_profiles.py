from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException
from loguru import logger
from pydantic import BaseModel

from api.auth import get_current_user
from open_notebook.podcasts.models import SpeakerProfile

router = APIRouter()


class SpeakerProfileResponse(BaseModel):
    id: str
    name: str
    description: str
    tts_provider: str
    tts_model: str
    speakers: List[Dict[str, Any]]


def _to_speaker_response(profile: SpeakerProfile) -> SpeakerProfileResponse:
    return SpeakerProfileResponse(
        id=str(profile.id),
        name=profile.name,
        description=profile.description or "",
        tts_provider=profile.tts_provider,
        tts_model=profile.tts_model,
        speakers=profile.speakers,
    )


@router.get("/speaker-profiles", response_model=List[SpeakerProfileResponse])
async def list_speaker_profiles(_user=Depends(get_current_user)):
    """List all available speaker profiles"""
    try:
        profiles = await SpeakerProfile.get_all(order_by="name asc")
        return [_to_speaker_response(profile) for profile in profiles]

    except Exception as e:
        logger.error("Failed to fetch speaker profiles: {}", str(e))
        raise HTTPException(
            status_code=500, detail="Failed to fetch speaker profiles"
        )


@router.get("/speaker-profiles/{profile_name}", response_model=SpeakerProfileResponse)
async def get_speaker_profile(profile_name: str, _user=Depends(get_current_user)):
    """Get a specific speaker profile by name"""
    try:
        profile = await SpeakerProfile.get_by_name(profile_name)

        if not profile:
            raise HTTPException(
                status_code=404, detail=f"Speaker profile '{profile_name}' not found"
            )

        return _to_speaker_response(profile)

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to fetch speaker profile '{}': {}", profile_name, str(e))
        raise HTTPException(
            status_code=500, detail="Failed to fetch speaker profile"
        )
