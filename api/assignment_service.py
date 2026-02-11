from datetime import datetime, timezone
from typing import Dict, List, Optional

from fastapi import HTTPException
from loguru import logger

from open_notebook.domain.company import Company
from open_notebook.domain.module_assignment import ModuleAssignment
from open_notebook.domain.notebook import Notebook
from api.models import LearnerModuleResponse


async def assign_module(
    company_id: str,
    notebook_id: str,
    assigned_by: Optional[str] = None,
) -> tuple[ModuleAssignment, Optional[str]]:
    """Assign a module (notebook) to a company.

    Returns a tuple of (assignment, warning_message).
    The warning_message is set if the module is not published.
    """
    logger.info(f"Assigning notebook {notebook_id} to company {company_id}")

    # Check company exists
    company = await _get_company_or_404(company_id)

    # Check notebook exists
    notebook = await _get_notebook_or_404(notebook_id)

    # Check if already assigned (idempotent)
    existing = await ModuleAssignment.get_by_company_and_notebook(company_id, notebook_id)
    if existing:
        logger.info(f"Assignment already exists: {existing.id}")
        warning = _get_unpublished_warning(notebook)
        return existing, warning

    # Create assignment
    assignment = ModuleAssignment(
        company_id=company_id,
        notebook_id=notebook_id,
        is_locked=False,
        assigned_at=datetime.now(timezone.utc).isoformat(),
        assigned_by=assigned_by,
    )
    await assignment.save()
    logger.info(f"Created assignment: {assignment.id}")

    warning = _get_unpublished_warning(notebook)
    return assignment, warning


async def unassign_module(company_id: str, notebook_id: str) -> bool:
    """Remove a module assignment from a company.

    Raises HTTPException 404 if assignment doesn't exist.
    """
    logger.info(f"Unassigning notebook {notebook_id} from company {company_id}")

    existing = await ModuleAssignment.get_by_company_and_notebook(company_id, notebook_id)
    if not existing:
        logger.error(f"Assignment not found for company {company_id} and notebook {notebook_id}")
        raise HTTPException(status_code=404, detail="Assignment not found")

    await ModuleAssignment.delete_assignment(company_id, notebook_id)
    logger.info(f"Deleted assignment for company {company_id} and notebook {notebook_id}")
    return True


async def list_assignments() -> List[ModuleAssignment]:
    """List all module assignments."""
    logger.info("Listing all module assignments")
    return await ModuleAssignment.get_all_assignments()


async def get_assignment_matrix() -> Dict:
    """Get the assignment matrix for UI display.

    Returns a structure with:
    - companies: list of {id, name, slug}
    - notebooks: list of {id, name, published}
    - assignments: {company_id: {notebook_id: {is_assigned, is_locked, assignment_id}}}
    """
    logger.info("Building assignment matrix")

    # Fetch all companies
    companies = await Company.get_all()
    company_summaries = [
        {"id": c.id or "", "name": c.name, "slug": c.slug}
        for c in companies
    ]

    # Fetch all notebooks
    notebooks = await Notebook.get_all()
    notebook_summaries = [
        {
            "id": n.id or "",
            "name": n.name,
            "published": getattr(n, "published", False),  # Default to False if not present (matches migration 21)
        }
        for n in notebooks
    ]

    # Fetch all assignments and build matrix
    all_assignments = await ModuleAssignment.get_all_assignments()

    # Build the assignments dict: {company_id: {notebook_id: cell}}
    assignments_matrix: Dict[str, Dict[str, Dict]] = {}
    for company in companies:
        if not company.id:
            continue
        assignments_matrix[company.id] = {}
        for notebook in notebooks:
            if not notebook.id:
                continue
            # Find if assignment exists
            matching = next(
                (
                    a
                    for a in all_assignments
                    if a.company_id == company.id and a.notebook_id == notebook.id
                ),
                None,
            )
            assignments_matrix[company.id][notebook.id] = {
                "is_assigned": matching is not None,
                "is_locked": matching.is_locked if matching else False,
                "assignment_id": matching.id if matching else None,
            }

    return {
        "companies": company_summaries,
        "notebooks": notebook_summaries,
        "assignments": assignments_matrix,
    }


