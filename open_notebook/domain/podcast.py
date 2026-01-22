"""Podcast domain model for the learning platform."""

from typing import ClassVar, Literal, Optional

from open_notebook.database.repository import ensure_record_id
from open_notebook.domain.base import ObjectModel


class Podcast(ObjectModel):
    """Podcast artifact - overview or custom generated."""

    table_name: ClassVar[str] = "podcast"

    notebook_id: str
    title: str
    topic: Optional[str] = None  # For custom podcasts
    length: Literal["short", "medium", "long"] = "medium"
    speaker_format: Literal["single", "multi"] = "multi"
    audio_file_path: Optional[str] = None
    transcript: Optional[str] = None
    is_overview: bool = False  # Pre-generated overview podcast
    created_by: Literal["admin", "user"] = "user"
    status: Literal["pending", "generating", "completed", "failed"] = "pending"
    error_message: Optional[str] = None
    
    def _prepare_save_data(self) -> dict:
        """Override to ensure notebook_id is converted to RecordID for database."""
        data = super()._prepare_save_data()
        
        # Convert notebook_id string to RecordID format for database
        if "notebook_id" in data and data["notebook_id"] is not None:
            data["notebook_id"] = ensure_record_id(data["notebook_id"])
        
        return data

    async def get_notebook(self):
        """Get the parent notebook."""
        from open_notebook.domain.notebook import Notebook

        return await Notebook.get(self.notebook_id)

    @property
    def duration_minutes(self) -> int:
        """Get estimated duration in minutes based on length setting."""
        duration_map = {
            "short": 3,
            "medium": 7,
            "long": 15,
        }
        return duration_map.get(self.length, 7)

    @property
    def is_ready(self) -> bool:
        """Check if podcast is ready to play."""
        return self.status == "completed" and self.audio_file_path is not None
