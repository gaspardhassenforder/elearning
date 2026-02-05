"""Learning Objectives API endpoints.

Story 3.3: Learning Objectives Configuration
Admin-only CRUD operations for managing learning objectives.
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from loguru import logger

from api import learning_objectives_service
from api.auth import require_admin
from api.models import (
    BatchGenerationResponse,
    LearningObjectiveCreate,
    LearningObjectiveReorder,
    LearningObjectiveResponse,
    LearningObjectiveUpdate,
)
from open_notebook.domain.user import User

router = APIRouter(dependencies=[Depends(require_admin)])


@router.get("/notebooks/{notebook_id}/learning-objectives", response_model=List[LearningObjectiveResponse])
async def list_objectives(notebook_id: str):
    """Get all learning objectives for a notebook (ordered by order field).

    Args:
        notebook_id: Notebook record ID

    Returns:
        List of LearningObjectiveResponse objects ordered by order ASC
    """
    objectives = await learning_objectives_service.list_objectives(notebook_id)
    return [
        LearningObjectiveResponse(
            id=obj.id or "",
            notebook_id=obj.notebook_id,
            text=obj.text,
            order=obj.order,
            auto_generated=obj.auto_generated,
            created=getattr(obj, "created", None),
            updated=getattr(obj, "updated", None),
        )
        for obj in objectives
    ]


@router.post("/notebooks/{notebook_id}/learning-objectives/generate", response_model=BatchGenerationResponse)
async def generate_objectives(notebook_id: str, admin: User = Depends(require_admin)):
    """Auto-generate learning objectives from notebook sources using LangGraph workflow.

    Args:
        notebook_id: Notebook record ID
        admin: Authenticated admin user (injected)

    Returns:
        BatchGenerationResponse with generation status and objective IDs

    Raises:
        HTTPException 400: Objectives already exist or notebook has no sources
        HTTPException 404: Notebook not found
    """
    result = await learning_objectives_service.generate_objectives(notebook_id)

    # Check for errors
    if result.get("error"):
        if "already exist" in result["error"]:
            raise HTTPException(status_code=400, detail=result["error"])
        elif "not found" in result["error"] or "No sources" in result["error"]:
            raise HTTPException(status_code=404, detail=result["error"])
        else:
            raise HTTPException(status_code=500, detail=result["error"])

    return BatchGenerationResponse(
        status=result["status"],
        objective_ids=result.get("objective_ids"),
        error=result.get("error"),
    )


@router.post("/notebooks/{notebook_id}/learning-objectives", response_model=LearningObjectiveResponse)
async def create_objective(
    notebook_id: str,
    data: LearningObjectiveCreate,
    admin: User = Depends(require_admin),
):
    """Create a new learning objective manually (auto_generated=false).

    Args:
        notebook_id: Notebook record ID
        data: LearningObjectiveCreate with text and order
        admin: Authenticated admin user (injected)

    Returns:
        LearningObjectiveResponse with created objective

    Raises:
        HTTPException 404: Notebook not found
        HTTPException 400: Invalid input
    """
    objective = await learning_objectives_service.create_objective(
        notebook_id=notebook_id,
        text=data.text,
        order=data.order,
    )

    if not objective:
        raise HTTPException(status_code=400, detail="Failed to create objective")

    return LearningObjectiveResponse(
        id=objective.id or "",
        notebook_id=objective.notebook_id,
        text=objective.text,
        order=objective.order,
        auto_generated=objective.auto_generated,
        created=getattr(objective, "created", None),
        updated=getattr(objective, "updated", None),
    )


@router.put("/notebooks/{notebook_id}/learning-objectives/{objective_id}", response_model=LearningObjectiveResponse)
async def update_objective(
    notebook_id: str,
    objective_id: str,
    data: LearningObjectiveUpdate,
    admin: User = Depends(require_admin),
):
    """Update an existing learning objective's text.

    Args:
        notebook_id: Notebook record ID (for URL structure)
        objective_id: Objective record ID
        data: LearningObjectiveUpdate with new text
        admin: Authenticated admin user (injected)

    Returns:
        LearningObjectiveResponse with updated objective

    Raises:
        HTTPException 404: Objective not found
        HTTPException 400: Invalid input
    """
    if not data.text:
        raise HTTPException(status_code=400, detail="Text field is required")

    objective = await learning_objectives_service.update_objective(
        objective_id=objective_id,
        text=data.text,
    )

    if not objective:
        raise HTTPException(status_code=404, detail="Objective not found")

    return LearningObjectiveResponse(
        id=objective.id or "",
        notebook_id=objective.notebook_id,
        text=objective.text,
        order=objective.order,
        auto_generated=objective.auto_generated,
        created=getattr(objective, "created", None),
        updated=getattr(objective, "updated", None),
    )


@router.delete("/notebooks/{notebook_id}/learning-objectives/{objective_id}")
async def delete_objective(
    notebook_id: str,
    objective_id: str,
    admin: User = Depends(require_admin),
):
    """Delete a learning objective.

    Args:
        notebook_id: Notebook record ID (for URL structure)
        objective_id: Objective record ID
        admin: Authenticated admin user (injected)

    Returns:
        Success message

    Raises:
        HTTPException 404: Objective not found
    """
    success = await learning_objectives_service.delete_objective(objective_id)

    if not success:
        raise HTTPException(status_code=404, detail="Objective not found")

    return {"message": "Objective deleted successfully"}


@router.post("/notebooks/{notebook_id}/learning-objectives/reorder")
async def reorder_objectives(
    notebook_id: str,
    data: LearningObjectiveReorder,
    admin: User = Depends(require_admin),
):
    """Reorder learning objectives via drag-and-drop.

    Bulk update order field for multiple objectives.

    Args:
        notebook_id: Notebook record ID (for URL structure)
        data: LearningObjectiveReorder with list of {id, order} dicts
        admin: Authenticated admin user (injected)

    Returns:
        Success message

    Raises:
        HTTPException 400: Invalid input or reorder failed
    """
    if not data.objectives:
        raise HTTPException(status_code=400, detail="No objectives provided")

    success = await learning_objectives_service.reorder_objectives(data.objectives)

    if not success:
        raise HTTPException(status_code=400, detail="Failed to reorder objectives")

    return {"message": f"Successfully reordered {len(data.objectives)} objectives"}
