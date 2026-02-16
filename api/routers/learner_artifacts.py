"""Learner artifact creation endpoints: podcast, quiz, transformation."""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from loguru import logger
from pydantic import BaseModel, Field

from api.auth import get_current_learner, LearnerContext
from api.routers.artifacts import validate_learner_access_to_notebook
from open_notebook.database.repository import repo_query, ensure_record_id
from open_notebook.domain.artifact import Artifact
from open_notebook.domain.notebook import Source

router = APIRouter()


# ============================================================================
# Request/Response Models
# ============================================================================


class LearnerPodcastRequest(BaseModel):
    episode_profile: str = Field(..., description="Episode profile name")
    episode_name: str = Field(..., description="Name for the podcast episode")
    source_ids: List[str] = Field(..., min_length=1, description="Source IDs to use")
    instructions: Optional[str] = Field(None, description="Additional instructions")


class LearnerPodcastResponse(BaseModel):
    job_id: str
    status: str = "submitted"
    artifact_id: Optional[str] = None


class LearnerQuizRequest(BaseModel):
    source_ids: Optional[List[str]] = Field(None, description="Source IDs to use")
    topic: Optional[str] = Field(None, description="Quiz topic focus")
    num_questions: int = Field(5, ge=1, le=10, description="Number of questions")


class LearnerTransformationRequest(BaseModel):
    transformation_id: str = Field(..., description="Transformation ID to execute")
    source_ids: List[str] = Field(..., min_length=1, description="Source IDs to use")
    instructions: Optional[str] = Field(None, description="Additional instructions")


class LearnerTransformationResponse(BaseModel):
    artifact_id: str
    title: str
    content_preview: str


# ============================================================================
# Shared Helpers
# ============================================================================


async def build_content_from_sources(
    notebook_id: str, source_ids: List[str]
) -> str:
    """Build concatenated text content from sources belonging to a notebook.

    Validates that all source_ids are associated with the notebook via
    the 'reference' relationship table, then fetches full text.

    Args:
        notebook_id: Notebook record ID
        source_ids: List of source record IDs

    Returns:
        Concatenated text with source titles as headers

    Raises:
        HTTPException 400: If no valid sources found or source_ids don't belong to notebook
    """
    if not source_ids:
        raise HTTPException(status_code=400, detail="At least one source is required")

    # Validate source_ids belong to the notebook via reference edges
    safe_ids = [ensure_record_id(sid) for sid in source_ids]
    valid_result = await repo_query(
        """
        SELECT VALUE in FROM reference
        WHERE out = $notebook_id AND in IN $source_ids
        """,
        {"notebook_id": ensure_record_id(notebook_id), "source_ids": safe_ids},
    )

    valid_source_ids = set()
    if valid_result:
        for item in valid_result:
            valid_source_ids.add(str(item))

    if not valid_source_ids:
        raise HTTPException(
            status_code=400,
            detail="None of the selected sources belong to this notebook",
        )

    # Fetch source full_text for valid sources
    content_parts = []
    for sid in source_ids:
        sid_str = str(ensure_record_id(sid))
        if sid_str not in valid_source_ids:
            continue
        try:
            source = await Source.get(sid)
            if source and source.full_text:
                title = source.title or "Untitled Source"
                text = source.full_text[:30000]  # Cap at 30K chars per source
                content_parts.append(f"# {title}\n\n{text}")
        except Exception as e:
            logger.warning(f"Failed to fetch source {sid}: {e}")

    if not content_parts:
        raise HTTPException(
            status_code=400, detail="No content found in selected sources"
        )

    return "\n\n---\n\n".join(content_parts)


# ============================================================================
# Endpoint 1: Podcast Generation
# ============================================================================


