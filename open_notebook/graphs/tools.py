from datetime import datetime
from typing import Optional

from langchain.tools import tool
from loguru import logger


# todo: turn this into a system prompt variable
@tool
def get_current_timestamp() -> str:
    """
    name: get_current_timestamp
    Returns the current timestamp in the format YYYYMMDDHHmmss.
    """
    return datetime.now().strftime("%Y%m%d%H%M%S")


@tool
async def surface_document(source_id: str, excerpt_text: str, relevance_reason: str) -> dict:
    """Surface a document snippet in the chat conversation.

    Use this tool when you want to reference a specific source document in your response.
    This will display an inline document card in the chat showing the excerpt and a link
    to open the full document in the sources panel.

    Args:
        source_id: The record ID of the source document (e.g., "source:abc123")
        excerpt_text: A relevant excerpt from the document (max 200 chars recommended)
        relevance_reason: Brief explanation of why this document is relevant to the conversation

    Returns:
        dict: Structured document snippet data with source metadata
    """
    from open_notebook.domain.notebook import Source

    logger.info(f"surface_document tool called for source_id: {source_id}")

    try:
        # Load source metadata
        source = await Source.get(source_id)

        if not source:
            logger.warning(f"Source not found: {source_id}")
            return {
                "error": "Source not found",
                "source_id": source_id
            }

        # Truncate excerpt to 200 characters if needed
        truncated_excerpt = excerpt_text
        if len(excerpt_text) > 200:
            truncated_excerpt = excerpt_text[:197] + "..."
            logger.debug(f"Truncated excerpt from {len(excerpt_text)} to 200 chars")

        # Determine file type from asset (file_path or URL)
        file_type = "document"
        if source.asset and source.asset.file_path:
            # Extract extension from file path
            import os
            _, ext = os.path.splitext(source.asset.file_path)
            file_type = ext.lstrip('.') if ext else "file"
        elif source.asset and source.asset.url:
            file_type = "url"

        # Return structured data for frontend rendering
        result = {
            "source_id": source_id,
            "title": source.title or "Untitled Document",
            "source_type": file_type,
            "excerpt": truncated_excerpt,
            "relevance": relevance_reason,
            "metadata": {
                "created": source.created.isoformat() if source.created else None,
                "file_type": file_type,
            }
        }

        logger.info(f"Successfully surfaced document: {source.title}")
        return result

    except Exception as e:
        logger.error(f"Error in surface_document tool for source {source_id}: {e}")
        return {
            "error": f"Failed to surface document: {str(e)}",
            "source_id": source_id
        }
