"""
Artifact generation service for batch artifact generation.

Orchestrates parallel generation of quizzes, summaries, transformations,
and async podcast generation for notebooks.
"""

import asyncio
from typing import Dict, List, Optional, Tuple
from loguru import logger

from open_notebook.domain.artifact import Artifact
from open_notebook.domain.notebook import Notebook, Source, Note
from open_notebook.domain.transformation import Transformation
from open_notebook.database.repository import repo_query, ensure_record_id
from api import quiz_service
from api.podcast_service import PodcastService


class BatchGenerationStatus:
    """Status container for batch artifact generation."""

    def __init__(self):
        self.quiz_status: str = "pending"
        self.quiz_id: Optional[str] = None
        self.quiz_error: Optional[str] = None

        self.summary_status: str = "pending"
        self.summary_id: Optional[str] = None
        self.summary_error: Optional[str] = None

        self.transformations_status: str = "pending"
        self.transformation_ids: List[str] = []
        self.transformation_errors: List[str] = []

        self.podcast_status: str = "pending"
        self.podcast_command_id: Optional[str] = None
        self.podcast_artifact_ids: List[str] = []
        self.podcast_error: Optional[str] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary for API response."""
        return {
            "quiz": {
                "status": self.quiz_status,
                "id": self.quiz_id,
                "error": self.quiz_error,
            },
            "summary": {
                "status": self.summary_status,
                "id": self.summary_id,
                "error": self.summary_error,
            },
            "transformations": {
                "status": self.transformations_status,
                "ids": self.transformation_ids,
                "errors": self.transformation_errors,
            },
            "podcast": {
                "status": self.podcast_status,
                "command_id": self.podcast_command_id,
                "artifact_ids": self.podcast_artifact_ids,
                "error": self.podcast_error,
            },
        }


async def generate_quiz_artifact(notebook_id: str) -> Tuple[str, Optional[str], Optional[str]]:
    """
    Generate quiz for notebook.

    Returns:
        Tuple of (status, quiz_id, error_message)
    """
    try:
        logger.info(f"Generating quiz for notebook {notebook_id}")
        result = await quiz_service.generate_quiz(
            notebook_id=notebook_id,
            num_questions=5,
        )

        if result.get("error"):
            logger.error(f"Quiz generation failed: {result['error']}")
            return ("error", None, result["error"])

        quiz_id = result.get("quiz_id")
        if not quiz_id:
            logger.error("Quiz generation returned no quiz_id")
            return ("error", None, "Quiz generation failed: no quiz_id returned")

        logger.info(f"Quiz generated successfully: {quiz_id}")
        return ("completed", quiz_id, None)

    except Exception as e:
        logger.error("Quiz generation exception: {}", str(e))
        logger.exception(e)
        return ("error", None, str(e))


async def generate_summary_artifact(notebook_id: str) -> Tuple[str, Optional[str], Optional[str]]:
    """
    Generate summary transformation for notebook.

    Returns:
        Tuple of (status, summary_id, error_message)
    """
    try:
        logger.info(f"Generating summary for notebook {notebook_id}")

        # Get the "summary" transformation (create if doesn't exist)
        summary_transformation = await get_or_create_summary_transformation()

        if not summary_transformation:
            logger.error("Failed to get or create summary transformation")
            return ("error", None, "Summary transformation not available")

        # Execute summary transformation on notebook content
        from open_notebook.graphs.transformation import graph as transformation_graph

        # Get notebook sources
        notebook = await Notebook.get(notebook_id)
        if not notebook:
            return ("error", None, "Notebook not found")

        # Fetch sources WITH full_text
        srcs = await repo_query(
            """
            select in as source from reference where out=$id
            fetch source
            """,
            {"id": ensure_record_id(notebook_id)},
        )
        sources = [Source(**src["source"]) for src in srcs] if srcs else []

        if not sources:
            logger.warning(f"No sources found for notebook {notebook_id}")
            return ("error", None, "No sources found in notebook")

        # Combine source content (limit per source)
        content_parts = []
        for source in sources[:5]:  # Limit to first 5 sources
            if source.full_text:
                text = source.full_text[:10000] if len(source.full_text) > 10000 else source.full_text
                title = source.title or "Untitled Source"
                content_parts.append(f"## {title}\n\n{text}")

        if not content_parts:
            return ("error", None, "No text content found in sources")

        combined_content = "\n\n---\n\n".join(content_parts)

        # Limit total content
        max_content_length = 50000
        if len(combined_content) > max_content_length:
            combined_content = combined_content[:max_content_length] + "\n\n[Content truncated...]"

        # Execute transformation
        result = await transformation_graph.ainvoke(
            dict(
                input_text=combined_content,
                transformation=summary_transformation,
            ),
            config=dict(configurable={"model_id": None}),
        )

        transformed_content = result.get("output", "")
        if not transformed_content:
            return ("error", None, "Summary generation returned empty result")

        # Create note with summary result
        note_title = f"Summary - {notebook.name}"
        note = Note(
            title=note_title,
            content=transformed_content,
            note_type="ai",
        )
        await note.save()

        # Create artifact tracker
        await Artifact.create_for_artifact(
            notebook_id=notebook_id,
            artifact_type="summary",
            artifact_id=note.id,
            title=note_title,
        )

        logger.info(f"Summary generated successfully: {note.id}")
        return ("completed", note.id, None)

    except Exception as e:
        logger.error("Summary generation exception: {}", str(e))
        logger.exception(e)
        return ("error", None, str(e))


async def generate_podcast_artifact(notebook_id: str) -> Tuple[str, Optional[str], List[str], Optional[str]]:
    """
    Submit async podcast generation job for notebook.

    Returns:
        Tuple of (status, command_id, artifact_ids, error_message)
    """
    try:
        logger.info(f"Submitting podcast generation for notebook {notebook_id}")

        # Get notebook for title
        notebook = await Notebook.get(notebook_id)
        if not notebook:
            return ("error", None, [], "Notebook not found")

        # Check that required podcast profiles exist before attempting generation
        from open_notebook.podcasts.models import EpisodeProfile, SpeakerProfile

        episode_profile = await EpisodeProfile.get_by_name("overview")
        if not episode_profile:
            logger.info("Podcast skipped: no 'overview' episode profile configured")
            return ("skipped", None, [], None)

        speaker_profile = await SpeakerProfile.get_by_name("alex_sarah")
        if not speaker_profile:
            logger.info("Podcast skipped: no 'alex_sarah' speaker profile configured")
            return ("skipped", None, [], None)

        # Submit podcast generation job with default profiles
        episode_name = f"{notebook.name} - Overview"

        command_id, artifact_ids = await PodcastService.submit_generation_job(
            episode_profile_name="overview",
            speaker_profile_name="alex_sarah",
            episode_name=episode_name,
            notebook_id=notebook_id,
        )

        logger.info(f"Podcast job submitted: command={command_id}, artifacts={artifact_ids}")
        return ("processing", command_id, artifact_ids, None)

    except Exception as e:
        logger.error("Podcast generation exception: {}", str(e))
        logger.exception(e)
        return ("error", None, [], str(e))


async def get_or_create_summary_transformation() -> Optional[Transformation]:
    """Get or create the summary transformation."""
    try:
        # Try to find existing summary transformation
        result = await repo_query(
            "SELECT * FROM transformation WHERE name = 'summary' LIMIT 1"
        )

        if result and len(result) > 0:
            return Transformation(**result[0])

        # Create default summary transformation if not exists
        summary = Transformation(
            name="summary",
            title="Summary",
            description="Generate a concise summary of the content",
            prompt="Create a comprehensive summary of the following content. Focus on the main ideas, key points, and important details:\n\n{{input_text}}",
            apply_default=True,
        )
        await summary.save()
        logger.info("Created default summary transformation")
        return summary

    except Exception as e:
        logger.error("Error getting/creating summary transformation: {}", str(e))
        return None


async def generate_all_artifacts(notebook_id: str) -> BatchGenerationStatus:
    """
    Orchestrate parallel artifact generation for a notebook.

    Generates:
    - Quiz (sync, 30-60s)
    - Summary (sync, 10-30s)
    - Podcast (async, fire-and-forget)

    Uses asyncio.gather with error isolation so one failure doesn't break others.

    Args:
        notebook_id: ID of the notebook

    Returns:
        BatchGenerationStatus with results for each artifact type
    """
    logger.info(f"Starting batch artifact generation for notebook {notebook_id}")
    status = BatchGenerationStatus()

    try:
        # Validate notebook exists
        notebook = await Notebook.get(notebook_id)
        if not notebook:
            logger.error(f"Notebook not found: {notebook_id}")
            status.quiz_status = "error"
            status.quiz_error = "Notebook not found"
            status.summary_status = "error"
            status.summary_error = "Notebook not found"
            status.podcast_status = "error"
            status.podcast_error = "Notebook not found"
            return status

        # Execute sync operations in parallel with error isolation
        results = await asyncio.gather(
            generate_quiz_artifact(notebook_id),
            generate_summary_artifact(notebook_id),
            return_exceptions=True,  # Don't fail entire batch if one fails
        )

        # Process quiz result
        if isinstance(results[0], Exception):
            status.quiz_status = "error"
            status.quiz_error = str(results[0])
            logger.error("Quiz generation failed with exception: {}", str(results[0]))
        else:
            quiz_status, quiz_id, quiz_error = results[0]
            status.quiz_status = quiz_status
            status.quiz_id = quiz_id
            status.quiz_error = quiz_error

        # Process summary result
        if isinstance(results[1], Exception):
            status.summary_status = "error"
            status.summary_error = str(results[1])
            logger.error("Summary generation failed with exception: {}", str(results[1]))
        else:
            summary_status, summary_id, summary_error = results[1]
            status.summary_status = summary_status
            status.summary_id = summary_id
            status.summary_error = summary_error

        # Fire-and-forget podcast generation (doesn't block)
        podcast_status, command_id, artifact_ids, podcast_error = await generate_podcast_artifact(notebook_id)
        status.podcast_status = podcast_status
        status.podcast_command_id = command_id
        status.podcast_artifact_ids = artifact_ids
        status.podcast_error = podcast_error

        logger.info(f"Batch generation complete for notebook {notebook_id}")
        logger.info(f"  Quiz: {status.quiz_status}")
        logger.info(f"  Summary: {status.summary_status}")
        logger.info(f"  Podcast: {status.podcast_status}")

        return status

    except Exception as e:
        logger.error("Batch generation failed with unexpected error: {}", str(e))
        logger.exception(e)
        status.quiz_status = "error"
        status.quiz_error = f"Unexpected error: {str(e)}"
        status.summary_status = "error"
        status.summary_error = f"Unexpected error: {str(e)}"
        status.podcast_status = "error"
        status.podcast_error = f"Unexpected error: {str(e)}"
        return status
