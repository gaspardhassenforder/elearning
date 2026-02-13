from pathlib import Path
from typing import List, Optional
from urllib.parse import unquote, urlparse

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from loguru import logger
from pydantic import BaseModel

from api.auth import get_current_user, require_admin, LearnerContext, get_current_learner
from open_notebook.domain.user import User
from open_notebook.domain.podcast import Podcast
from api.podcast_service import (
    PodcastGenerationRequest,
    PodcastGenerationResponse,
    PodcastService,
)

router = APIRouter(dependencies=[Depends(get_current_user)])


class PodcastEpisodeResponse(BaseModel):
    id: str
    name: str
    episode_profile: dict
    speaker_profile: dict
    briefing: str
    audio_file: Optional[str] = None
    audio_url: Optional[str] = None
    transcript: Optional[dict] = None
    outline: Optional[dict] = None
    created: Optional[str] = None
    job_status: Optional[str] = None


def _resolve_audio_path(audio_file: str) -> Path:
    if audio_file.startswith("file://"):
        parsed = urlparse(audio_file)
        return Path(unquote(parsed.path))
    return Path(audio_file)


@router.post("/podcasts/generate", response_model=PodcastGenerationResponse)
async def generate_podcast(request: PodcastGenerationRequest, admin: User = Depends(require_admin)):
    """
    Generate a podcast episode using Episode Profiles.
    Returns immediately with job ID for status tracking.
    """
    logger.info("=" * 80)
    logger.info(f"PODCAST GENERATION REQUEST RECEIVED")
    logger.info(f"  Episode Name: {request.episode_name}")
    logger.info(f"  Episode Profile: {request.episode_profile}")
    logger.info(f"  Speaker Profile: {request.speaker_profile}")
    logger.info(f"  Notebook ID: {request.notebook_id}")
    logger.info(f"  Notebook IDs: {request.notebook_ids}")
    logger.info(f"  Content Length: {len(request.content) if request.content else 0} chars")
    logger.info("=" * 80)
    
    try:
        logger.info("Submitting podcast generation job...")
        job_id, artifact_ids = await PodcastService.submit_generation_job(
            episode_profile_name=request.episode_profile,
            speaker_profile_name=request.speaker_profile,
            episode_name=request.episode_name,
            notebook_id=request.notebook_id,
            notebook_ids=request.notebook_ids,
            content=request.content,
            briefing_suffix=request.briefing_suffix,
        )

        logger.info(f"✓ Podcast generation job submitted successfully!")
        logger.info(f"  Job ID: {job_id}")
        logger.info(f"  Artifact IDs: {artifact_ids}")
        logger.info("=" * 80)

        return PodcastGenerationResponse(
            job_id=job_id,
            status="submitted",
            message=f"Podcast generation started for episode '{request.episode_name}'",
            episode_profile=request.episode_profile,
            episode_name=request.episode_name,
            artifact_id=artifact_ids[0] if artifact_ids else None,
        )

    except Exception as e:
        logger.error("=" * 80)
        logger.error("ERROR generating podcast: {}", str(e))
        logger.exception(e)
        logger.error("=" * 80)
        raise HTTPException(
            status_code=500, detail="Failed to generate podcast"
        )


@router.get("/podcasts/jobs/{job_id:path}")
async def get_podcast_job_status(job_id: str):
    """Get the status of a podcast generation job
    
    Note: Using {job_id:path} to handle job IDs that may contain colons (command:xxx)
    """
    try:
        logger.debug(f"Getting podcast job status for job_id: {job_id}")
        status_data = await PodcastService.get_job_status(job_id)
        return status_data

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error("Error fetching podcast job status for {}: {}", job_id, str(e))
        logger.exception(e)
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch job status: {str(e)}"
        )


@router.get("/podcasts/episodes", response_model=List[PodcastEpisodeResponse])
async def list_podcast_episodes():
    """List all podcast episodes"""
    try:
        episodes = await PodcastService.list_episodes()

        response_episodes = []
        for episode in episodes:
            # Skip incomplete episodes without command or audio
            if not episode.command and not episode.audio_file:
                continue

            # Get job status if available
            job_status = None
            if episode.command:
                try:
                    job_status = await episode.get_job_status()
                except Exception:
                    job_status = "unknown"
            else:
                # No command but has audio file = completed import
                job_status = "completed"

            audio_url = None
            if episode.audio_file:
                audio_path = _resolve_audio_path(episode.audio_file)
                if audio_path.exists():
                    audio_url = f"/api/podcasts/episodes/{episode.id}/audio"

            response_episodes.append(
                PodcastEpisodeResponse(
                    id=str(episode.id),
                    name=episode.name,
                    episode_profile=episode.episode_profile,
                    speaker_profile=episode.speaker_profile,
                    briefing=episode.briefing,
                    audio_file=episode.audio_file,
                    audio_url=audio_url,
                    transcript=episode.transcript,
                    outline=episode.outline,
                    created=str(episode.created) if episode.created else None,
                    job_status=job_status,
                )
            )

        return response_episodes

    except Exception as e:
        logger.error("Error listing podcast episodes: {}", str(e))
        raise HTTPException(
            status_code=500, detail="Failed to list podcast episodes"
        )


