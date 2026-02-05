from typing import List

from fastapi import APIRouter, Depends, HTTPException
from loguru import logger

from api import assignment_service
from api.auth import LearnerContext, get_current_learner
from api.models import LearnerModuleResponse
from open_notebook.domain.module_assignment import ModuleAssignment
from open_notebook.domain.notebook import Notebook

router = APIRouter()


@router.get("/learner/modules", response_model=List[LearnerModuleResponse])
async def get_learner_modules(
    learner: LearnerContext = Depends(get_current_learner),
):
    """Get modules assigned to the learner's company (unlocked only).

    Automatically scoped to learner's company via get_current_learner() dependency.
    Returns only modules that are:
    - Assigned to learner's company
    - NOT locked (is_locked = false)

    Args:
        learner: LearnerContext with user and company_id (auto-injected)

    Returns:
        List of LearnerModuleResponse with learner-safe fields:
        - id: Notebook ID
        - name: Module name
        - description: Module description
        - is_locked: Lock status (always False in this endpoint)
        - source_count: Number of sources in module
        - assigned_at: ISO timestamp of assignment

    Note:
        Admin-only fields (assigned_by) are NOT included.
        Company scoping is AUTOMATICALLY enforced by get_current_learner().
    """
    logger.info(f"Fetching modules for learner {learner.user.id} (company {learner.company_id})")
    modules = await assignment_service.get_learner_modules(learner.company_id)
    return [
        LearnerModuleResponse(
            id=m["id"],
            name=m["name"],
            description=m.get("description"),
            is_locked=m["is_locked"],
            source_count=m["source_count"],
            assigned_at=m["assigned_at"],
        )
        for m in modules
    ]


@router.get("/learner/modules/{notebook_id}", response_model=LearnerModuleResponse)
async def get_learner_module(
    notebook_id: str,
    learner: LearnerContext = Depends(get_current_learner),
):
    """Validate learner access to a specific module (direct URL protection).

    Used for direct URL navigation protection. If a learner tries to access
    a module directly via URL, this endpoint validates they have permission.

    Validation rules:
    1. Module must be assigned to learner's company
    2. Module must NOT be locked (is_locked = false)

    Args:
        notebook_id: Notebook (module) record ID (path parameter)
        learner: LearnerContext with user and company_id (auto-injected)

    Returns:
        LearnerModuleResponse with module details if accessible

    Raises:
        HTTPException 403: Module not assigned, locked, or access denied
        HTTPException 404: Module doesn't exist

    Note:
        Company scoping is AUTOMATICALLY enforced by get_current_learner().
        This endpoint is the SINGLE enforcement point for direct module access.
    """
    logger.info(
        f"Validating access for learner {learner.user.id} (company {learner.company_id}) to module {notebook_id}"
    )

    # Check if module is assigned to learner's company
    assignment = await ModuleAssignment.get_by_company_and_notebook(
        learner.company_id, notebook_id
    )

    if not assignment:
        logger.warning(
            f"Module {notebook_id} not assigned to company {learner.company_id} - access denied"
        )
        raise HTTPException(
            status_code=403, detail="This module is not accessible to you"
        )

    # Check if module is locked
    if assignment.is_locked:
        logger.warning(
            f"Module {notebook_id} is locked for company {learner.company_id} - access denied"
        )
        raise HTTPException(
            status_code=403, detail="This module is currently locked"
        )

    # Fetch notebook details
    try:
        notebook = await Notebook.get(notebook_id)
    except Exception:
        logger.error(f"Notebook {notebook_id} not found")
        raise HTTPException(status_code=404, detail="Module not found")

    # Count sources
    source_count = len(getattr(notebook, "sources", []))

    logger.info(f"Access granted for learner {learner.user.id} to module {notebook_id}")

    return LearnerModuleResponse(
        id=notebook_id,
        name=notebook.name,
        description=notebook.description,
        is_locked=assignment.is_locked,
        source_count=source_count,
        assigned_at=assignment.assigned_at or "",
    )
