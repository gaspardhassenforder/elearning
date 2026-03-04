"""Lesson Plan Service - Business Logic for structured learning paths.

Handles AI generation of lesson plans from notebook sources, and progress
tracking for learners working through lesson steps.
"""

import json
import re
from typing import Dict, List, Optional

from loguru import logger

from open_notebook.ai.provision import provision_langchain_model
from open_notebook.domain.lesson_step import LessonStep
from open_notebook.domain.learner_step_progress import LearnerStepProgress
from open_notebook.domain.notebook import Notebook
from open_notebook.exceptions import DatabaseOperationError


def _is_video_source(source) -> bool:
    """Detect video sources by mirroring frontend getVideoType() logic."""
    asset = getattr(source, "asset", None)
    if not asset:
        return False
    url = getattr(asset, "url", None) or ""
    if re.search(r"youtube\.com|youtu\.be", url):
        return True
    file_path = getattr(asset, "file_path", None) or ""
    if re.search(r"\.(mp4|webm|mov|avi)$", file_path, re.IGNORECASE):
        return True
    return False


async def generate_lesson_plan(notebook_id: str) -> Dict:
    """Generate a structured lesson plan for a notebook using AI.

    1. Load all sources for the notebook (id, title, source_type)
    2. Call LLM with sources list + generation prompt
    3. Parse JSON response into ordered lesson steps
    4. Delete existing auto-generated steps for notebook
    5. Create new LessonStep records
    6. Return result dict

    Args:
        notebook_id: Notebook record ID

    Returns:
        Dict with status, step_ids (if successful), and error (if failed)
    """
    logger.info(f"Generating lesson plan for notebook {notebook_id}")

    try:
        # Check notebook exists
        notebook = await Notebook.get(notebook_id)
        if not notebook:
            return {"status": "failed", "error": f"Notebook {notebook_id} not found"}

        # Load all sources
        sources = await notebook.get_sources()
        if not sources:
            return {
                "status": "failed",
                "error": "No sources found in this notebook. Please add sources before generating a lesson plan.",
            }

        # Build sources list for the prompt
        sources_data = []
        for source in sources:
            source_id = str(source.id) if source.id else ""
            sources_data.append(
                {
                    "id": source_id,
                    "title": getattr(source, "title", "Untitled") or "Untitled",
                    "source_type": "video" if _is_video_source(source) else "document",
                }
            )

        logger.debug(f"Building lesson plan prompt for {len(sources_data)} sources")

        # Render the generation prompt
        from ai_prompter import Prompter

        prompt = Prompter(prompt_template="lesson_plan/generate").render(
            data={"sources": sources_data}
        )

        # Call LLM
        model = await provision_langchain_model(
            prompt, model_id=None, default_type="chat", max_tokens=4096
        )
        response = await model.ainvoke(prompt)

        # Extract text content
        content = response.content
        if isinstance(content, list):
            text_parts = [
                item.get("text", "")
                for item in content
                if isinstance(item, dict) and "text" in item
            ]
            content = "\n".join(text_parts) if text_parts else str(content)
        elif not isinstance(content, str):
            content = str(content)

        # Strip any thinking tags
        from open_notebook.utils import clean_thinking_content

        content = clean_thinking_content(content).strip()

        # Extract JSON array from response (may have trailing text)
        json_start = content.find("[")
        json_end = content.rfind("]") + 1
        if json_start == -1 or json_end == 0:
            logger.error(f"No JSON array found in LLM response: {content[:200]}")
            return {
                "status": "failed",
                "error": "AI returned unexpected format. Please try again.",
            }

        json_str = content[json_start:json_end]
        steps_data = json.loads(json_str)

        if not isinstance(steps_data, list):
            return {"status": "failed", "error": "AI returned invalid step format."}

        # Delete existing auto-generated steps
        deleted = await LessonStep.delete_auto_generated_for_notebook(notebook_id)
        logger.info(f"Deleted {deleted} existing auto-generated steps")

        # Create new steps
        step_ids = []
        for i, step_data in enumerate(steps_data):
            # Validate step type
            step_type = step_data.get("step_type", "read")
            if step_type not in ("watch", "read", "quiz", "discuss"):
                logger.warning(f"Invalid step_type '{step_type}', defaulting to 'read'")
                step_type = "read"

            # Resolve source_id - validate it actually exists in our sources
            source_id = step_data.get("source_id")
            if source_id:
                # Validate it's in the sources list
                valid_source_ids = {s["id"] for s in sources_data}
                if source_id not in valid_source_ids:
                    logger.warning(
                        f"Step {i} references unknown source_id '{source_id}', clearing"
                    )
                    source_id = None

            step = LessonStep(
                notebook_id=notebook_id,
                title=step_data.get("title", f"Step {i + 1}"),
                step_type=step_type,
                source_id=source_id,
                discussion_prompt=step_data.get("discussion_prompt") or None,
                order=i,
                required=True,
                auto_generated=True,
            )
            await step.save()
            if step.id:
                step_ids.append(str(step.id))

        logger.info(
            f"Generated {len(step_ids)} lesson steps for notebook {notebook_id}"
        )
        return {"status": "completed", "step_ids": step_ids}

    except json.JSONDecodeError as e:
        logger.error(f"JSON parse error in lesson plan generation: {str(e)}")
        return {
            "status": "failed",
            "error": "Failed to parse AI response. Please try again.",
        }
    except Exception as e:
        logger.error(f"Error generating lesson plan for notebook {notebook_id}: {str(e)}")
        return {"status": "failed", "error": str(e)}


