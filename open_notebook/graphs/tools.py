from datetime import datetime
from typing import Optional, List

from langchain.tools import tool
from loguru import logger


async def _fetch_suggested_modules(user_id: str, current_notebook_id: str) -> List[dict]:
    """Fetch suggested modules for learner on module completion.

    Queries available modules for learner's company, excluding the current module.
    Returns up to 3 suggested modules with id, title, and description.

    Args:
        user_id: Learner's user ID
        current_notebook_id: Current notebook ID to exclude

    Returns:
        List of suggested module dicts with id, title, description
    """
    from open_notebook.database.repository import repo_query
    from open_notebook.domain.user import User

    try:
        # Get learner's company_id
        user = await User.get(user_id)
        if not user or not user.company_id:
            logger.warning(f"User {user_id} has no company_id - cannot suggest modules")
            return []

        # Query available modules for learner's company
        # Filter: published + unlocked + assigned to company + exclude current module
        query = """
            SELECT notebook.id, notebook.title, notebook.description
            FROM notebook
            JOIN module_assignment ON module_assignment.notebook_id = notebook.id
            WHERE module_assignment.company_id = $company_id
              AND module_assignment.is_locked = false
              AND notebook.published = true
              AND notebook.id != $current_notebook_id
            ORDER BY notebook.created DESC
            LIMIT 3
        """

        results = await repo_query(
            query,
            {"company_id": user.company_id, "current_notebook_id": current_notebook_id},
        )

        # Format results
        suggestions = []
        for row in results:
            suggestions.append({
                "id": row.get("id"),
                "title": row.get("title", "Untitled Module"),
                "description": row.get("description", ""),
            })

        logger.info(f"Found {len(suggestions)} suggested modules for user {user_id}")
        return suggestions

    except Exception as e:
        logger.error(f"Error fetching suggested modules: {e}")
        return []


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

    Security Note:
        Currently relies on API-layer access control to ensure learners only access
        sources from their assigned notebooks. The learner chat endpoint validates
        notebook assignment before invoking this tool.

        TODO (Story 7.5): Add defense-in-depth validation to verify source belongs to
        the notebook in the current chat session. Requires passing notebook_id via
        RunnableConfig or adding graph edge validation query.
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


@tool
async def check_off_objective(
    objective_id: str,
    evidence_text: str,
    config: Optional[dict] = None,
) -> dict:
    """Check off a learning objective when learner demonstrates understanding.

    Use this tool when you assess that the learner has demonstrated comprehension
    of a specific learning objective through their conversation. The evidence text
    should explain what the learner said or did that demonstrates understanding.

    Args:
        objective_id: The record ID of the learning objective (e.g., "learning_objective:abc123")
        evidence_text: Your reasoning explaining why this objective is now complete
            (e.g., "Learner correctly explained the difference between supervised and unsupervised learning")
        config: RunnableConfig containing user_id (injected by chat graph)

    Returns:
        dict: Progress data including completion counts and all_complete flag

    Security Note:
        Relies on API-layer access control via notebook assignment.
        The learner chat endpoint validates notebook assignment before invoking this tool.
        User ID is passed via RunnableConfig from the authenticated session.
    """
    from open_notebook.domain.learning_objective import LearningObjective
    from open_notebook.domain.learner_objective_progress import (
        LearnerObjectiveProgress,
        ProgressStatus,
        CompletedVia,
    )

    logger.info(f"check_off_objective tool called for objective_id: {objective_id}")

    try:
        # Load objective to validate it exists
        objective = await LearningObjective.get(objective_id)

        if not objective:
            logger.warning(f"Learning objective not found: {objective_id}")
            return {"error": "Learning objective not found", "objective_id": objective_id}

        # Extract user_id from config (passed by learner chat service)
        # Config is injected via RunnableConfig in chat graph
        user_id = None
        if config:
            configurable = config.get("configurable", {})
            user_id = configurable.get("user_id")

        if not user_id:
            logger.warning("check_off_objective called without user_id in config")
            return {
                "error": "User context not available",
                "objective_id": objective_id,
                "objective_text": objective.text,
                "evidence": evidence_text,
                "note": "Ensure user_id is passed via RunnableConfig"
            }

        # Create or retrieve progress record (handles duplicates gracefully)
        progress = await LearnerObjectiveProgress.create(
            user_id=user_id,
            objective_id=objective_id,
            status=ProgressStatus.COMPLETED,
            completed_via=CompletedVia.CONVERSATION,
            evidence=evidence_text,
        )

        # Count total completed vs total objectives for this notebook
        total_completed = await LearnerObjectiveProgress.count_completed_for_notebook(
            user_id=user_id, notebook_id=objective.notebook_id
        )
        total_objectives = await LearningObjective.count_for_notebook(objective.notebook_id)

        # Determine if all objectives are complete
        all_complete = total_completed >= total_objectives

        result = {
            "objective_id": objective_id,
            "objective_text": objective.text,
            "evidence": evidence_text,
            "total_completed": total_completed,
            "total_objectives": total_objectives,
            "all_complete": all_complete,
        }

        # Story 4.5: When all objectives complete, suggest next modules
        if all_complete:
            suggested_modules = await _fetch_suggested_modules(
                user_id=user_id, current_notebook_id=objective.notebook_id
            )
            result["suggested_modules"] = suggested_modules
            logger.info(f"Module completion: suggested {len(suggested_modules)} modules")
        else:
            result["suggested_modules"] = []

        logger.info(
            f"Checked off objective {objective_id}: {total_completed}/{total_objectives} complete"
        )
        return result

    except Exception as e:
        logger.error(f"Error in check_off_objective tool for objective {objective_id}: {e}")
        return {"error": f"Failed to check off objective: {str(e)}", "objective_id": objective_id}
