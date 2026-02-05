import re
from typing import List, Optional

from loguru import logger

from api.models import CompanyResponse
from open_notebook.database.repository import repo_query
from open_notebook.domain.company import Company


def generate_slug(name: str) -> str:
    """Generate URL-friendly slug from company name."""
    slug = name.lower().strip()
    slug = re.sub(r'[^a-z0-9]+', '-', slug)
    slug = slug.strip('-')
    return slug


async def create_company(name: str, slug: Optional[str] = None) -> Company:
    """Create a new company with auto-generated slug if not provided."""
    if not name or not name.strip():
        raise ValueError("Company name cannot be empty")

    # Auto-generate slug if not provided
    if not slug:
        slug = generate_slug(name)

    # Check if slug already exists
    existing = await Company.get_by_slug(slug)
    if existing:
        raise ValueError(f"Company with slug '{slug}' already exists")

    company = Company(name=name.strip(), slug=slug)
    await company.save()
    logger.info(f"Company created: {company.name} (slug: {company.slug})")
    return company


async def list_companies() -> List[CompanyResponse]:
    """List all companies with user counts.

    Returns list of CompanyResponse Pydantic models with user_count field.
    Uses single query to avoid N+1 problem.
    """
    try:
        # Get all companies
        companies = await Company.get_all(order_by="name")

        # Get user counts for all companies in single query (avoid N+1)
        user_counts = {}
        try:
            result = await repo_query(
                "SELECT company_id, count() as count FROM user WHERE company_id != NONE GROUP BY company_id",
                {}
            )
            for row in result:
                company_id = row.get("company_id")
                if company_id:
                    user_counts[company_id] = row.get("count", 0)
        except Exception as e:
            logger.warning(f"Error getting user counts: {e}")

        # Build response with counts
        response = []
        for company in companies:
            response.append(CompanyResponse(
                id=company.id,
                name=company.name,
                slug=company.slug,
                user_count=user_counts.get(company.id, 0),
                assignment_count=0,  # Will be populated when Story 2.2 creates module_assignment table
                created=str(company.created),
                updated=str(company.updated),
            ))

        return response
    except Exception as e:
        logger.error(f"Error listing companies: {e}")
        raise


async def get_company(company_id: str) -> Optional[CompanyResponse]:
    """Get company by ID with user count."""
    try:
        company = await Company.get(company_id)
        if not company:
            return None

        user_count = await company.get_member_count()

        return CompanyResponse(
            id=company.id,
            name=company.name,
            slug=company.slug,
            user_count=user_count,
            assignment_count=0,  # Will be populated when Story 2.2 creates module_assignment table
            created=str(company.created),
            updated=str(company.updated),
        )
    except Exception as e:
        logger.error(f"Error getting company {company_id}: {e}")
        raise


async def update_company(
    company_id: str, name: Optional[str] = None, slug: Optional[str] = None
) -> Optional[Company]:
    """Update company fields."""
    try:
        company = await Company.get(company_id)
        if not company:
            return None

        if name is not None:
            if not name.strip():
                raise ValueError("Company name cannot be empty")
            company.name = name.strip()

        if slug is not None:
            if not slug.strip():
                raise ValueError("Company slug cannot be empty")
            # Check if new slug is taken by another company
            existing = await Company.get_by_slug(slug)
            if existing and existing.id != company_id:
                raise ValueError(f"Company with slug '{slug}' already exists")
            company.slug = slug.strip()

        await company.save()
        logger.info(f"Company updated: {company.name}")
        return company
    except Exception as e:
        logger.error(f"Error updating company {company_id}: {e}")
        raise


async def delete_company(company_id: str) -> bool:
    """Delete company if no users or module assignments exist.

    Returns True if deleted, raises ValueError if company has dependencies.
    """
    try:
        company = await Company.get(company_id)
        if not company:
            return False

        # Check for assigned users
        user_count = await company.get_member_count()
        if user_count > 0:
            raise ValueError(
                f"Cannot delete company with {user_count} assigned users. "
                "Reassign or remove users first."
            )

        # Check for module assignments (Story 2.2)
        # For now, assignment_count will always be 0 until Story 2.2 is implemented
        result = await repo_query(
            "SELECT count() as count FROM module_assignment WHERE company_id = $cid GROUP ALL",
            {"cid": company_id}
        )
        assignment_count = result[0].get("count", 0) if result else 0

        if assignment_count > 0:
            raise ValueError(
                f"Cannot delete company with {assignment_count} module assignments. "
                "Remove assignments first."
            )

        await company.delete()
        logger.info(f"Company deleted: {company.name}")
        return True
    except ValueError:
        raise
    except Exception as e:
        logger.error(f"Error deleting company {company_id}: {e}")
        # If module_assignment table doesn't exist yet, that's OK (Story 2.2 not done)
        if "does not exist" in str(e).lower() or "not found" in str(e).lower():
            logger.debug("module_assignment table not found - Story 2.2 not implemented yet")
            # Still try to delete if only user count check passed
            try:
                await company.delete()
                logger.info(f"Company deleted: {company.name}")
                return True
            except Exception as delete_error:
                logger.error(f"Final delete failed: {delete_error}")
                raise
        raise
