"""Learning objectives service layer.

Story 3.3: Learning Objectives Configuration
Business logic for managing learning objectives and auto-generation workflow.
"""

import asyncio
import json
from typing import Dict, List, Optional

from ai_prompter import Prompter
from fastapi import HTTPException
from loguru import logger

from open_notebook.ai.provision import provision_langchain_model
from open_notebook.database.repository import ensure_record_id, repo_query
from open_notebook.domain.learning_objective import LearningObjective
from open_notebook.domain.notebook import Notebook
from open_notebook.graphs.learning_objectives_generation import objectives_generation_graph
from open_notebook.observability.langsmith_handler import get_langsmith_callback
from open_notebook.utils import (
    build_dual_key_lookup,
    clean_thinking_content,
    extract_json_array,
    extract_text_from_response,
)


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

        # Auto-delete existing objectives before regenerating
        existing = await LearningObjective.get_for_notebook(notebook_id)
        if existing:
            deleted = await LearningObjective.delete_all_for_notebook(notebook_id)
            logger.info(f"Deleted {deleted} existing objectives before regeneration")

        # Check notebook has sources
        sources = await notebook.get_sources()
        if not sources:
            logger.error(f"Notebook {notebook_id} has no sources")
            return {
                "status": "failed",
                "error": "Notebook has no sources. Add documents before generating learning objectives.",
            }

        # Story 7.4: Create LangSmith callback for tracing (or None if not configured)
        langsmith_callback = get_langsmith_callback(
            user_id=None,  # Objectives generation - typically triggered by admin
            company_id=None,  # No company context at generation time
            notebook_id=notebook_id,
            workflow_name="objectives_generation",
            run_name=f"objectives:{notebook_id}",
        )

        # Build callbacks list (empty if LangSmith not configured)
        callbacks = [langsmith_callback] if langsmith_callback else []

        # Invoke LangGraph workflow
        logger.info(f"Invoking objectives generation workflow for notebook {notebook_id}")
        result = await objectives_generation_graph.ainvoke(
            {
                "notebook_id": notebook_id,
                "status": "pending",
                "content_analyses": [],
                "generated_objectives": [],
                "objective_ids": [],
                "error": None,
            },
            config={"callbacks": callbacks},  # Story 7.4: LangSmith tracing
        )

        logger.info(f"Workflow completed with status: {result['status']}")

        return {
            "status": result["status"],
            "objective_ids": result.get("objective_ids"),
            "error": result.get("error"),
        }

    except Exception as e:
        logger.error("Error generating objectives for notebook {}: {}", notebook_id, str(e))
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
        logger.error("Error creating objective for notebook {}: {}", notebook_id, str(e))
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
        logger.error("Error updating objective {}: {}", objective_id, str(e))
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
        logger.error("Error deleting objective {}: {}", objective_id, str(e))
        logger.exception(e)
        return False


async def refine_objectives(notebook_id: str, refinement_prompt: str) -> dict:
    """Refine existing learning objectives based on admin's natural language instruction.

    Args:
        notebook_id: Notebook record ID
        refinement_prompt: Natural language instruction for how to change the objectives

    Returns:
        Dict with status field
    """
    logger.info(f"Refining learning objectives for notebook {notebook_id}: {refinement_prompt[:50]}")

    try:
        objectives = await LearningObjective.get_for_notebook(notebook_id, ordered=True)
        if not objectives:
            return {"status": "failed", "error": "No learning objectives found to refine"}

        objectives_data = [
            {
                "id": str(obj.id),
                "text": obj.text,
                "order": obj.order,
            }
            for obj in objectives
        ]

        prompt = Prompter(prompt_template="learning_objectives/refine").render(
            data={"objectives": objectives_data, "refinement_prompt": refinement_prompt}
        )

        model = await provision_langchain_model(prompt, None, "chat", max_tokens=2000)
        response = await model.ainvoke(prompt)
        content = clean_thinking_content(extract_text_from_response(response.content)).strip()

        try:
            revised_objectives = extract_json_array(content)
        except ValueError:
            logger.error(f"No JSON array found in refine response: {content[:200]}")
            return {"status": "failed", "error": "AI returned unexpected format"}

        # Build lookup by ID (full or bare)
        existing_by_id = build_dual_key_lookup(objectives)
        returned_ids: set[str] = set()
        save_coros = []
        created_count = 0
        updated_count = 0

        for i, obj_data in enumerate(revised_objectives):
            obj_id = obj_data.get("id")
            new_text = (obj_data.get("text") or "").strip()

            if obj_id and obj_id in existing_by_id:
                # UPDATE existing objective
                returned_ids.add(obj_id)
                obj = existing_by_id[obj_id]
                if new_text:
                    obj.text = new_text
                obj.order = i
                save_coros.append(obj.save())
                updated_count += 1
            elif new_text:
                # CREATE new objective (id is null/missing/unknown)
                new_obj = LearningObjective(
                    notebook_id=notebook_id,
                    text=new_text,
                    order=i,
                    auto_generated=False,
                )
                save_coros.append(new_obj.save())
                created_count += 1

        # Persist all updates and creates in parallel
        await asyncio.gather(*save_coros)

        # Bulk-delete objectives omitted from AI response (single round-trip)
        ids_to_delete = []
        for obj in objectives:
            sid = str(obj.id)
            bare = sid.split(":", 1)[1] if ":" in sid else sid
            if sid not in returned_ids and bare not in returned_ids:
                ids_to_delete.append(ensure_record_id(sid))
        if ids_to_delete:
            await repo_query(
                "DELETE learning_objective WHERE id IN $ids", {"ids": ids_to_delete}
            )

        logger.info(
            f"Refined objectives for {notebook_id}: "
            f"{updated_count} updated, {created_count} created, {len(ids_to_delete)} deleted"
        )
        return {"status": "completed"}

    except json.JSONDecodeError as e:
        logger.error(f"JSON parse error in objectives refinement: {str(e)}")
        return {"status": "failed", "error": "Failed to parse AI response"}
    except Exception as e:
        logger.error(f"Error refining objectives for notebook {notebook_id}: {str(e)}")
        return {"status": "failed", "error": str(e)}


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
        logger.error("Error reordering objectives: {}", str(e))
        logger.exception(e)
        return False
