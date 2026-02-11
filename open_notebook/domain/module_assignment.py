from datetime import datetime
from typing import Any, ClassVar, Dict, Optional

from loguru import logger
from pydantic import field_validator

from open_notebook.database.repository import ensure_record_id, repo_query
from open_notebook.domain.base import ObjectModel
from open_notebook.exceptions import DatabaseOperationError


def _record_params(**kwargs: str) -> Dict[str, Any]:
    """Convert string record IDs to RecordID objects for SurrealDB query params.

    SurrealDB stores record<> fields as RecordIDs. Passing plain strings
    in WHERE clauses won't match. This helper ensures proper type casting.
    """
    return {k: ensure_record_id(v) for k, v in kwargs.items()}


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

    @field_validator("assigned_at", mode="before")
    @classmethod
    def coerce_assigned_at(cls, v: Any) -> Optional[str]:
        if isinstance(v, datetime):
            return v.isoformat()
        return v

    def needs_embedding(self) -> bool:
        """ModuleAssignments are not searchable."""
        return False

    def _prepare_save_data(self) -> Dict[str, Any]:
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
                _record_params(company_id=company_id),
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
                _record_params(notebook_id=notebook_id),
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
                _record_params(company_id=company_id, notebook_id=notebook_id),
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
                _record_params(company_id=company_id, notebook_id=notebook_id),
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
    async def get_unlocked_for_company(cls, company_id: str) -> list[dict]:
        """Get all unlocked module assignments for a company with notebook data.

        Used for learner module visibility — only shows unlocked modules.

        Args:
            company_id: Company record ID

        Returns:
            List of dicts with assignment fields + nested notebook_data dict
        """
        logger.info(f"Fetching unlocked modules for company {company_id}")

        try:
            # Step 1: Fetch unlocked assignments
            result = await repo_query(
                """
                SELECT *
                FROM module_assignment
                WHERE company_id = $company_id
                  AND is_locked = false
                ORDER BY assigned_at DESC
                """,
                _record_params(company_id=company_id),
            )

            # Step 2: Batch-fetch notebook data for all assignments
            nb_map: Dict[str, dict] = {}
            if result:
                nb_ids = list({str(r.get("notebook_id")) for r in result})
                nb_id_list = ", ".join(nb_ids)
                notebooks = await repo_query(
                    f"SELECT id, name, description, published, array::len(sources ?? []) AS source_count FROM notebook WHERE id IN [{nb_id_list}]"
                )
                for nb in notebooks:
                    nb_map[str(nb.get("id"))] = nb

            # Step 3: Build enriched dicts
            enriched = []
            for row in result:
                nb = nb_map.get(str(row.get("notebook_id")), {})
                enriched.append({
                    "notebook_id": row.get("notebook_id"),
                    "is_locked": row.get("is_locked", False),
                    "assigned_at": row.get("assigned_at"),
                    "notebook_data": {
                        "name": nb.get("name"),
                        "description": nb.get("description"),
                        "published": nb.get("published", False),
                        "source_count": nb.get("source_count", 0),
                    },
                })

            logger.info(f"Found {len(enriched)} unlocked modules for company {company_id}")
            return enriched
        except Exception as e:
            logger.error(f"Error fetching unlocked assignments for company {company_id}: {str(e)}")
            raise DatabaseOperationError(e)
