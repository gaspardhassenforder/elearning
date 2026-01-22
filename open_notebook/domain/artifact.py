"""Artifact domain model for unified artifact tracking."""

from typing import ClassVar, Literal, Optional

from open_notebook.database.repository import ensure_record_id
from open_notebook.domain.base import ObjectModel


class Artifact(ObjectModel):
    """Unified tracking of all generated artifacts in a notebook."""

    table_name: ClassVar[str] = "artifact"

    notebook_id: str
    artifact_type: Literal["quiz", "podcast", "note", "transformation"]
    artifact_id: str  # ID of the actual artifact (quiz:xxx, podcast:xxx, etc.)
    title: str
    
    def _prepare_save_data(self) -> dict:
        """Override to ensure notebook_id is converted to RecordID for database."""
        data = super()._prepare_save_data()
        
        # Convert notebook_id string to RecordID format for database
        if "notebook_id" in data and data["notebook_id"] is not None:
            data["notebook_id"] = ensure_record_id(data["notebook_id"])
        
        return data

    async def get_artifact(self):
        """Get the actual artifact object based on type."""
        if self.artifact_type == "quiz":
            from open_notebook.domain.quiz import Quiz

            return await Quiz.get(self.artifact_id)
        elif self.artifact_type == "podcast":
            from open_notebook.domain.podcast import Podcast

            return await Podcast.get(self.artifact_id)
        elif self.artifact_type == "note":
            from open_notebook.domain.notebook import Note

            return await Note.get(self.artifact_id)
        # transformation types can be added as needed
        return None

    async def delete_with_content(self) -> bool:
        """Delete both the artifact tracker and the actual artifact content."""
        try:
            artifact = await self.get_artifact()
            if artifact:
                await artifact.delete()
            await self.delete()
            return True
        except Exception:
            return False

    @classmethod
    async def create_for_artifact(
        cls,
        notebook_id: str,
        artifact_type: Literal["quiz", "podcast", "note", "transformation"],
        artifact_id: str,
        title: str,
    ) -> "Artifact":
        """Create and save a new artifact tracker."""
        artifact = cls(
            notebook_id=notebook_id,
            artifact_type=artifact_type,
            artifact_id=artifact_id,
            title=title,
        )
        await artifact.save()
        return artifact
