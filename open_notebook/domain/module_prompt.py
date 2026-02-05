"""Module prompt domain model for AI teacher configuration.

Story 3.4: AI Teacher Prompt Configuration
"""

from typing import ClassVar, Optional

from loguru import logger
from pydantic import field_validator

from open_notebook.database.repository import repo_query
from open_notebook.domain.base import ObjectModel
from open_notebook.exceptions import DatabaseOperationError


class ModulePrompt(ObjectModel):
    """Per-module AI teacher prompt configuration.

    ModulePrompt provides the second layer of the two-layer prompt system,
    enabling admins to customize AI teacher behavior for specific modules.

    The prompt is optional - if not provided, the global system prompt alone
    governs AI teacher behavior.

    Attributes:
        notebook_id: Reference to notebook (module) this prompt customizes
        system_prompt: Optional Jinja2 template for module-specific teaching style
        updated_at: Timestamp of last update (auto-managed)
        updated_by: Admin user who last updated the prompt
    """

    table_name: ClassVar[str] = "module_prompt"

    notebook_id: str
    system_prompt: Optional[str] = None
    updated_by: str

    @field_validator("notebook_id")
    @classmethod
    def ensure_notebook_id_format(cls, v: str) -> str:
        """Ensure notebook_id is in RecordID format (notebook:id)."""
        if not v.startswith("notebook:"):
            return f"notebook:{v}"
        return v

    @field_validator("updated_by")
    @classmethod
    def ensure_updated_by_format(cls, v: str) -> str:
        """Ensure updated_by is in RecordID format (user:id)."""
        if not v.startswith("user:"):
            return f"user:{v}"
        return v

    def needs_embedding(self) -> bool:
        """Module prompts are not searchable - internal configuration only."""
        return False

    @classmethod
    async def get_by_notebook(cls, notebook_id: str) -> Optional["ModulePrompt"]:
        """Get module prompt for a notebook (1:1 relationship).

        Args:
            notebook_id: Notebook record ID (with or without 'notebook:' prefix)

        Returns:
            ModulePrompt instance if exists, None if no prompt configured

        Raises:
            DatabaseOperationError: If query fails
        """
        # Ensure notebook_id has correct format
        if not notebook_id.startswith("notebook:"):
            notebook_id = f"notebook:{notebook_id}"

        try:
            query = "SELECT * FROM module_prompt WHERE notebook_id = $notebook_id LIMIT 1"
            result = await repo_query(query, {"notebook_id": notebook_id})

            if result:
                return cls(**result[0])
            return None
        except Exception as e:
            logger.error(f"Error fetching module prompt for notebook {notebook_id}: {str(e)}")
            raise DatabaseOperationError(e)

    @classmethod
    async def create_or_update(
        cls,
        notebook_id: str,
        system_prompt: Optional[str],
        updated_by: str
    ) -> "ModulePrompt":
        """Create or update module prompt for a notebook.

        Implements upsert logic - checks for existing prompt and updates,
        or creates new if none exists. Enforces 1:1 relationship via
        unique index on notebook_id.

        Args:
            notebook_id: Notebook record ID
            system_prompt: Optional Jinja2 template (None to clear)
            updated_by: Admin user ID who is updating

        Returns:
            ModulePrompt instance (created or updated)

        Raises:
            DatabaseOperationError: If operation fails
        """
        # Ensure IDs have correct format
        if not notebook_id.startswith("notebook:"):
            notebook_id = f"notebook:{notebook_id}"
        if not updated_by.startswith("user:"):
            updated_by = f"user:{updated_by}"

        try:
            # Check if prompt exists
            existing = await cls.get_by_notebook(notebook_id)

            if existing:
                # Update existing prompt
                existing.system_prompt = system_prompt
                existing.updated_by = updated_by
                await existing.save()
                logger.info(f"Updated module prompt for notebook {notebook_id}")
                return existing
            else:
                # Create new prompt
                new_prompt = cls(
                    notebook_id=notebook_id,
                    system_prompt=system_prompt,
                    updated_by=updated_by
                )
                await new_prompt.save()
                logger.info(f"Created module prompt for notebook {notebook_id}")
                return new_prompt
        except Exception as e:
            logger.error(f"Error creating/updating module prompt for notebook {notebook_id}: {str(e)}")
            raise DatabaseOperationError(e)

    @classmethod
    async def delete_by_notebook(cls, notebook_id: str) -> bool:
        """Delete module prompt for a notebook.

        Args:
            notebook_id: Notebook record ID

        Returns:
            True if deleted successfully, False if no prompt existed

        Raises:
            DatabaseOperationError: If deletion fails
        """
        # Ensure notebook_id has correct format
        if not notebook_id.startswith("notebook:"):
            notebook_id = f"notebook:{notebook_id}"

        try:
            existing = await cls.get_by_notebook(notebook_id)
            if existing:
                await repo_query("DELETE $id", {"id": existing.id})
                logger.info(f"Deleted module prompt for notebook {notebook_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting module prompt for notebook {notebook_id}: {str(e)}")
            raise DatabaseOperationError(e)