@router.post("/learner/notebooks/{notebook_id}/podcasts/generate")
async def learner_generate_podcast(
    notebook_id: str,
    request: LearnerPodcastRequest,
    learner: LearnerContext = Depends(get_current_learner),
) -> LearnerPodcastResponse:
    """Generate a podcast from selected sources (learner-scoped).

    Validates notebook access, builds content from sources server-side,
    and submits a podcast generation job.
    """
    await validate_learner_access_to_notebook(notebook_id, learner)

    try:
        # Build content from source_ids
        content = await build_content_from_sources(notebook_id, request.source_ids)

        # Resolve speaker_config from episode profile
        from open_notebook.podcasts.models import EpisodeProfile

        episode_profile = await EpisodeProfile.get_by_name(request.episode_profile)
        if not episode_profile:
            raise HTTPException(
                status_code=400,
                detail=f"Episode profile '{request.episode_profile}' not found",
            )
        speaker_profile_name = episode_profile.speaker_config

        # Build briefing_suffix from instructions if provided
        briefing_suffix = request.instructions

        # Submit generation job
        from api.podcast_service import PodcastService

        job_id, artifact_ids = await PodcastService.submit_generation_job(
            episode_profile_name=request.episode_profile,
            speaker_profile_name=speaker_profile_name,
            episode_name=request.episode_name,
            notebook_id=notebook_id,
            content=content,
            briefing_suffix=briefing_suffix,
        )

        # Update artifact(s) with created_by
        for art_id in artifact_ids:
            try:
                await repo_query(
                    "UPDATE $art_id SET created_by = $user_id",
                    {"art_id": ensure_record_id(art_id), "user_id": str(learner.user.id)},
                )
            except Exception as e:
                logger.warning(f"Failed to set created_by on artifact {art_id}: {e}")

        logger.info(
            f"Learner {learner.user.id} started podcast generation in notebook {notebook_id}, job_id={job_id}"
        )

        return LearnerPodcastResponse(
            job_id=job_id,
            status="submitted",
            artifact_id=artifact_ids[0] if artifact_ids else None,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating learner podcast: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate podcast: {str(e)}")


# ============================================================================
# Endpoint 2: Quiz Generation
# ============================================================================


@router.post("/learner/notebooks/{notebook_id}/quizzes/generate")
async def learner_generate_quiz(
    notebook_id: str,
    request: LearnerQuizRequest,
    learner: LearnerContext = Depends(get_current_learner),
):
    """Generate a quiz from notebook sources (learner-scoped).

    Validates notebook access, then generates quiz using existing workflow.
    Quiz generation is synchronous and may take 30-60 seconds.
    """
    await validate_learner_access_to_notebook(notebook_id, learner)

    try:
        # Validate source_ids belong to notebook if provided
        if request.source_ids:
            safe_ids = [ensure_record_id(sid) for sid in request.source_ids]
            valid_result = await repo_query(
                """
                SELECT VALUE in FROM reference
                WHERE out = $notebook_id AND in IN $source_ids
                """,
                {"notebook_id": ensure_record_id(notebook_id), "source_ids": safe_ids},
            )
            if not valid_result:
                raise HTTPException(
                    status_code=400,
                    detail="None of the selected sources belong to this notebook",
                )

        # Generate quiz using existing service
        from api import quiz_service

        result = await quiz_service.generate_quiz(
            notebook_id=notebook_id,
            topic=request.topic,
            num_questions=request.num_questions,
            source_ids=request.source_ids,
            user_id=str(learner.user.id),
            company_id=str(learner.company_id),
        )

        if result.get("error"):
            raise HTTPException(status_code=400, detail=result["error"])

        # Update artifact created_by for the quiz
        quiz_id = result.get("quiz_id")
        if quiz_id:
            try:
                await repo_query(
                    """
                    UPDATE artifact SET created_by = $user_id
                    WHERE artifact_id = $quiz_id AND notebook_id = $notebook_id
                    """,
                    {
                        "user_id": str(learner.user.id),
                        "quiz_id": quiz_id,
                        "notebook_id": ensure_record_id(notebook_id),
                    },
                )
            except Exception as e:
                logger.warning(f"Failed to set created_by on quiz artifact: {e}")

        logger.info(
            f"Learner {learner.user.id} generated quiz in notebook {notebook_id}"
        )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating learner quiz: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate quiz: {str(e)}")


# ============================================================================
# Endpoint 3: Transformation Execution
# ============================================================================


@router.post("/learner/notebooks/{notebook_id}/transformations/execute")
async def learner_execute_transformation(
    notebook_id: str,
    request: LearnerTransformationRequest,
    learner: LearnerContext = Depends(get_current_learner),
) -> LearnerTransformationResponse:
    """Execute a transformation on selected sources (learner-scoped).

    Validates notebook access, builds content from sources,
    executes transformation, and creates a Note + Artifact.
    """
    await validate_learner_access_to_notebook(notebook_id, learner)

    try:
        # Build content from sources
        content = await build_content_from_sources(notebook_id, request.source_ids)

        # Validate transformation exists
        from open_notebook.domain.transformation import Transformation

        transformation = await Transformation.get(request.transformation_id)
        if not transformation:
            raise HTTPException(status_code=404, detail="Transformation not found")

        # Prepend instructions if provided
        input_text = content
        if request.instructions:
            input_text = f"Additional instructions: {request.instructions}\n\n{content}"

        # Execute transformation graph
        from open_notebook.graphs.transformation import graph as transformation_graph

        result = await transformation_graph.ainvoke(
            dict(
                input_text=input_text,
                transformation=transformation,
            ),
            config=dict(configurable={}),
        )

        output = result.get("output", "")

        # Create Note with the result
        from open_notebook.domain.notebook import Note

        note_title = f"{transformation.title}"
        note = Note(
            title=note_title,
            content=output,
            note_type="ai",
        )
        await note.save()

        # Link note to notebook
        await note.add_to_notebook(notebook_id)

        # Create Artifact tracker
        artifact = await Artifact.create_for_artifact(
            notebook_id=notebook_id,
            artifact_type="transformation",
            artifact_id=note.id,
            title=note_title,
            created_by=str(learner.user.id),
        )

        logger.info(
            f"Learner {learner.user.id} executed transformation '{transformation.title}' in notebook {notebook_id}"
        )

        return LearnerTransformationResponse(
            artifact_id=artifact.id or "",
            title=note_title,
            content_preview=output[:500] if output else "",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error executing learner transformation: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to execute transformation: {str(e)}"
        )
