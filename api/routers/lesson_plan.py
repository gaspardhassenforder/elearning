"""Lesson Plan API endpoints.

Provides admin endpoints for generating and managing lesson steps,
and learner endpoints for tracking step completion progress.
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from loguru import logger

from api import lesson_plan_service
from api.auth import LearnerContext, get_current_learner, require_admin
from api.learner_chat_service import validate_learner_access_to_notebook
from api.models import (
    LessonStepCreate,
    LessonStepUpdate,
    LessonStepResponse,
    LessonStepReorder,
    LessonPlanGenerationResponse,
    LearnerStepProgressResponse,
)
from open_notebook.domain.lesson_step import LessonStep
from open_notebook.domain.learner_step_progress import LearnerStepProgress
from open_notebook.domain.user import User

# Admin router for lesson plan management
router = APIRouter()

# Learner router for progress tracking
learner_router = APIRouter()


@router.post(
    "/notebooks/{notebook_id}/lesson-steps/generate",
    response_model=LessonPlanGenerationResponse,
    dependencies=[Depends(require_admin)],
)
async def generate_lesson_plan(notebook_id: str):
    """Generate a lesson plan for a notebook using AI.

    Analyzes the notebook's sources and creates an ordered set of lesson steps
    with appropriate types (watch/read/quiz/discuss).

    Args:
        notebook_id: Notebook record ID

    Returns:
        LessonPlanGenerationResponse with status and step IDs
    """
    logger.info(f"Admin triggering lesson plan generation for notebook {notebook_id}")

    result = await lesson_plan_service.generate_lesson_plan(notebook_id)

    if result.get("error"):
        if "not found" in result["error"]:
            raise HTTPException(status_code=404, detail=result["error"])
        elif "No sources" in result["error"]:
            raise HTTPException(status_code=400, detail=result["error"])
        else:
            raise HTTPException(status_code=500, detail=result["error"])

    return LessonPlanGenerationResponse(
        status=result["status"],
        step_ids=result.get("step_ids"),
        error=result.get("error"),
    )


@router.get(
    "/notebooks/{notebook_id}/lesson-steps",
    response_model=List[LessonStepResponse],
)
async def list_lesson_steps(
    notebook_id: str,
    user: User = Depends(require_admin),
):
    """Get ordered list of lesson steps for a notebook (admin).

    Args:
        notebook_id: Notebook record ID

    Returns:
        Ordered list of LessonStepResponse
    """
    steps = await lesson_plan_service.list_steps_with_source_titles(notebook_id)
    return [LessonStepResponse(**step) for step in steps]


@router.put(
    "/lesson-steps/{step_id}",
    response_model=LessonStepResponse,
    dependencies=[Depends(require_admin)],
)
async def update_lesson_step(step_id: str, data: LessonStepUpdate):
    """Update a lesson step (admin only).

    Args:
        step_id: Step record ID
        data: Fields to update

    Returns:
        Updated LessonStepResponse
    """
    from open_notebook.database.repository import repo_update

    # Build update dict (only include non-None fields)
    update_data = {}
    if data.title is not None:
        update_data["title"] = data.title
    if data.step_type is not None:
        update_data["step_type"] = data.step_type
    if data.source_id is not None:
        update_data["source_id"] = data.source_id
    if data.discussion_prompt is not None:
        update_data["discussion_prompt"] = data.discussion_prompt
    if data.order is not None:
        update_data["order"] = data.order
    if data.required is not None:
        update_data["required"] = data.required

    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")

    try:
        result = await repo_update("lesson_step", step_id, update_data)
        if not result:
            raise HTTPException(status_code=404, detail="Lesson step not found")

        step = LessonStep(**result)
        # Resolve source title if applicable
        source_title = None
        if step.source_id:
            from open_notebook.database.repository import repo_query, ensure_record_id

            title_result = await repo_query(
                "SELECT VALUE title FROM $id",
                {"id": ensure_record_id(step.source_id)},
            )
            if title_result:
                source_title = str(title_result[0]) if title_result[0] else None

        return LessonStepResponse(
            id=str(step.id),
            notebook_id=step.notebook_id,
            title=step.title,
            step_type=step.step_type,
            source_id=step.source_id,
            source_title=source_title,
            discussion_prompt=step.discussion_prompt,
            order=step.order,
            required=step.required,
            auto_generated=step.auto_generated,
            created=str(step.created) if step.created else None,
            updated=str(step.updated) if step.updated else None,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating lesson step {step_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update lesson step")


@router.delete(
    "/lesson-steps/{step_id}",
    dependencies=[Depends(require_admin)],
)
async def delete_lesson_step(step_id: str):
    """Delete a lesson step (admin only).

    Args:
        step_id: Step record ID
    """
    try:
        await LessonStep.delete_by_id(step_id)
        return {"message": "Lesson step deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting lesson step {step_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete lesson step")


@router.post(
    "/notebooks/{notebook_id}/lesson-steps/reorder",
    dependencies=[Depends(require_admin)],
)
async def reorder_lesson_steps(notebook_id: str, data: LessonStepReorder):
    """Bulk reorder lesson steps (admin only).

    Args:
        notebook_id: Notebook record ID (for URL consistency)
        data: List of {id, order} dicts
    """
    if not data.steps:
        raise HTTPException(status_code=400, detail="No steps provided")

    try:
        await LessonStep.reorder_steps(data.steps)
        return {"message": f"Successfully reordered {len(data.steps)} steps"}
    except Exception as e:
        logger.error(f"Error reordering lesson steps: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to reorder lesson steps")


# ============================================================
# Learner endpoints
# ============================================================


@learner_router.post(
    "/lesson-steps/{step_id}/complete",
)
async def complete_lesson_step(
    step_id: str,
    learner: LearnerContext = Depends(get_current_learner),
):
    """Mark a lesson step as complete for the authenticated learner.

    Args:
        step_id: Lesson step record ID
        learner: Authenticated learner context

    Returns:
        Success response
    """
    try:
        await LearnerStepProgress.mark_complete(
            user_id=learner.user.id, step_id=step_id
        )
        logger.info(
            f"Learner {learner.user.id} completed lesson step {step_id}"
        )
        return {"message": "Step marked as complete"}
    except Exception as e:
        logger.error(
            f"Error marking step {step_id} complete for learner {learner.user.id}: {str(e)}"
        )
        raise HTTPException(status_code=500, detail="Failed to mark step as complete")


@learner_router.get(
    "/notebooks/{notebook_id}/lesson-steps/progress",
    response_model=LearnerStepProgressResponse,
)
async def get_lesson_steps_progress(
    notebook_id: str,
    learner: LearnerContext = Depends(get_current_learner),
):
    """Get lesson step progress for the authenticated learner.

    Returns completed step IDs, total steps, and completed count.

    Args:
        notebook_id: Notebook record ID
        learner: Authenticated learner context

    Returns:
        LearnerStepProgressResponse
    """
    # Validate learner access
    try:
        await validate_learner_access_to_notebook(
            notebook_id=notebook_id, learner_context=learner
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error validating learner access to notebook {notebook_id}: {str(e)}"
        )
        raise HTTPException(status_code=500, detail="Failed to validate notebook access")

    progress = await lesson_plan_service.get_learner_step_progress(
        notebook_id=notebook_id, user_id=learner.user.id
    )

    return LearnerStepProgressResponse(
        completed_step_ids=progress["completed_step_ids"],
        total_steps=progress["total_steps"],
        completed_count=progress["completed_count"],
    )


@learner_router.get(
    "/notebooks/{notebook_id}/lesson-steps",
    response_model=List[LessonStepResponse],
)
async def list_lesson_steps_learner(
    notebook_id: str,
    learner: LearnerContext = Depends(get_current_learner),
):
    """Get ordered list of lesson steps for a notebook (learner view).

    Args:
        notebook_id: Notebook record ID
        learner: Authenticated learner context

    Returns:
        Ordered list of LessonStepResponse
    """
    # Validate learner access
    try:
        await validate_learner_access_to_notebook(
            notebook_id=notebook_id, learner_context=learner
        )
    except HTTPException:
        raise

    steps = await lesson_plan_service.list_steps_with_source_titles(notebook_id)
    return [LessonStepResponse(**step) for step in steps]