@router.get("/podcasts/episodes/{episode_id}", response_model=PodcastEpisodeResponse)
async def get_podcast_episode(episode_id: str):
    """Get a specific podcast episode"""
    try:
        episode = await PodcastService.get_episode(episode_id)

        # Get job status if available
        job_status = None
        if episode.command:
            try:
                job_status = await episode.get_job_status()
            except Exception:
                job_status = "unknown"
        else:
            # No command but has audio file = completed import
            job_status = "completed" if episode.audio_file else "unknown"

        audio_url = None
        if episode.audio_file:
            audio_path = _resolve_audio_path(episode.audio_file)
            if audio_path.exists():
                audio_url = f"/api/podcasts/episodes/{episode.id}/audio"

        return PodcastEpisodeResponse(
            id=str(episode.id),
            name=episode.name,
            episode_profile=episode.episode_profile,
            speaker_profile=episode.speaker_profile,
            briefing=episode.briefing,
            audio_file=episode.audio_file,
            audio_url=audio_url,
            transcript=episode.transcript,
            outline=episode.outline,
            created=str(episode.created) if episode.created else None,
            job_status=job_status,
        )

    except Exception as e:
        logger.error("Error fetching podcast episode: {}", str(e))
        raise HTTPException(status_code=404, detail="Episode not found")


@router.get("/podcasts/episodes/{episode_id}/audio")
async def stream_podcast_episode_audio(episode_id: str):
    """Stream the audio file associated with a podcast episode"""
    try:
        episode = await PodcastService.get_episode(episode_id)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error fetching podcast episode for audio: {}", str(e))
        raise HTTPException(status_code=404, detail="Episode not found")

    if not episode.audio_file:
        raise HTTPException(status_code=404, detail="Episode has no audio file")

    audio_path = _resolve_audio_path(episode.audio_file)
    if not audio_path.exists():
        raise HTTPException(status_code=404, detail="Audio file not found on disk")

    return FileResponse(
        audio_path,
        media_type="audio/mpeg",
        filename=audio_path.name,
    )


@router.delete("/podcasts/episodes/{episode_id}")
async def delete_podcast_episode(episode_id: str, admin: User = Depends(require_admin)):
    """Delete a podcast episode and its associated audio file"""
    try:
        # Get the episode first to check if it exists and get the audio file path
        episode = await PodcastService.get_episode(episode_id)

        # Delete the physical audio file if it exists
        if episode.audio_file:
            audio_path = _resolve_audio_path(episode.audio_file)
            if audio_path.exists():
                try:
                    audio_path.unlink()
                    logger.info(f"Deleted audio file: {audio_path}")
                except Exception as e:
                    logger.warning("Failed to delete audio file {}: {}", audio_path, str(e))

        # Delete the episode from the database
        await episode.delete()

        logger.info(f"Deleted podcast episode: {episode_id}")
        return {"message": "Episode deleted successfully", "episode_id": episode_id}

    except Exception as e:
        logger.error("Error deleting podcast episode: {}", str(e))
        raise HTTPException(
            status_code=500, detail="Failed to delete episode"
        )


# ==============================================================================
# Story 4.6: Podcast Artifact Endpoints (for surface_podcast tool)
# ==============================================================================


