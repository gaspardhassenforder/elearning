from typing import List, Optional

from fastapi import APIRouter, Depends
from loguru import logger

from api import assignment_service
from api.auth import require_admin
from api.models import (
    AssignmentMatrixResponse,
    AssignmentToggleRequest,
    AssignmentToggleResponse,
    ModuleAssignmentCreate,
    ModuleAssignmentLockRequest,
    ModuleAssignmentResponse,
)
from open_notebook.domain.user import User

router = APIRouter(dependencies=[Depends(require_admin)])


@router.get("/module-assignments", response_model=List[ModuleAssignmentResponse])
async def list_assignments():
    """Get all module assignments.

    Returns:
        List of ModuleAssignmentResponse objects containing:
        - id: Assignment record ID
        - company_id: Company record ID
        - notebook_id: Notebook (module) record ID
        - is_locked: Whether module is locked for this company
        - assigned_at: ISO timestamp of assignment creation
        - assigned_by: User ID who created the assignment
    """
    assignments = await assignment_service.list_assignments()
    return [
        ModuleAssignmentResponse(
            id=a.id or "",
            company_id=a.company_id,
            notebook_id=a.notebook_id,
            is_locked=a.is_locked,
            assigned_at=a.assigned_at,
            assigned_by=a.assigned_by,
            warning=None,
        )
        for a in assignments
    ]


@router.post("/module-assignments", response_model=ModuleAssignmentResponse)
async def assign_module(
    data: ModuleAssignmentCreate,
    admin: User = Depends(require_admin),
):
    """Assign a module (notebook) to a company.

    Args:
        data: ModuleAssignmentCreate with company_id and notebook_id
        admin: Authenticated admin user (injected)

    Returns:
        ModuleAssignmentResponse with assignment details and optional warning
        if the module is not yet published.

    Raises:
        HTTPException 404: Company or notebook not found
    """
    assignment, warning = await assignment_service.assign_module(
        company_id=data.company_id,
        notebook_id=data.notebook_id,
        assigned_by=admin.id,
    )
    return ModuleAssignmentResponse(
        id=assignment.id or "",
        company_id=assignment.company_id,
        notebook_id=assignment.notebook_id,
        is_locked=assignment.is_locked,
        assigned_at=assignment.assigned_at,
        assigned_by=assignment.assigned_by,
        warning=warning,
    )


@router.delete("/module-assignments/company/{company_id}/notebook/{notebook_id}")
async def unassign_module_by_compound_key(
    company_id: str,
    notebook_id: str,
):
    """Remove a module assignment by company and notebook IDs.

    Args:
        company_id: Company record ID (path parameter)
        notebook_id: Notebook record ID (path parameter)

    Returns:
        Success message

    Raises:
        HTTPException 404: Assignment not found
    """
    await assignment_service.unassign_module(company_id, notebook_id)
    return {"message": "Assignment removed successfully"}


@router.get("/module-assignments/matrix", response_model=AssignmentMatrixResponse)
async def get_assignment_matrix():
    """Get the assignment matrix for the admin UI.

    Returns a comprehensive matrix structure showing all companies,
    all notebooks, and the assignment status for each combination.

    Returns:
        AssignmentMatrixResponse containing:
        - companies: List of CompanySummary (id, name, slug)
        - notebooks: List of NotebookSummary (id, name, published)
        - assignments: Dict[company_id][notebook_id] with:
            - is_assigned: bool
            - is_locked: bool
            - assignment_id: Optional[str]

    Used by the admin assignment matrix UI to render the grid.
    """
    matrix = await assignment_service.get_assignment_matrix()
    return AssignmentMatrixResponse(**matrix)


@router.post("/module-assignments/toggle", response_model=AssignmentToggleResponse)
async def toggle_assignment(
    data: AssignmentToggleRequest,
    admin: User = Depends(require_admin),
):
    """Toggle assignment: create if not exists, delete if exists.

    Efficiently handles both assignment creation and removal in a single
    endpoint. Used by the matrix UI for checkbox toggle interactions.

    Args:
        data: AssignmentToggleRequest with company_id and notebook_id
        admin: Authenticated admin user (injected)

    Returns:
        AssignmentToggleResponse with:
        - action: "assigned" or "unassigned"
        - company_id: Company record ID
        - notebook_id: Notebook record ID
        - assignment_id: Present when action="assigned"
        - warning: Present when assigning unpublished module

    Raises:
        HTTPException 404: Company or notebook not found
    """
    result = await assignment_service.toggle_assignment(
        company_id=data.company_id,
        notebook_id=data.notebook_id,
        assigned_by=admin.id,
    )
    return AssignmentToggleResponse(
        action=result["action"],
        company_id=result["company_id"],
        notebook_id=result["notebook_id"],
        assignment_id=result.get("assignment_id"),
        warning=result.get("warning"),
    )


@router.put(
    "/module-assignments/company/{company_id}/notebook/{notebook_id}/lock",
    response_model=ModuleAssignmentResponse,
)
async def toggle_module_lock(
    company_id: str,
    notebook_id: str,
    data: ModuleAssignmentLockRequest,
    admin: User = Depends(require_admin),
):
    """Toggle lock status on a module assignment (admin only).

    Allows admins to lock/unlock modules per company. Locked modules
    are hidden from learners even if assigned.

    Args:
        company_id: Company record ID (path parameter)
        notebook_id: Notebook record ID (path parameter)
        data: ModuleAssignmentLockRequest with is_locked boolean
        admin: Authenticated admin user (injected)

    Returns:
        ModuleAssignmentResponse with updated lock status and optional
        warning if the module is not yet published.

    Raises:
        HTTPException 404: Company, notebook, or assignment not found
    """
    assignment, warning = await assignment_service.toggle_module_lock(
        company_id=company_id,
        notebook_id=notebook_id,
        is_locked=data.is_locked,
        toggled_by=admin.id,
    )
    return ModuleAssignmentResponse(
        id=assignment.id or "",
        company_id=assignment.company_id,
        notebook_id=assignment.notebook_id,
        is_locked=assignment.is_locked,
        assigned_at=assignment.assigned_at,
        assigned_by=assignment.assigned_by,
        warning=warning,
    )
