"""Learning objectives domain model for module configuration.

Story 3.3: Learning Objectives Configuration
"""

from typing import ClassVar, Optional

from loguru import logger
from pydantic import field_validator

from open_notebook.database.repository import ensure_record_id, repo_query
from open_notebook.domain.base import ObjectModel
from open_notebook.exceptions import DatabaseOperationError, InvalidInputError


class LearningObjective(ObjectModel):
    """Learning objective for a module/notebook.

    Learning objectives define measurable goals for learners in a module.
    They guide the AI teacher's conversation strategy and track learner progress.

    Attributes:
        notebook_id: Reference to notebook (module) this objective belongs to
        text: Objective description (measurable, action-verb based)
        order: Display order for drag-and-drop reordering (0-indexed)
        auto_generated: True if AI-generated, False if manually created by admin
    """

    table_name: ClassVar[str] = "learning_objective"
    record_id_fields: ClassVar[set[str]] = {"notebook_id"}

    notebook_id: str
    text: str
    order: int = 0
    auto_generated: bool = False
    source_refs: list[str] = []  # Content IDs that contributed to this objective

    @field_validator("notebook_id")
    @classmethod
    def ensure_notebook_id_format(cls, v: str) -> str:
        """Ensure notebook_id is in RecordID format (notebook:id)."""
        if not v.startswith("notebook:"):
            return f"notebook:{v}"
        return v

    @field_validator("text")
    @classmethod
    def validate_text(cls, v: str) -> str:
        """Ensure text is not empty."""
        if not v or not v.strip():
            raise InvalidInputError("Learning objective text cannot be empty")
        return v.strip()

    def needs_embedding(self) -> bool:
        """Learning objectives are not searchable."""
        return False

    @classmethod
    async def get_for_notebook(cls, notebook_id: str, ordered: bool = True) -> list["LearningObjective"]:
        """Get all learning objectives for a notebook, optionally ordered.

        Args:
            notebook_id: Notebook record ID (with or without 'notebook:' prefix)
            ordered: If True, sort by order ASC (default), else unordered

        Returns:
            List of LearningObjective instances
        """
        # Ensure notebook_id has correct format (validator only applies to instance creation)
        if not notebook_id.startswith("notebook:"):
            notebook_id = f"notebook:{notebook_id}"

        try:
            query = "SELECT * FROM learning_objective WHERE notebook_id = $notebook_id"
            if ordered:
                query += " ORDER BY order ASC"

            result = await repo_query(query, {"notebook_id": ensure_record_id(notebook_id)})
            return [cls(**item) for item in result]
        except Exception as e:
            logger.error(f"Error fetching objectives for notebook {notebook_id}: {str(e)}")
            raise DatabaseOperationError(e)

    @classmethod
    async def reorder_objectives(cls, objective_updates: list[dict[str, int]]) -> bool:
        """Bulk update order field for multiple objectives.

        Used for drag-and-drop reordering. Updates all objectives in a single transaction.

        Args:
            objective_updates: List of dicts with 'id' and 'order' keys
                Example: [{"id": "learning_objective:1", "order": 0}, ...]

        Returns:
            True if successful

        Raises:
            DatabaseOperationError: If update fails
        """
        logger.info(f"Reordering {len(objective_updates)} learning objectives")

        try:
            # Build update query for all objectives
            # UPDATE learning_objective SET order = $order WHERE id = $id
            for item in objective_updates:
                await repo_query(
                    "UPDATE $id SET order = $order",
                    {"id": item["id"], "order": item["order"]},
                )

            logger.info(f"Successfully reordered {len(objective_updates)} objectives")
            return True
        except Exception as e:
            logger.error(f"Error reordering objectives: {str(e)}")
            raise DatabaseOperationError(e)

    @classmethod
    async def delete_by_id(cls, objective_id: str) -> bool:
        """Delete a learning objective by ID.

        Args:
            objective_id: Objective record ID

        Returns:
            True if deleted successfully
        """
        try:
            await repo_query("DELETE $id", {"id": objective_id})
            logger.info(f"Deleted learning objective {objective_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting objective {objective_id}: {str(e)}")
            raise DatabaseOperationError(e)

    @classmethod
    async def count_for_notebook(cls, notebook_id: str) -> int:
        """Count learning objectives for a notebook.

        Args:
            notebook_id: Notebook record ID

        Returns:
            Count of objectives
        """
        # Ensure notebook_id has correct format
        if not notebook_id.startswith("notebook:"):
            notebook_id = f"notebook:{notebook_id}"

        try:
            result = await repo_query(
                "SELECT count() AS count FROM learning_objective WHERE notebook_id = $notebook_id GROUP ALL",
                {"notebook_id": ensure_record_id(notebook_id)},
            )
            return result[0]["count"] if result else 0
        except Exception as e:
            logger.error(f"Error counting objectives for notebook {notebook_id}: {str(e)}")
            raise DatabaseOperationError(e)
