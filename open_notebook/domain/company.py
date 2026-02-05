from typing import ClassVar, Optional

from loguru import logger

from open_notebook.database.repository import repo_query
from open_notebook.domain.base import ObjectModel
from open_notebook.exceptions import DatabaseOperationError


class Company(ObjectModel):
    """Company model for grouping users in a B2B context."""

    table_name: ClassVar[str] = "company"

    name: str
    slug: str
    description: Optional[str] = None

    @classmethod
    async def get_by_slug(cls, slug: str) -> Optional["Company"]:
        """Fetch company by slug."""
        try:
            result = await repo_query(
                "SELECT * FROM company WHERE slug = $slug LIMIT 1",
                {"slug": slug},
            )
            if result:
                return cls(**result[0])
            return None
        except Exception as e:
            logger.error(f"Error fetching company by slug {slug}: {str(e)}")
            raise DatabaseOperationError(e)

    @classmethod
    async def get_users(cls, company_id: str) -> list:
        """Get all users belonging to this company."""
        from open_notebook.domain.user import User

        try:
            result = await repo_query(
                "SELECT * FROM user WHERE company_id = $company_id",
                {"company_id": company_id},
            )
            return [User(**user_data) for user_data in result]
        except Exception as e:
            logger.error(f"Error fetching users for company {company_id}: {str(e)}")
            raise DatabaseOperationError(e)

    @classmethod
    async def get_user_count(cls, company_id: str) -> int:
        """Get count of users belonging to this company."""
        try:
            result = await repo_query(
                "SELECT count() FROM user WHERE company_id = $company_id GROUP ALL",
                {"company_id": company_id},
            )
            return result[0].get("count", 0) if result else 0
        except Exception as e:
            logger.error(f"Error counting users for company {company_id}: {str(e)}")
            return 0

    @classmethod
    async def get_assignment_count(cls, company_id: str) -> int:
        """Get count of module assignments for this company.

        Note: ModuleAssignment table will be created in Story 2.2.
        Until then, this returns 0. Once Story 2.2 is implemented,
        this will query the module_assignment table.
        """
        try:
            result = await repo_query(
                "SELECT count() FROM module_assignment WHERE company_id = $company_id GROUP ALL",
                {"company_id": company_id},
            )
            return result[0].get("count", 0) if result else 0
        except Exception as e:
            # Table doesn't exist yet (Story 2.2 not implemented)
            # Log at debug level since this is expected until Story 2.2
            logger.debug(f"Module assignment table not found for company {company_id}: {str(e)}")
            return 0

    @classmethod
    async def get_all_user_counts(cls) -> dict[str, int]:
        """Get user counts for all companies in a single query.

        Returns a dict mapping company_id -> user_count.
        This avoids N+1 queries when listing companies.
        """
        try:
            result = await repo_query(
                "SELECT company_id, count() FROM user GROUP BY company_id",
                {},
            )
            return {row["company_id"]: row.get("count", 0) for row in result if row.get("company_id")}
        except Exception as e:
            logger.error(f"Error counting users by company: {str(e)}")
            return {}

    @classmethod
    async def get_all_assignment_counts(cls) -> dict[str, int]:
        """Get module assignment counts for all companies in a single query.

        Returns a dict mapping company_id -> assignment_count.
        This avoids N+1 queries when listing companies.

        Note: Returns empty dict if module_assignment table doesn't exist (Story 2.2).
        """
        try:
            result = await repo_query(
                "SELECT company_id, count() FROM module_assignment GROUP BY company_id",
                {},
            )
            return {row["company_id"]: row.get("count", 0) for row in result if row.get("company_id")}
        except Exception as e:
            # Table doesn't exist yet (Story 2.2 not implemented)
            logger.debug(f"Module assignment table not found: {str(e)}")
            return {}
