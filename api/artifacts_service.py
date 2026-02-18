"""Artifacts service for unified artifact management."""

from typing import List, Optional

from loguru import logger

from open_notebook.database.repository import repo_query, ensure_record_id
from open_notebook.domain.artifact import Artifact


async def get_notebook_artifacts(notebook_id: str) -> List[Artifact]:
    """Get all artifacts for a notebook."""
    logger.debug(f"Fetching artifacts for notebook: {notebook_id}")
    try:
        result = await repo_query(
            """
            SELECT * FROM artifact 
            WHERE notebook_id = $notebook_id 
            ORDER BY created DESC
            """,
            {"notebook_id": ensure_record_id(notebook_id)},
        )
        artifacts = [Artifact(**r) for r in result] if result else []
        logger.info(f"Found {len(artifacts)} artifacts for notebook {notebook_id}")
        return artifacts
    except Exception as e:
        logger.error("Error getting artifacts for notebook {}: {}", notebook_id, str(e))
        return []


async def get_notebook_artifacts_by_type(
    notebook_id: str, artifact_type: str
) -> List[Artifact]:
    """Get artifacts of a specific type for a notebook."""
    logger.debug(f"Fetching {artifact_type} artifacts for notebook: {notebook_id}")
    try:
        result = await repo_query(
            """
            SELECT * FROM artifact 
            WHERE notebook_id = $notebook_id AND artifact_type = $artifact_type
            ORDER BY created DESC
            """,
            {
                "notebook_id": ensure_record_id(notebook_id),
                "artifact_type": artifact_type,
            },
        )
        artifacts = [Artifact(**r) for r in result] if result else []
        logger.info(f"Found {len(artifacts)} {artifact_type} artifacts for notebook {notebook_id}")
        return artifacts
    except Exception as e:
        logger.error(
            "Error getting {} artifacts for notebook {}: {}", artifact_type, notebook_id, str(e)
        )
        return []


async def get_artifact(artifact_id: str) -> Optional[Artifact]:
    """Get an artifact by ID."""
    logger.debug(f"Fetching artifact: {artifact_id}")
    try:
        artifact = await Artifact.get(artifact_id)
        if artifact:
            logger.debug(f"Found artifact {artifact_id}: type={artifact.artifact_type}, content_id={artifact.artifact_id}")
        else:
            logger.warning(f"Artifact not found: {artifact_id}")
        return artifact
    except Exception as e:
        logger.error("Error getting artifact {}: {}", artifact_id, str(e))
        return None


async def delete_artifact(artifact_id: str) -> bool:
    """Delete an artifact and its associated content."""
    logger.info(f"Deleting artifact: {artifact_id}")
    try:
        artifact = await Artifact.get(artifact_id)
        if not artifact:
            logger.warning(f"Cannot delete - artifact not found: {artifact_id}")
            return False

        logger.debug(f"Deleting artifact {artifact_id}: type={artifact.artifact_type}, content_id={artifact.artifact_id}")
        success = await artifact.delete_with_content()
        if success:
            logger.info(f"Successfully deleted artifact {artifact_id} and its content")
        else:
            logger.warning(f"Failed to delete artifact {artifact_id}")
        return success
    except Exception as e:
        logger.error("Error deleting artifact {}: {}", artifact_id, str(e))
        return False


async def get_artifact_with_preview(artifact_id: str) -> Optional[dict]:
    """
    Get artifact with type-specific preview data.

    Returns preview data formatted according to artifact type:
    - quiz: questions with answers, question count
    - podcast: audio URL, transcript, duration
    - summary: content, word count
    - transformation: content, word count, transformation name
    """
    logger.debug(f"Getting artifact preview for: {artifact_id}")
    try:
        artifact = await Artifact.get(artifact_id)
        if not artifact:
            logger.warning(f"Artifact not found: {artifact_id}")
            return None

        # Get type-specific preview data
        preview_data = await get_artifact_preview_data(artifact)
        return preview_data

    except Exception as e:
        logger.error("Error getting artifact preview {}: {}", artifact_id, str(e))
        return None


