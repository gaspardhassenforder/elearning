"""Content analysis domain model for per-content AI analysis cache.

Stores AI-generated summaries and preliminary learning objectives
for individual sources and artifacts. Used as a cache layer for
learning objectives generation workflow.
"""

from typing import ClassVar, Optional

from loguru import logger

from open_notebook.database.repository import repo_query
from open_notebook.domain.base import ObjectModel
from open_notebook.exceptions import DatabaseOperationError


class ContentAnalysis(ObjectModel):
    """Per-content AI analysis result.

    One record per source or artifact. Caches the AI-generated summary
    and preliminary objectives so re-generation can skip unchanged content.

    Attributes:
        content_id: ID of analyzed content (e.g., "source:xxx", "quiz:xxx")
        content_type: Type of content ("source", "quiz", "podcast", "note")
        summary: AI-generated summary of this content
        objectives: Preliminary learning objectives derived from this content
    """

    table_name: ClassVar[str] = "content_analysis"

    content_id: str
    content_type: str
    summary: str
    objectives: list[str] = []

    @classmethod
    async def get_for_content(cls, content_id: str) -> Optional["ContentAnalysis"]:
        """Get cached analysis for a specific content item.

        Args:
            content_id: Content record ID (e.g., "source:abc123")

        Returns:
            ContentAnalysis if found, None otherwise
        """
        try:
            result = await repo_query(
                "SELECT * FROM content_analysis WHERE content_id = $content_id LIMIT 1",
                {"content_id": content_id},
            )
            if result:
                return cls(**result[0])
            return None
        except Exception as e:
            logger.error(f"Error fetching content analysis for {content_id}: {e}")
            return None

    @classmethod
    async def get_for_contents(cls, content_ids: list[str]) -> list["ContentAnalysis"]:
        """Batch lookup of cached analyses for multiple content items.

        Args:
            content_ids: List of content record IDs

        Returns:
            List of ContentAnalysis records found
        """
        if not content_ids:
            return []

        try:
            result = await repo_query(
                "SELECT * FROM content_analysis WHERE content_id IN $content_ids",
                {"content_ids": content_ids},
            )
            return [cls(**item) for item in result] if result else []
        except Exception as e:
            logger.error(f"Error batch fetching content analyses: {e}")
            return []

    @classmethod
    async def delete_for_content(cls, content_id: str) -> bool:
        """Delete cached analysis for a content item (invalidate cache).

        Args:
            content_id: Content record ID

        Returns:
            True if deleted
        """
        try:
            await repo_query(
                "DELETE content_analysis WHERE content_id = $content_id",
                {"content_id": content_id},
            )
            logger.info(f"Invalidated content analysis cache for {content_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting content analysis for {content_id}: {e}")
            raise DatabaseOperationError(e)
