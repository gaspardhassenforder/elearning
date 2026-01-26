"""Artifact domain model for unified artifact tracking."""

from typing import ClassVar, Literal, Optional

from loguru import logger
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

    def _is_job_id(self) -> bool:
        """Check if artifact_id is a job ID (command:xxx) rather than a real artifact ID."""
        return self.artifact_id.startswith("command:")

    async def get_artifact(self):
        """Get the actual artifact object based on type."""
        # Don't try to fetch if this is a job ID (command:xxx)
        # Job IDs are placeholders used while generation is in progress
        if self._is_job_id():
            return None
        
        try:
            if self.artifact_type == "quiz":
                from open_notebook.domain.quiz import Quiz

                return await Quiz.get(self.artifact_id)
            elif self.artifact_type == "podcast":
                from open_notebook.podcasts.models import PodcastEpisode

                return await PodcastEpisode.get(self.artifact_id)
            elif self.artifact_type == "note":
                from open_notebook.domain.notebook import Note

                return await Note.get(self.artifact_id)
            # transformation types can be added as needed
            return None
        except Exception as e:
            # If fetching fails (e.g., job ID that wasn't caught, or artifact doesn't exist),
            # log and return None instead of raising
            logger.debug(
                f"Could not fetch artifact {self.artifact_id} of type {self.artifact_type}: {e}"
            )
            return None

    async def delete_with_content(self) -> bool:
        """Delete both the artifact tracker and the actual artifact content."""
        try:
            # Only try to fetch and delete the actual artifact if it's not a job ID
            # Job IDs (command:xxx) are placeholders and don't have corresponding artifact records
            if not self._is_job_id():
                artifact = await self.get_artifact()
                if artifact:
                    await artifact.delete()
            
            # Always delete the artifact tracker itself
            await self.delete()
            return True
        except Exception as e:
            # Log the error but still try to delete the tracker
            logger.warning(
                f"Failed to delete artifact content for {self.artifact_id}: {e}"
            )
            # Try to delete the tracker anyway
            try:
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
