from typing import List, Optional

from loguru import logger

from open_notebook.domain.company import Company


async def create_company(name: str, slug: str, description: Optional[str] = None) -> Company:
    """Create a new company."""
    existing = await Company.get_by_slug(slug)
    if existing:
        raise ValueError("Company slug already exists")

    company = Company(
        name=name,
        slug=slug,
        description=description,
    )
    await company.save()
    logger.info(f"Company created: {name} ({slug})")
    return company


async def get_company_by_id(company_id: str) -> Optional[Company]:
    """Fetch company by ID."""
    try:
        return await Company.get(company_id)
    except Exception:
        return None


async def get_company_by_slug(slug: str) -> Optional[Company]:
    """Fetch company by slug."""
    return await Company.get_by_slug(slug)


async def list_companies() -> List[Company]:
    """List all companies."""
    return await Company.get_all()


async def list_companies_with_counts() -> List[tuple[Company, int, int]]:
    """List all companies with user and assignment counts.

    Returns a list of tuples: (company, user_count, assignment_count).
    Uses batch queries to avoid N+1 query problem.
    """
    companies = await Company.get_all()
    user_counts = await Company.get_all_user_counts()
    assignment_counts = await Company.get_all_assignment_counts()

    return [
        (
            company,
            user_counts.get(company.id, 0) if company.id else 0,
            assignment_counts.get(company.id, 0) if company.id else 0,
        )
        for company in companies
    ]


async def update_company(
    company_id: str,
    name: Optional[str] = None,
    slug: Optional[str] = None,
    description: Optional[str] = None,
) -> Optional[Company]:
    """Update company fields."""
    company = await get_company_by_id(company_id)
    if not company:
        return None

    if slug and slug != company.slug:
        existing = await Company.get_by_slug(slug)
        if existing:
            raise ValueError("Company slug already exists")
        company.slug = slug

    if name:
        company.name = name
    if description is not None:
        company.description = description

    await company.save()
    logger.info(f"Company updated: {company.name}")
    return company


async def delete_company(company_id: str) -> bool:
    """Delete a company. Returns True if deleted.

    Raises ValueError if company has assigned users or module assignments.
    """
    company = await get_company_by_id(company_id)
    if not company:
        return False

    # Check for assigned users
    user_count = await Company.get_user_count(company_id)

    # Check for module assignments (returns 0 if table doesn't exist yet)
    assignment_count = await Company.get_assignment_count(company_id)

    if user_count > 0 or assignment_count > 0:
        error_parts = []
        if user_count > 0:
            error_parts.append(f"{user_count} assigned learner{'s' if user_count > 1 else ''}")
        if assignment_count > 0:
            error_parts.append(f"{assignment_count} assigned module{'s' if assignment_count > 1 else ''}")
        error_msg = f"Cannot delete company with {' and '.join(error_parts)}. Reassign or remove them first."
        logger.warning(f"Delete company blocked: {error_msg}")
        raise ValueError(error_msg)

    await company.delete()
    logger.info(f"Company deleted: {company.name}")
    return True


async def get_company_user_count(company_id: str) -> int:
    """Get number of users in a company."""
    return await Company.get_user_count(company_id)


async def get_company_assignment_count(company_id: str) -> int:
    """Get number of module assignments for a company."""
    return await Company.get_assignment_count(company_id)
