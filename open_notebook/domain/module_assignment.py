from typing import Any, ClassVar, Dict, Optional

from loguru import logger

from open_notebook.database.repository import ensure_record_id, repo_query
from open_notebook.domain.base import ObjectModel
from open_notebook.exceptions import DatabaseOperationError


class ModuleAssignment(ObjectModel):
    """Assignment of a module (notebook) to a company.

    ModuleAssignment is a separate domain model (not a simple relationship)
    to allow for additional metadata like is_locked, assigned_at, assigned_by.
    """

    table_name: ClassVar[str] = "module_assignment"

    company_id: str
    notebook_id: str
    is_locked: bool = False
    assigned_at: Optional[str] = None
    assigned_by: Optional[str] = None

    def needs_embedding(self) -> bool:
        """ModuleAssignments are not searchable."""
        return False

    def _prepare_save_data(self) -> Dict[str, Any]:
        from datetime import datetime

        data = super()._prepare_save_data()
        # SurrealDB schema defines these as record<company>, record<notebook>,
        # option<record<user>>. connection.insert() requires RecordID objects.
        for field in ("company_id", "notebook_id", "assigned_by"):
            if data.get(field) and isinstance(data[field], str):
                data[field] = ensure_record_id(data[field])
        # SurrealDB expects assigned_at as datetime, not string
        if data.get("assigned_at") and isinstance(data["assigned_at"], str):
            data["assigned_at"] = datetime.fromisoformat(data["assigned_at"])
        return data

    @classmethod
    async def get_by_company(cls, company_id: str) -> list["ModuleAssignment"]:
        """Get all module assignments for a company."""
        try:
            result = await repo_query(
                "SELECT * FROM module_assignment WHERE company_id = $company_id",
                {"company_id": company_id},
            )
            return [cls(**item) for item in result]
        except Exception as e:
            logger.error(f"Error fetching assignments for company {company_id}: {str(e)}")
            raise DatabaseOperationError(e)

    @classmethod
    async def get_by_notebook(cls, notebook_id: str) -> list["ModuleAssignment"]:
        """Get all module assignments for a notebook."""
        try:
            result = await repo_query(
                "SELECT * FROM module_assignment WHERE notebook_id = $notebook_id",
                {"notebook_id": notebook_id},
            )
            return [cls(**item) for item in result]
        except Exception as e:
            logger.error(f"Error fetching assignments for notebook {notebook_id}: {str(e)}")
            raise DatabaseOperationError(e)

    @classmethod
    async def get_by_company_and_notebook(
        cls, company_id: str, notebook_id: str
    ) -> Optional["ModuleAssignment"]:
        """Get a specific assignment by company and notebook IDs."""
        try:
            result = await repo_query(
                "SELECT * FROM module_assignment WHERE company_id = $company_id AND notebook_id = $notebook_id LIMIT 1",
                {"company_id": company_id, "notebook_id": notebook_id},
            )
            return cls(**result[0]) if result else None
        except Exception as e:
            logger.error(
                f"Error fetching assignment for company {company_id} and notebook {notebook_id}: {str(e)}"
            )
            raise DatabaseOperationError(e)

    @classmethod
    async def delete_assignment(cls, company_id: str, notebook_id: str) -> bool:
        """Delete an assignment by company and notebook IDs."""
        try:
            await repo_query(
                "DELETE FROM module_assignment WHERE company_id = $company_id AND notebook_id = $notebook_id",
                {"company_id": company_id, "notebook_id": notebook_id},
            )
            logger.info(
                f"Deleted assignment for company {company_id} and notebook {notebook_id}"
            )
            return True
        except Exception as e:
            logger.error(
                f"Error deleting assignment for company {company_id} and notebook {notebook_id}: {str(e)}"
            )
            raise DatabaseOperationError(e)

    @classmethod
    async def get_all_assignments(cls) -> list["ModuleAssignment"]:
        """Get all module assignments."""
        try:
            result = await repo_query("SELECT * FROM module_assignment")
            return [cls(**item) for item in result]
        except Exception as e:
            logger.error(f"Error fetching all assignments: {str(e)}")
            raise DatabaseOperationError(e)

    @classmethod
    async def toggle_lock(
        cls, company_id: str, notebook_id: str, is_locked: bool
    ) -> Optional["ModuleAssignment"]:
        """Toggle lock status on a module assignment.

        Args:
            company_id: Company record ID
            notebook_id: Notebook record ID
            is_locked: New lock state (True = locked, False = unlocked)

        Returns:
            Updated ModuleAssignment or None if not found
        """
        logger.info(
            f"Toggling lock for company {company_id} notebook {notebook_id} to {is_locked}"
        )

        # Query assignment by compound key
        assignment = await cls.get_by_company_and_notebook(company_id, notebook_id)
        if not assignment:
            logger.error(
                f"Assignment not found: company {company_id} notebook {notebook_id}"
            )
            return None

        # Update is_locked field
        assignment.is_locked = is_locked
        await assignment.save()

        logger.info(f"Lock toggled successfully: {assignment.id} is_locked={is_locked}")
        return assignment

    @classmethod
    async def get_unlocked_for_company(cls, company_id: str) -> list["ModuleAssignment"]:
        """Get all unlocked module assignments for a company.

        Used for learner module visibility — only shows unlocked modules.

        Args:
            company_id: Company record ID

        Returns:
            List of ModuleAssignments where is_locked = False
        """
        logger.info(f"Fetching unlocked modules for company {company_id}")

        try:
            result = await repo_query(
                """
                SELECT
                    assignment.*,
                    notebook.*,
                    array::len(notebook.sources) AS source_count
                FROM module_assignment AS assignment
                JOIN notebook ON assignment.notebook_id = notebook.id
                WHERE assignment.company_id = $company_id
                  AND assignment.is_locked = false
                ORDER BY assignment.assigned_at DESC
                """,
                {"company_id": company_id},
            )

            # Parse results - each row has both assignment and notebook fields
            assignments = []
            for row in result:
                # Extract assignment fields
                assignment = cls(
                    id=row.get("assignment.id") or row.get("id"),
                    company_id=row.get("assignment.company_id") or row.get("company_id"),
                    notebook_id=row.get("assignment.notebook_id")
                    or row.get("notebook_id"),
                    is_locked=row.get("assignment.is_locked", False),
                    assigned_at=row.get("assignment.assigned_at"),
                    assigned_by=row.get("assignment.assigned_by"),
                )
                # Attach notebook data for service layer (includes source_count and published from JOIN)
                assignment.notebook_data = {
                    "id": row.get("notebook.id"),
                    "name": row.get("notebook.name"),
                    "description": row.get("notebook.description"),
                    "published": row.get("notebook.published", False),
                    "source_count": row.get("source_count", 0),
                }
                assignments.append(assignment)

            logger.info(f"Found {len(assignments)} unlocked modules for company {company_id}")
            return assignments
        except Exception as e:
            logger.error(f"Error fetching unlocked assignments for company {company_id}: {str(e)}")
            raise DatabaseOperationError(e)