@router.get("/podcasts/{podcast_id}")
async def get_podcast(podcast_id: str, user: User = Depends(get_current_user)):
    """
    Get a specific podcast artifact by ID.

    Story 4.6: Company scoping for learners - validates notebook assignment.
    Story 7.5: Uses get_current_learner() for consistent company isolation.
    Used by InlineAudioPlayer component for artifact surfacing in chat.

    Handles both Podcast (podcast:xxx) and PodcastEpisode (episode:xxx) IDs.
    """
    from open_notebook.database.repository import repo_query, ensure_record_id
    from open_notebook.podcasts.models import PodcastEpisode

    try:
        # Detect model type from ID prefix
        is_episode = podcast_id.startswith("episode:")

        if is_episode:
            # Handle PodcastEpisode (from artifact system)
            try:
                episode = await PodcastEpisode.get(podcast_id)
            except Exception as e:
                logger.error("Error fetching episode {}: {}", podcast_id, str(e))
                raise HTTPException(status_code=404, detail="Episode not found")

            if not episode:
                raise HTTPException(status_code=404, detail="Episode not found")

            # PodcastEpisode doesn't have notebook_id for company scoping
            # Episodes accessed via artifacts are already scoped by the artifact query
            audio_url = None
            if episode.audio_file:
                audio_path = _resolve_audio_path(episode.audio_file)
                if audio_path.exists():
                    audio_url = f"/api/podcasts/episodes/{podcast_id}/audio"

            return {
                "id": str(episode.id),
                "title": episode.name,
                "topic": None,
                "length": "medium",
                "speaker_format": "multi",
                "audio_file_path": episode.audio_file,
                "transcript": episode.transcript,
                "is_overview": False,
                "created_by": "admin",
                "status": "completed" if episode.audio_file else "pending",
                "duration_minutes": 7,
                "is_ready": bool(episode.audio_file),
                "created": str(episode.created) if episode.created else None,
            }

        # Standard Podcast model path
        try:
            podcast = await Podcast.get(podcast_id)
        except Exception as e:
            logger.error("Error fetching podcast {}: {}", podcast_id, str(e))
            raise HTTPException(status_code=404, detail="Podcast not found")

        if not podcast:
            raise HTTPException(status_code=404, detail="Podcast not found")

        # Story 7.5: Company scoping - admin vs learner pattern
        if user.role == "learner":
            # Validate podcast's notebook is assigned to learner's company
            if not user.company_id:
                raise HTTPException(status_code=403, detail="Access denied")

            # Check module_assignment for company access
            result = await repo_query(
                """
                SELECT VALUE true
                FROM module_assignment
                WHERE notebook_id = $notebook_id
                  AND company_id = $company_id
                LIMIT 1
                """,
                {"notebook_id": ensure_record_id(podcast.notebook_id), "company_id": ensure_record_id(user.company_id)},
            )

            if not result:
                logger.warning(
                    "Learner {} attempted to access podcast {} from unassigned notebook {}",
                    user.id, podcast_id, podcast.notebook_id,
                )
                raise HTTPException(status_code=403, detail="Podcast not accessible")

        logger.info("Podcast {} accessed by {} user {}", podcast_id, user.role, user.id)

        return {
            "id": podcast.id,
            "title": podcast.title,
            "topic": podcast.topic,
            "length": podcast.length,
            "speaker_format": podcast.speaker_format,
            "audio_file_path": podcast.audio_file_path,
            "transcript": podcast.transcript,
            "is_overview": podcast.is_overview,
            "created_by": podcast.created_by,
            "status": podcast.status,
            "duration_minutes": podcast.duration_minutes,
            "is_ready": podcast.is_ready,
            "created": podcast.created,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Unexpected error fetching podcast {}: {}", podcast_id, str(e))
        raise HTTPException(status_code=500, detail="Failed to fetch podcast")


@router.get("/podcasts/{podcast_id}/audio")
async def stream_podcast_audio(podcast_id: str, user: User = Depends(get_current_user)):
    """
    Stream the audio file for a podcast artifact.

    Story 4.6: Company scoping for learners - validates notebook assignment.
    Story 7.5: Uses get_current_learner() for consistent company isolation.

    Handles both Podcast (podcast:xxx) and PodcastEpisode (episode:xxx) IDs.
    Episode IDs may arrive here if the frontend was built with an older artifact URL format.
    """
    from open_notebook.database.repository import repo_query, ensure_record_id
    from open_notebook.podcasts.models import PodcastEpisode

    try:
        # Detect model type from ID prefix
        is_episode = podcast_id.startswith("episode:")

        if is_episode:
            # Handle PodcastEpisode (legacy artifact URLs)
            try:
                episode = await PodcastEpisode.get(podcast_id)
            except Exception as e:
                logger.error("Error fetching episode {} for audio: {}", podcast_id, str(e))
                raise HTTPException(status_code=404, detail="Episode not found")

            if not episode:
                raise HTTPException(status_code=404, detail="Episode not found")

            if not episode.audio_file:
                raise HTTPException(status_code=404, detail="Episode has no audio file")

            audio_path = _resolve_audio_path(episode.audio_file)
            if not audio_path.exists():
                raise HTTPException(status_code=404, detail="Audio file not found on disk")

            return FileResponse(
                audio_path,
                media_type="audio/mpeg",
                filename=audio_path.name,
            )

        # Standard Podcast model path
        try:
            podcast = await Podcast.get(podcast_id)
        except Exception as e:
            logger.error("Error fetching podcast {} for audio: {}", podcast_id, str(e))
            raise HTTPException(status_code=404, detail="Podcast not found")

        if not podcast:
            raise HTTPException(status_code=404, detail="Podcast not found")

        # Story 7.5: Company scoping - admin vs learner pattern
        if user.role == "learner":
            if not user.company_id:
                raise HTTPException(status_code=403, detail="Access denied")

            result = await repo_query(
                """
                SELECT VALUE true
                FROM module_assignment
                WHERE notebook_id = $notebook_id
                  AND company_id = $company_id
                LIMIT 1
                """,
                {"notebook_id": ensure_record_id(podcast.notebook_id), "company_id": ensure_record_id(user.company_id)},
            )

            if not result:
                logger.warning(
                    "Learner {} attempted to access podcast audio {} from unassigned notebook",
                    user.id, podcast_id,
                )
                raise HTTPException(status_code=403, detail="Podcast not accessible")

        if not podcast.audio_file_path:
            raise HTTPException(status_code=404, detail="Podcast has no audio file")

        audio_path = Path(podcast.audio_file_path)
        if not audio_path.exists():
            raise HTTPException(status_code=404, detail="Audio file not found on disk")

        return FileResponse(
            audio_path,
            media_type="audio/mpeg",
            filename=audio_path.name,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Unexpected error streaming audio for {}: {}", podcast_id, str(e))
        raise HTTPException(status_code=500, detail="Failed to stream audio")


@router.get("/podcasts/{podcast_id}/transcript")
async def get_podcast_transcript(podcast_id: str, user: User = Depends(get_current_user)):
    """
    Get the transcript for a podcast artifact.

    Story 4.6: Company scoping for learners - validates notebook assignment.
    Story 7.5: Uses get_current_learner() for consistent company isolation.

    Handles both Podcast (podcast:xxx) and PodcastEpisode (episode:xxx) IDs.
    """
    from open_notebook.database.repository import repo_query, ensure_record_id
    from open_notebook.podcasts.models import PodcastEpisode

    try:
        # Detect model type from ID prefix
        is_episode = podcast_id.startswith("episode:")

        if is_episode:
            try:
                episode = await PodcastEpisode.get(podcast_id)
            except Exception as e:
                logger.error("Error fetching episode {} for transcript: {}", podcast_id, str(e))
                raise HTTPException(status_code=404, detail="Episode not found")

            if not episode:
                raise HTTPException(status_code=404, detail="Episode not found")

            if not episode.transcript:
                raise HTTPException(status_code=404, detail="Episode has no transcript")

            return {
                "podcast_id": str(episode.id),
                "title": episode.name,
                "transcript": episode.transcript,
            }

        # Standard Podcast model path
        try:
            podcast = await Podcast.get(podcast_id)
        except Exception as e:
            logger.error("Error fetching podcast {} for transcript: {}", podcast_id, str(e))
            raise HTTPException(status_code=404, detail="Podcast not found")

        if not podcast:
            raise HTTPException(status_code=404, detail="Podcast not found")

        # Story 7.5: Company scoping - admin vs learner pattern
        if user.role == "learner":
            if not user.company_id:
                raise HTTPException(status_code=403, detail="Access denied")

            result = await repo_query(
                """
                SELECT VALUE true
                FROM module_assignment
                WHERE notebook_id = $notebook_id
                  AND company_id = $company_id
                LIMIT 1
                """,
                {"notebook_id": ensure_record_id(podcast.notebook_id), "company_id": ensure_record_id(user.company_id)},
            )

            if not result:
                logger.warning(
                    "Learner {} attempted to access podcast transcript {} from unassigned notebook",
                    user.id, podcast_id,
                )
                raise HTTPException(status_code=403, detail="Podcast not accessible")

        if not podcast.transcript:
            raise HTTPException(status_code=404, detail="Podcast has no transcript")

        return {
            "podcast_id": podcast.id,
            "title": podcast.title,
            "transcript": podcast.transcript,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Unexpected error fetching transcript for {}: {}", podcast_id, str(e))
        raise HTTPException(status_code=500, detail="Failed to fetch transcript")
