from typing import Any, Dict, Optional, Tuple

from fastapi import HTTPException
from loguru import logger
from pydantic import BaseModel
from surreal_commands import get_command_status, submit_command

from open_notebook.domain.artifact import Artifact
from open_notebook.domain.notebook import Notebook
from open_notebook.podcasts.models import EpisodeProfile, PodcastEpisode, SpeakerProfile


class PodcastGenerationRequest(BaseModel):
    """Request model for podcast generation"""

    episode_profile: str
    speaker_profile: str
    episode_name: str
    content: Optional[str] = None
    notebook_id: Optional[str] = None
    notebook_ids: Optional[list[str]] = None  # All notebooks that contributed content
    briefing_suffix: Optional[str] = None


class PodcastGenerationResponse(BaseModel):
    """Response model for podcast generation"""

    job_id: str
    status: str
    message: str
    episode_profile: str
    episode_name: str
    artifact_id: Optional[str] = None


class PodcastService:
    """Service layer for podcast operations"""

    @staticmethod
    async def submit_generation_job(
        episode_profile_name: str,
        speaker_profile_name: str,
        episode_name: str,
        notebook_id: Optional[str] = None,
        notebook_ids: Optional[list[str]] = None,
        content: Optional[str] = None,
        briefing_suffix: Optional[str] = None,
    ) -> Tuple[str, list[str]]:
        """Submit a podcast generation job for background processing.
        
        Returns:
            Tuple of (job_id, artifact_ids) - list of artifact IDs created for each notebook
        """
        logger.info(f"Submitting podcast generation: {episode_name}")
        logger.debug(f"Parameters: episode_profile={episode_profile_name}, speaker_profile={speaker_profile_name}")
        logger.debug(f"Notebooks: notebook_id={notebook_id}, notebook_ids={notebook_ids}")
        try:
            # Validate episode profile exists
            logger.debug(f"Validating episode profile: {episode_profile_name}")
            episode_profile = await EpisodeProfile.get_by_name(episode_profile_name)
            if not episode_profile:
                logger.error(f"Episode profile not found: {episode_profile_name}")
                raise ValueError(f"Episode profile '{episode_profile_name}' not found")

            # Validate speaker profile exists
            logger.debug(f"Validating speaker profile: {speaker_profile_name}")
            speaker_profile = await SpeakerProfile.get_by_name(speaker_profile_name)
            if not speaker_profile:
                logger.error(f"Speaker profile not found: {speaker_profile_name}")
                raise ValueError(f"Speaker profile '{speaker_profile_name}' not found")
            
            logger.debug(f"Validated profiles: episode={episode_profile_name}, speaker={speaker_profile_name}")

            # Get content from notebook if not provided directly
            if not content and notebook_id:
                try:
                    notebook = await Notebook.get(notebook_id)
                    # Get notebook context (this may need to be adjusted based on actual Notebook implementation)
                    content = (
                        await notebook.get_context()
                        if hasattr(notebook, "get_context")
                        else str(notebook)
                    )
                except Exception as e:
                    logger.warning(
                        "Failed to get notebook content, using notebook_id as content: {}", str(e)
                    )
                    content = f"Notebook ID: {notebook_id}"

            if not content:
                raise ValueError(
                    "Content is required - provide either content or notebook_id"
                )

            # Consolidate all notebook IDs (from both notebook_id and notebook_ids)
            all_notebook_ids: list[str] = []
            if notebook_ids:
                all_notebook_ids.extend(notebook_ids)
            if notebook_id and notebook_id not in all_notebook_ids:
                all_notebook_ids.append(notebook_id)

            # Prepare command arguments - pass all notebook IDs
            command_args = {
                "episode_profile": episode_profile_name,
                "speaker_profile": speaker_profile_name,
                "episode_name": episode_name,
                "content": str(content),
                "notebook_ids": all_notebook_ids if all_notebook_ids else None,
                "briefing_suffix": briefing_suffix,
            }

            # Ensure command modules are imported before submitting
            # This is needed because submit_command validates against local registry
            try:
                import commands.podcast_commands  # noqa: F401
            except ImportError as import_err:
                logger.error("Failed to import podcast commands: {}", str(import_err))
                raise ValueError("Podcast commands not available")

            # Submit command to surreal-commands
            logger.info(f"Submitting command to surreal-commands: open_notebook.generate_podcast")
            logger.debug(f"Command args: {command_args}")
            job_id = submit_command("open_notebook", "generate_podcast", command_args)

            # Convert RecordID to string if needed
            if not job_id:
                raise ValueError("Failed to get job_id from submit_command")
            job_id_str = str(job_id)
            logger.info(f"Command submitted successfully, job_id: {job_id_str}")
            
            # Create artifact records for ALL notebooks that contributed content
            # Use job_id as placeholder artifact_id (will be updated when episode is created)
            artifact_ids: list[str] = []
            for nb_id in all_notebook_ids:
                try:
                    artifact = await Artifact.create_for_artifact(
                        notebook_id=nb_id,
                        artifact_type="podcast",
                        artifact_id=job_id_str,  # Use job_id as placeholder
                        title=episode_name,
                    )
                    artifact_ids.append(str(artifact.id))
                    logger.info(
                        f"Created artifact {artifact.id} for podcast job {job_id_str} in notebook {nb_id}"
                    )
                except Exception as artifact_err:
                    logger.warning("Failed to create artifact record for notebook {}: {}", nb_id, str(artifact_err))
            
            logger.info(
                f"Submitted podcast generation job: {job_id_str} for episode '{episode_name}' "
                f"with {len(artifact_ids)} artifact(s) in {len(all_notebook_ids)} notebook(s)"
            )
            return job_id_str, artifact_ids

        except Exception as e:
            logger.error("Failed to submit podcast generation job: {}", str(e))
            raise HTTPException(
                status_code=500,
                detail=f"Failed to submit podcast generation job: {str(e)}",
            )

    @staticmethod
    async def get_job_status(job_id: str) -> Dict[str, Any]:
        """Get status of a podcast generation job"""
        logger.debug(f"Getting podcast job status for: {job_id}")
        try:
            # Ensure job_id has the command: prefix required by surreal_commands
            clean_job_id = job_id if job_id.startswith("command:") else f"command:{job_id}"
            if clean_job_id != job_id:
                logger.debug(f"Added prefix to job_id: {job_id} -> {clean_job_id}")

            status = await get_command_status(clean_job_id)
            
            if not status:
                logger.warning(f"Job status not found for job_id: {clean_job_id}")
                return {
                    "job_id": clean_job_id,
                    "status": "unknown",
                    "result": None,
                    "error_message": "Job not found",
                    "created": None,
                    "updated": None,
                    "progress": None,
                }
            
            return {
                "job_id": clean_job_id,
                "status": status.status if status else "unknown",
                "result": status.result if status else None,
                "error_message": getattr(status, "error_message", None)
                if status
                else None,
                "created": str(status.created)
                if status and hasattr(status, "created") and status.created
                else None,
                "updated": str(status.updated)
                if status and hasattr(status, "updated") and status.updated
                else None,
                "progress": getattr(status, "progress", None) if status else None,
            }
        except Exception as e:
            logger.error("Failed to get podcast job status for {}: {}", job_id, str(e))
            logger.exception(e)
            raise HTTPException(
                status_code=500, detail=f"Failed to get job status: {str(e)}"
            )

    @staticmethod
    async def list_episodes() -> list:
        """List all podcast episodes"""
        try:
            episodes = await PodcastEpisode.get_all(order_by="created desc")
            return episodes
        except Exception as e:
            logger.error("Failed to list podcast episodes: {}", str(e))
            raise HTTPException(
                status_code=500, detail=f"Failed to list episodes: {str(e)}"
            )

    @staticmethod
    async def get_episode(episode_id: str) -> PodcastEpisode:
        """Get a specific podcast episode"""
        try:
            episode = await PodcastEpisode.get(episode_id)
            return episode
        except Exception as e:
            logger.error("Failed to get podcast episode {}: {}", episode_id, str(e))
            raise HTTPException(status_code=404, detail=f"Episode not found: {str(e)}")


class DefaultProfiles:
    """Utility class for creating default profiles (if needed beyond migration data)"""

    @staticmethod
    async def create_default_episode_profiles():
        """Create default episode profiles if they don't exist"""
        try:
            # Check if profiles already exist
            existing = await EpisodeProfile.get_all()
            if existing:
                logger.info(f"Episode profiles already exist: {len(existing)} found")
                return existing

            # This would create profiles, but since we have migration data,
            # this is mainly for future extensibility
            logger.info(
                "Default episode profiles should be created via database migration"
            )
            return []

        except Exception as e:
            logger.error("Failed to create default episode profiles: {}", str(e))
            raise

    @staticmethod
    async def create_default_speaker_profiles():
        """Create default speaker profiles if they don't exist"""
        try:
            # Check if profiles already exist
            existing = await SpeakerProfile.get_all()
            if existing:
                logger.info(f"Speaker profiles already exist: {len(existing)} found")
                return existing

            # This would create profiles, but since we have migration data,
            # this is mainly for future extensibility
            logger.info(
                "Default speaker profiles should be created via database migration"
            )
            return []

        except Exception as e:
            logger.error("Failed to create default speaker profiles: {}", str(e))
            raise