async def toggle_assignment(
    company_id: str,
    notebook_id: str,
    assigned_by: Optional[str] = None,
) -> Dict:
    """Toggle assignment: create if not exists, delete if exists.

    Returns a dict with action and details.
    """
    logger.info(f"Toggling assignment for company {company_id} notebook {notebook_id}")

    # Validate company and notebook exist before toggle
    await _get_company_or_404(company_id)
    await _get_notebook_or_404(notebook_id)

    existing = await ModuleAssignment.get_by_company_and_notebook(company_id, notebook_id)

    if existing:
        # Delete existing assignment
        await ModuleAssignment.delete_assignment(company_id, notebook_id)
        logger.info(f"Removed assignment for company {company_id} notebook {notebook_id}")
        return {
            "action": "unassigned",
            "company_id": company_id,
            "notebook_id": notebook_id,
        }
    else:
        # Create new assignment
        assignment, warning = await assign_module(company_id, notebook_id, assigned_by)
        return {
            "action": "assigned",
            "company_id": company_id,
            "notebook_id": notebook_id,
            "assignment_id": assignment.id,
            "warning": warning,
        }


def _get_unpublished_warning(notebook: Notebook) -> Optional[str]:
    """Return warning message if notebook is not published."""
    is_published = getattr(notebook, "published", False)  # Default False if field doesn't exist (matches migration 21)
    if not is_published:
        return "This module is not published yet. Learners will see it once published."
    return None


async def _get_company_or_404(company_id: str) -> Company:
    """Fetch company by ID or raise 404."""
    try:
        company = await Company.get(company_id)
        return company
    except Exception:
        logger.error(f"Company not found: {company_id}")
        raise HTTPException(status_code=404, detail="Company not found")


async def _get_notebook_or_404(notebook_id: str) -> Notebook:
    """Fetch notebook by ID or raise 404."""
    try:
        notebook = await Notebook.get(notebook_id)
        return notebook
    except Exception:
        logger.error(f"Notebook not found: {notebook_id}")
        raise HTTPException(status_code=404, detail="Module not found")


async def toggle_module_lock(
    company_id: str,
    notebook_id: str,
    is_locked: bool,
    toggled_by: Optional[str] = None,
) -> tuple[ModuleAssignment, Optional[str]]:
    """Toggle lock status on a module assignment (admin only).

    Args:
        company_id: Company record ID
        notebook_id: Notebook record ID
        is_locked: New lock state (True = locked, False = unlocked)
        toggled_by: Admin user ID who toggled

    Returns:
        Tuple of (ModuleAssignment, warning_message)

    Raises:
        HTTPException 404: Company, notebook, or assignment not found
    """
    logger.info(
        f"Admin {toggled_by} toggling lock: company={company_id} notebook={notebook_id} is_locked={is_locked}"
    )

    # Validate company exists
    await _get_company_or_404(company_id)

    # Validate notebook exists
    notebook = await _get_notebook_or_404(notebook_id)

    # Toggle lock via domain method
    assignment = await ModuleAssignment.toggle_lock(company_id, notebook_id, is_locked)
    if not assignment:
        logger.error(f"Assignment not found: company={company_id} notebook={notebook_id}")
        raise HTTPException(status_code=404, detail="Assignment not found")

    # Build warning (future: check published status)
    warning = _get_unpublished_warning(notebook)

    return assignment, warning


async def get_learner_modules(company_id: str) -> List[LearnerModuleResponse]:
    """Get modules visible to learners (assigned, unlocked, published).

    Enforces visibility rules:
    - Only modules assigned to learner's company
    - Only modules that are NOT locked
    - Only modules that are published (when Story 3.5 implemented)

    Args:
        company_id: Learner's company ID (from get_current_learner dependency)

    Returns:
        List of module dicts with learner-safe fields only

    Note:
        This function is called with company_id from authenticated learner context.
        Company scoping is ALREADY enforced by get_current_learner() dependency.
    """
    logger.info(f"Fetching learner modules for company {company_id}")

    # Get unlocked assignments with notebook data (returns list of dicts)
    assignments = await ModuleAssignment.get_unlocked_for_company(company_id)

    # Build learner-safe responses (exclude admin fields)
    modules = []
    for entry in assignments:
        notebook_data = entry.get("notebook_data", {})

        # Only show published modules to learners
        if not notebook_data.get("published", False):
            logger.info(f"Skipping unpublished module {entry.get('notebook_id')} for learner visibility")
            continue

        modules.append(
            LearnerModuleResponse(
                id=entry.get("notebook_id"),
                name=notebook_data.get("name", "Untitled Module"),
                description=notebook_data.get("description"),
                is_locked=entry.get("is_locked", False),
                source_count=notebook_data.get("source_count", 0),
                assigned_at=str(entry.get("assigned_at") or datetime.now(timezone.utc).isoformat()),
            )
        )

    logger.info(f"Returning {len(modules)} modules for company {company_id}")
    return modules
