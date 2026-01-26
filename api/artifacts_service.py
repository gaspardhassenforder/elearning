"""Artifacts service for unified artifact management."""

from typing import List, Optional

from loguru import logger

from open_notebook.database.repository import repo_query, ensure_record_id
from open_notebook.domain.artifact import Artifact


async def get_notebook_artifacts(notebook_id: str) -> List[Artifact]:
    """Get all artifacts for a notebook."""
    logger.debug(f"Fetching artifacts for notebook: {notebook_id}")
    try:
        result = await repo_query(
            """
            SELECT * FROM artifact 
            WHERE notebook_id = $notebook_id 
            ORDER BY created DESC
            """,
            {"notebook_id": ensure_record_id(notebook_id)},
        )
        artifacts = [Artifact(**r) for r in result] if result else []
        logger.info(f"Found {len(artifacts)} artifacts for notebook {notebook_id}")
        return artifacts
    except Exception as e:
        logger.error(f"Error getting artifacts for notebook {notebook_id}: {e}")
        return []


async def get_notebook_artifacts_by_type(
    notebook_id: str, artifact_type: str
) -> List[Artifact]:
    """Get artifacts of a specific type for a notebook."""
    logger.debug(f"Fetching {artifact_type} artifacts for notebook: {notebook_id}")
    try:
        result = await repo_query(
            """
            SELECT * FROM artifact 
            WHERE notebook_id = $notebook_id AND artifact_type = $artifact_type
            ORDER BY created DESC
            """,
            {
                "notebook_id": ensure_record_id(notebook_id),
                "artifact_type": artifact_type,
            },
        )
        artifacts = [Artifact(**r) for r in result] if result else []
        logger.info(f"Found {len(artifacts)} {artifact_type} artifacts for notebook {notebook_id}")
        return artifacts
    except Exception as e:
        logger.error(
            f"Error getting {artifact_type} artifacts for notebook {notebook_id}: {e}"
        )
        return []


async def get_artifact(artifact_id: str) -> Optional[Artifact]:
    """Get an artifact by ID."""
    logger.debug(f"Fetching artifact: {artifact_id}")
    try:
        artifact = await Artifact.get(artifact_id)
        if artifact:
            logger.debug(f"Found artifact {artifact_id}: type={artifact.artifact_type}, content_id={artifact.artifact_id}")
        else:
            logger.warning(f"Artifact not found: {artifact_id}")
        return artifact
    except Exception as e:
        logger.error(f"Error getting artifact {artifact_id}: {e}")
        return None


async def delete_artifact(artifact_id: str) -> bool:
    """Delete an artifact and its associated content."""
    logger.info(f"Deleting artifact: {artifact_id}")
    try:
        artifact = await Artifact.get(artifact_id)
        if not artifact:
            logger.warning(f"Cannot delete - artifact not found: {artifact_id}")
            return False

        logger.debug(f"Deleting artifact {artifact_id}: type={artifact.artifact_type}, content_id={artifact.artifact_id}")
        success = await artifact.delete_with_content()
        if success:
            logger.info(f"Successfully deleted artifact {artifact_id} and its content")
        else:
            logger.warning(f"Failed to delete artifact {artifact_id}")
        return success
    except Exception as e:
        logger.error(f"Error deleting artifact {artifact_id}: {e}")
        return False
