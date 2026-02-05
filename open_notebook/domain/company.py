from typing import ClassVar, Optional

from loguru import logger
from pydantic import field_validator

from open_notebook.database.repository import repo_query
from open_notebook.domain.base import ObjectModel
from open_notebook.exceptions import DatabaseOperationError, InvalidInputError


class Company(ObjectModel):
    table_name: ClassVar[str] = "company"

    name: str
    slug: str

    @field_validator("name")
    @classmethod
    def name_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise InvalidInputError("Company name cannot be empty")
        return v.strip()

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

    async def get_member_count(self) -> int:
        """Get count of users assigned to this company."""
        if not self.id:
            return 0
        try:
            result = await repo_query(
                "SELECT count() as count FROM user WHERE company_id = $cid GROUP ALL",
                {"cid": self.id},
            )
            if result and len(result) > 0:
                return result[0].get("count", 0)
            return 0
        except Exception as e:
            logger.error(f"Error getting member count for company {self.id}: {str(e)}")
            raise DatabaseOperationError(e)
