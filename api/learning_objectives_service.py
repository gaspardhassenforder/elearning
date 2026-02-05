"""Learning objectives service layer.

Story 3.3: Learning Objectives Configuration
Business logic for managing learning objectives and auto-generation workflow.
"""

from typing import Dict, List, Optional

from fastapi import HTTPException
from loguru import logger

from open_notebook.domain.learning_objective import LearningObjective
from open_notebook.domain.notebook import Notebook
from open_notebook.graphs.learning_objectives_generation import objectives_generation_graph


async def list_objectives(notebook_id: str) -> List[LearningObjective]:
    """Get all learning objectives for a notebook (ordered).

    Args:
        notebook_id: Notebook record ID

    Returns:
        List of LearningObjective instances ordered by order ASC
    """
    logger.info(f"Listing objectives for notebook {notebook_id}")
    return await LearningObjective.get_for_notebook(notebook_id, ordered=True)


async def generate_objectives(notebook_id: str) -> Dict:
    """Auto-generate learning objectives using LangGraph workflow.

    Args:
        notebook_id: Notebook record ID

    Returns:
        Dict with status, objective_ids (if successful), and error (if failed)

    Raises:
        Does not raise exceptions - returns error dict for router to handle
    """
    logger.info(f"Generating objectives for notebook {notebook_id}")

    try:
        # Check notebook exists
        notebook = await Notebook.get(notebook_id)
        if not notebook:
            logger.error(f"Notebook {notebook_id} not found")
            return {
                "status": "failed",
                "error": f"Notebook {notebook_id} not found",
            }

        # Check if objectives already exist
        existing = await LearningObjective.get_for_notebook(notebook_id)
        if existing:
            logger.warning(f"Objectives already exist for notebook {notebook_id}")
            return {
                "status": "failed",
                "error": f"Learning objectives already exist for this notebook. Delete existing objectives before generating new ones.",
            }

        # Check notebook has sources
        sources = await notebook.get_sources()
        if not sources:
            logger.error(f"Notebook {notebook_id} has no sources")
            return {
                "status": "failed",
                "error": "Notebook has no sources. Add documents before generating learning objectives.",
            }

        # Invoke LangGraph workflow
        logger.info(f"Invoking objectives generation workflow for notebook {notebook_id}")
        result = await objectives_generation_graph.ainvoke({
            "notebook_id": notebook_id,
            "num_objectives": 4,  # Default to 4 objectives
            "status": "pending",
            "generated_objectives": [],
            "objective_ids": [],
            "error": None,
        })

        logger.info(f"Workflow completed with status: {result['status']}")

        return {
            "status": result["status"],
            "objective_ids": result.get("objective_ids"),
            "error": result.get("error"),
        }

    except Exception as e:
        logger.error(f"Error generating objectives for notebook {notebook_id}: {e}")
        logger.exception(e)
        return {
            "status": "failed",
            "error": f"Failed to generate objectives: {str(e)}",
        }


async def create_objective(
    notebook_id: str,
    text: str,
    order: int = 0,
) -> Optional[LearningObjective]:
    """Create a new learning objective manually.

    Args:
        notebook_id: Notebook record ID
        text: Objective text
        order: Display order (default 0)

    Returns:
        LearningObjective instance or None if creation failed
    """
    logger.info(f"Creating manual objective for notebook {notebook_id}")

    try:
        # Check notebook exists
        notebook = await Notebook.get(notebook_id)
        if not notebook:
            logger.error(f"Notebook {notebook_id} not found")
            raise HTTPException(status_code=404, detail="Notebook not found")

        # If order is 0, set to max + 1
        if order == 0:
            existing = await LearningObjective.get_for_notebook(notebook_id)
            if existing:
                max_order = max((obj.order for obj in existing), default=-1)
                order = max_order + 1

        # Create objective
        objective = LearningObjective(
            notebook_id=notebook_id,
            text=text,
            order=order,
            auto_generated=False,  # Manually created
        )
        await objective.save()
        logger.info(f"Created manual objective: {objective.id}")

        return objective

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating objective for notebook {notebook_id}: {e}")
        logger.exception(e)
        return None


async def update_objective(
    objective_id: str,
    text: str,
) -> Optional[LearningObjective]:
    """Update an existing learning objective's text.

    Args:
        objective_id: Objective record ID
        text: New objective text

    Returns:
        LearningObjective instance or None if not found
    """
    logger.info(f"Updating objective {objective_id}")

    try:
        # Load objective
        objective = await LearningObjective.get(objective_id)
        if not objective:
            logger.error(f"Objective {objective_id} not found")
            return None

        # Update text
        objective.text = text
        await objective.save()
        logger.info(f"Updated objective {objective_id}")

        return objective

    except Exception as e:
        logger.error(f"Error updating objective {objective_id}: {e}")
        logger.exception(e)
        return None


async def delete_objective(objective_id: str) -> bool:
    """Delete a learning objective.

    Args:
        objective_id: Objective record ID

    Returns:
        True if deleted successfully, False if not found
    """
    logger.info(f"Deleting objective {objective_id}")

    try:
        # Check objective exists
        objective = await LearningObjective.get(objective_id)
        if not objective:
            logger.error(f"Objective {objective_id} not found")
            return False

        # Delete
        await LearningObjective.delete_by_id(objective_id)
        logger.info(f"Deleted objective {objective_id}")

        return True

    except Exception as e:
        logger.error(f"Error deleting objective {objective_id}: {e}")
        logger.exception(e)
        return False


async def reorder_objectives(objective_updates: List[Dict[str, int]]) -> bool:
    """Reorder learning objectives via drag-and-drop.

    Args:
        objective_updates: List of dicts with 'id' and 'order' keys

    Returns:
        True if reordered successfully, False otherwise
    """
    logger.info(f"Reordering {len(objective_updates)} objectives")

    try:
        await LearningObjective.reorder_objectives(objective_updates)
        logger.info(f"Successfully reordered {len(objective_updates)} objectives")
        return True

    except Exception as e:
        logger.error(f"Error reordering objectives: {e}")
        logger.exception(e)
        return False