async def list_steps_with_source_titles(notebook_id: str) -> List[dict]:
    """Get lesson steps with resolved source titles for display.

    Args:
        notebook_id: Notebook record ID

    Returns:
        List of step dicts with source_title resolved
    """
    try:
        steps = await LessonStep.get_for_notebook(notebook_id, ordered=True)
        if not steps:
            return []

        # Collect unique source IDs to resolve titles
        source_ids = {s.source_id for s in steps if s.source_id}
        source_title_map: dict[str, str] = {}

        if source_ids:
            from open_notebook.database.repository import repo_query, ensure_record_id

            for source_id in source_ids:
                try:
                    result = await repo_query(
                        "SELECT VALUE title FROM $id",
                        {"id": ensure_record_id(source_id)},
                    )
                    if result:
                        source_title_map[source_id] = str(result[0]) if result[0] else ""
                except Exception as e:
                    logger.warning(f"Could not resolve title for source {source_id}: {e}")

        return [
            {
                "id": str(s.id),
                "notebook_id": s.notebook_id,
                "title": s.title,
                "step_type": s.step_type,
                "source_id": s.source_id,
                "source_title": source_title_map.get(s.source_id, "") if s.source_id else None,
                "discussion_prompt": s.discussion_prompt,
                "order": s.order,
                "required": s.required,
                "auto_generated": s.auto_generated,
                "created": str(s.created) if s.created else None,
                "updated": str(s.updated) if s.updated else None,
            }
            for s in steps
        ]

    except Exception as e:
        logger.error(f"Error listing steps for notebook {notebook_id}: {str(e)}")
        return []


async def get_learner_step_progress(
    notebook_id: str, user_id: str
) -> dict:
    """Get learner progress on lesson steps for a notebook.

    Args:
        notebook_id: Notebook record ID
        user_id: User record ID

    Returns:
        Dict with completed_step_ids, total_steps, completed_count
    """
    try:
        steps = await LessonStep.get_for_notebook(notebook_id, ordered=True)
        total_steps = len(steps)

        if total_steps == 0:
            return {
                "completed_step_ids": [],
                "total_steps": 0,
                "completed_count": 0,
            }

        completed_ids = await LearnerStepProgress.get_completed_step_ids(
            user_id=user_id, notebook_id=notebook_id
        )

        return {
            "completed_step_ids": completed_ids,
            "total_steps": total_steps,
            "completed_count": len(completed_ids),
        }

    except Exception as e:
        logger.error(
            f"Error fetching step progress for user {user_id} in notebook {notebook_id}: {str(e)}"
        )
        return {"completed_step_ids": [], "total_steps": 0, "completed_count": 0}