async def regenerate_artifact(artifact_id: str) -> dict:
    """
    Regenerate an artifact by deleting old and creating new with same parameters.

    Args:
        artifact_id: ID of the artifact to regenerate

    Returns:
        Dictionary with regeneration status and new artifact info
    """
    logger.info(f"Regenerating artifact: {artifact_id}")
    try:
        # Get the existing artifact
        artifact = await Artifact.get(artifact_id)
        if not artifact:
            logger.error(f"Artifact not found: {artifact_id}")
            return {
                "status": "error",
                "artifact_id": artifact_id,
                "error": "Artifact not found",
            }

        # Store metadata before deletion
        artifact_type = artifact.artifact_type
        notebook_id = artifact.notebook_id
        title = artifact.title

        logger.debug(f"Regenerating {artifact_type} artifact for notebook {notebook_id}")

        # Delete old artifact
        delete_success = await delete_artifact(artifact_id)
        if not delete_success:
            logger.error(f"Failed to delete old artifact: {artifact_id}")
            return {
                "status": "error",
                "artifact_id": artifact_id,
                "artifact_type": artifact_type,
                "error": "Failed to delete old artifact",
            }

        # Regenerate based on type
        if artifact_type == "quiz":
            from api.artifact_generation_service import generate_quiz_artifact
            status, new_id, error = await generate_quiz_artifact(notebook_id)
            return {
                "status": status,
                "artifact_id": artifact_id,
                "artifact_type": "quiz",
                "new_artifact_id": new_id,
                "error": error,
            }

        elif artifact_type == "summary":
            from api.artifact_generation_service import generate_summary_artifact
            status, new_id, error = await generate_summary_artifact(notebook_id)
            return {
                "status": status,
                "artifact_id": artifact_id,
                "artifact_type": "summary",
                "new_artifact_id": new_id,
                "error": error,
            }

        elif artifact_type == "podcast":
            from api.artifact_generation_service import generate_podcast_artifact
            status, command_id, artifact_ids, error = await generate_podcast_artifact(notebook_id)
            return {
                "status": status,
                "artifact_id": artifact_id,
                "artifact_type": "podcast",
                "command_id": command_id,
                "new_artifact_ids": artifact_ids,
                "error": error,
            }

        elif artifact_type == "transformation":
            # Transformations require transformation_id which we don't store
            # For now, return error - this would need enhancement
            logger.warning(f"Transformation regeneration not fully supported")
            return {
                "status": "error",
                "artifact_id": artifact_id,
                "artifact_type": "transformation",
                "error": "Transformation regeneration requires transformation_id (not yet supported)",
            }

        else:
            logger.error(f"Unsupported artifact type for regeneration: {artifact_type}")
            return {
                "status": "error",
                "artifact_id": artifact_id,
                "artifact_type": artifact_type,
                "error": f"Artifact type '{artifact_type}' regeneration not supported",
            }

    except Exception as e:
        logger.error("Error regenerating artifact {}: {}", artifact_id, str(e))
        logger.exception(e)
        return {
            "status": "error",
            "artifact_id": artifact_id,
            "error": str(e),
        }


async def get_artifact_preview_data(artifact: Artifact) -> dict:
    """
    Get type-specific preview data for an artifact.

    Args:
        artifact: The artifact to get preview data for

    Returns:
        Dictionary with type-specific preview information
    """
    from open_notebook.domain.quiz import Quiz
    from open_notebook.domain.notebook import Note
    from open_notebook.podcasts.models import PodcastEpisode

    artifact_type = artifact.artifact_type
    artifact_id = artifact.artifact_id

    try:
        if artifact_type == "quiz":
            # Get quiz with questions
            quiz = await Quiz.get(artifact_id)
            if not quiz:
                return {
                    "artifact_type": "quiz",
                    "error": "Quiz not found",
                }

            # Format questions for preview
            questions_data = []
            for q in quiz.questions:
                questions_data.append({
                    "question": q.question,
                    "options": q.options,
                    "correct_answer": q.correct_answer,
                    "explanation": q.explanation,
                })

            return {
                "artifact_type": "quiz",
                "id": quiz.id,
                "title": quiz.title or artifact.title,
                "question_count": len(quiz.questions),
                "questions": questions_data,
            }

        elif artifact_type == "podcast":
            # If artifact_id is still a job placeholder (command:xxx), podcast isn't ready yet
            if artifact.artifact_id.startswith("command:"):
                return {
                    "artifact_type": "podcast",
                    "id": artifact.artifact_id,
                    "title": artifact.title or "Podcast",
                    "status": "generating",
                    "error": "Podcast is still being generated",
                }
            # Get podcast episode
            podcast = await PodcastEpisode.get(artifact_id)
            if not podcast:
                return {
                    "artifact_type": "podcast",
                    "error": "Podcast not found",
                }

            # Route to the correct audio endpoint based on ID prefix:
            # - episode:xxx → /api/podcasts/episodes/{id}/audio
            # - podcast:xxx → /api/podcasts/{id}/audio
            audio_url = None
            if podcast.audio_file:
                pid = str(podcast.id)
                if pid.startswith("episode:"):
                    audio_url = f"/api/podcasts/episodes/{pid}/audio"
                else:
                    audio_url = f"/api/podcasts/{pid}/audio"

            return {
                "artifact_type": "podcast",
                "id": podcast.id,
                "title": podcast.name or artifact.title,
                "audio_url": audio_url,
                "transcript": podcast.transcript,
            }

        elif artifact_type in ("summary", "transformation"):
            # Get note content
            note = await Note.get(artifact_id)
            if not note:
                return {
                    "artifact_type": artifact_type,
                    "error": "Note not found",
                }

            # Calculate word count
            word_count = len(note.content.split()) if note.content else 0

            result = {
                "artifact_type": artifact_type,
                "id": note.id,
                "title": note.title or artifact.title,
                "word_count": word_count,
                "content": note.content,
            }

            # Add transformation name for transformation artifacts
            if artifact_type == "transformation":
                # Extract transformation name from title (format: "TransformationName - NotebookName")
                title_parts = artifact.title.split(" - ")
                if len(title_parts) > 0:
                    result["transformation_name"] = title_parts[0]

            return result

        else:
            logger.warning(f"Unknown artifact type: {artifact_type}")
            return {
                "artifact_type": artifact_type,
                "error": f"Unknown artifact type: {artifact_type}",
            }

    except Exception as e:
        logger.error("Error getting preview data for artifact {}: {}", artifact.id, str(e))
        return {
            "artifact_type": artifact_type,
            "error": str(e),
        }
