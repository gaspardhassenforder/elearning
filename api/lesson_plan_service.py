"""Lesson Plan Service - Business Logic for structured learning paths.

Handles AI generation of lesson plans from notebook sources, and progress
tracking for learners working through lesson steps.
"""

import asyncio
import json
import re
from typing import Dict, List, Optional

from ai_prompter import Prompter
from loguru import logger

from open_notebook.ai.provision import provision_langchain_model
from open_notebook.domain.learning_objective import LearningObjective
from open_notebook.domain.lesson_step import LessonStep
from open_notebook.domain.learner_step_progress import LearnerStepProgress
from open_notebook.domain.notebook import Notebook
from open_notebook.exceptions import DatabaseOperationError
from open_notebook.utils import (
    build_dual_key_lookup,
    clean_thinking_content,
    extract_json_array,
    extract_text_from_response,
)


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
        prompt = Prompter(prompt_template="lesson_plan/generate").render(
            data={"sources": sources_data}
        )

        # Call LLM
        model = await provision_langchain_model(
            prompt, model_id=None, default_type="chat", max_tokens=4096
        )
        response = await model.ainvoke(prompt)
        content = clean_thinking_content(extract_text_from_response(response.content)).strip()

        # Extract JSON array from response (may have trailing text)
        try:
            steps_data = extract_json_array(content)
        except ValueError:
            logger.error(f"No JSON array found in LLM response: {content[:200]}")
            return {
                "status": "failed",
                "error": "AI returned unexpected format. Please try again.",
            }

        # Delete existing auto-generated steps
        deleted = await LessonStep.delete_auto_generated_for_notebook(notebook_id)
        logger.info(f"Deleted {deleted} existing auto-generated steps")

        # Create new steps
        step_ids = []
        created_steps = []
        for i, step_data in enumerate(steps_data):
            # Validate step type
            step_type = step_data.get("step_type", "read")
            if step_type not in ("watch", "read", "quiz", "discuss", "podcast"):
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
                ai_instructions=step_data.get("ai_instructions") or None,
                order=i,
                required=True,
                auto_generated=True,
            )
            await step.save()
            if step.id:
                step_ids.append(str(step.id))
                created_steps.append(step)

        # Parallel ai_instructions enrichment — makes instructions content-specific
        all_objectives = await LearningObjective.get_for_notebook(notebook_id)

        async def _enrich_step(step: LessonStep):
            if step.step_type in ("read", "watch") and step.source_id:
                try:
                    from open_notebook.domain.notebook import Source
                    full_source = await Source.get(step.source_id)
                    text = (full_source.full_text or "")[:3000]
                    if not text:
                        return
                    related_objectives = [
                        obj.text for obj in all_objectives
                        if step.source_id in (obj.source_refs or [])
                    ]
                    prompt = Prompter(prompt_template="lesson_plan/enrich_instructions").render(
                        data={
                            "title": step.title,
                            "step_type": step.step_type,
                            "source_title": full_source.title or "Untitled",
                            "content": text,
                            "objectives": related_objectives,
                        }
                    )
                    model = await provision_langchain_model(prompt, None, "chat", max_tokens=1000)
                    response = await model.ainvoke(prompt)
                    enriched = clean_thinking_content(extract_text_from_response(response.content)).strip()
                    if enriched:
                        step.ai_instructions = enriched
                        await step.save()
                except Exception as e:
                    logger.warning("Failed to enrich ai_instructions for step {}: {}", step.id, str(e))

            elif step.step_type == "quiz":
                try:
                    sources_context = []
                    for source_entry in sources_data:
                        from open_notebook.domain.notebook import Source
                        try:
                            full_source = await Source.get(source_entry["id"])
                            text = (full_source.full_text or "")[:1500]
                            if text:
                                sources_context.append({
                                    "title": full_source.title or source_entry["title"],
                                    "content": text,
                                })
                        except Exception:
                            pass
                    if not sources_context:
                        return
                    prompt = Prompter(prompt_template="lesson_plan/enrich_quiz_instructions").render(
                        data={
                            "sources": sources_context,
                            "objectives": [obj.text for obj in all_objectives],
                        }
                    )
                    model = await provision_langchain_model(prompt, None, "chat", max_tokens=1000)
                    response = await model.ainvoke(prompt)
                    enriched = clean_thinking_content(extract_text_from_response(response.content)).strip()
                    if enriched:
                        step.ai_instructions = enriched
                        await step.save()
                except Exception as e:
                    logger.warning("Failed to enrich quiz ai_instructions for step {}: {}", step.id, str(e))

        await asyncio.gather(*[_enrich_step(s) for s in created_steps])

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

        # Collect unique source IDs and batch-resolve titles in a single query
        source_ids = [s.source_id for s in steps if s.source_id]
        source_title_map: dict[str, str] = {}

        if source_ids:
            from open_notebook.database.repository import repo_query, ensure_record_id

            try:
                record_ids = [ensure_record_id(sid) for sid in source_ids]
                rows = await repo_query(
                    "SELECT id, title FROM source WHERE id IN $ids",
                    {"ids": record_ids},
                )
                for row in rows:
                    raw_id = row.get("id")
                    # Normalise to the format stored in step.source_id ("source:xxx")
                    key = str(raw_id) if raw_id else None
                    if key:
                        source_title_map[key] = str(row.get("title") or "")
            except Exception as e:
                logger.warning(f"Could not batch-resolve source titles: {e}")

        return [
            {
                "id": str(s.id),
                "notebook_id": s.notebook_id,
                "title": s.title,
                "step_type": s.step_type,
                "source_id": s.source_id,
                "source_title": source_title_map.get(s.source_id, "") if s.source_id else None,
                "discussion_prompt": s.discussion_prompt,
                "ai_instructions": s.ai_instructions,
                "artifact_id": s.artifact_id,
                "command_id": s.command_id,
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


async def complete_step_with_objectives(user_id: str, step_id: str, notebook_id: str) -> dict:
    """Mark a lesson step complete and auto-complete objectives if all required steps are done.

    Shared logic used by both the HTTP endpoint and the chat tool.

    Args:
        user_id: Learner user record ID
        step_id: Lesson step record ID
        notebook_id: Notebook record ID (used for objective auto-completion check)

    Returns:
        Dict with message and all_objectives_completed flag
    """
    await LearnerStepProgress.mark_complete(user_id=user_id, step_id=step_id)

    all_objectives_completed = False
    try:
        from open_notebook.domain.learning_objective import LearningObjective
        from open_notebook.domain.learner_objective_progress import (
            CompletedVia,
            LearnerObjectiveProgress,
            ProgressStatus,
        )

        all_steps = await LessonStep.get_for_notebook(notebook_id)
        required = [s for s in all_steps if s.required]
        completed_ids = await LearnerStepProgress.get_completed_step_ids(user_id, notebook_id)

        if required and all(str(s.id) in completed_ids for s in required):
            objectives = await LearningObjective.get_for_notebook(notebook_id)
            await asyncio.gather(*[
                LearnerObjectiveProgress.create(
                    user_id=user_id,
                    objective_id=str(obj.id),
                    status=ProgressStatus.COMPLETED,
                    completed_via=CompletedVia.LESSON_COMPLETION,
                    evidence="All required lesson steps completed",
                )
                for obj in objectives
            ])
            all_objectives_completed = True
            logger.info(
                f"All steps complete for {notebook_id} — auto-completed {len(objectives)} objectives"
            )
    except Exception as e:
        logger.warning(
            "Auto-objective-completion failed for notebook {}: {}", notebook_id, str(e)
        )

    return {"message": "Step marked complete", "all_objectives_completed": all_objectives_completed}


async def trigger_podcast_for_step(
    step_id: str,
    title: Optional[str] = None,
    ai_instructions: Optional[str] = None,
    source_ids: Optional[List[str]] = None,
) -> "LessonStep":
    """Trigger podcast generation for a podcast-type lesson step.

    Args:
        step_id: Lesson step record ID
        title: Optional override for episode title
        ai_instructions: Optional override for podcast topic/instructions
        source_ids: Optional list of source IDs to use; uses all notebook sources if empty

    Returns:
        Updated LessonStep with command_id and artifact_id set

    Raises:
        ValueError: If step not found or wrong type
    """
    from api.podcast_service import PodcastService
    from open_notebook.database.repository import repo_query
    from open_notebook.domain.notebook import Source

    step = await LessonStep.get(step_id)
    if not step:
        raise ValueError(f"Lesson step {step_id} not found")
    if step.step_type != "podcast":
        raise ValueError(f"Step {step_id} is not a podcast step (type: {step.step_type})")

    if title is not None:
        step.title = title
    if ai_instructions is not None:
        step.ai_instructions = ai_instructions

    # Fetch all notebook sources
    notebook = await Notebook.get(step.notebook_id)
    if not notebook:
        raise ValueError(f"Notebook {step.notebook_id} not found")
    all_sources = await notebook.get_sources()

    # Filter to requested sources if provided
    if source_ids:
        selected = [s for s in all_sources if str(s.id) in source_ids]
    else:
        selected = all_sources

    # Build content from up to 5 sources
    texts = []
    for source in selected[:5]:
        text = (source.full_text or "").strip()
        if text:
            texts.append(text)
    content = "\n\n---\n\n".join(texts) if texts else ""

    # Fetch profiles
    episode_profiles = await repo_query("SELECT * FROM episode_profile LIMIT 1", {})
    speaker_profiles = await repo_query("SELECT * FROM speaker_profile LIMIT 1", {})

    if not episode_profiles or not speaker_profiles:
        raise ValueError("No podcast profiles configured. Please configure episode and speaker profiles first.")

    episode_profile_name = episode_profiles[0]["name"]
    speaker_profile_name = speaker_profiles[0]["name"]

    briefing = step.ai_instructions or step.title

    job_id, artifact_ids = await PodcastService.submit_generation_job(
        episode_profile_name=episode_profile_name,
        speaker_profile_name=speaker_profile_name,
        episode_name=step.title,
        notebook_id=step.notebook_id,
        briefing_suffix=briefing,
        created_by="admin",
        content=content if content else None,
    )

    step.command_id = job_id
    step.artifact_id = artifact_ids[0] if artifact_ids else None
    await step.save()

    logger.info("Triggered podcast generation for step {}: job {}", step.id, job_id)
    return step


async def refine_lesson_plan(notebook_id: str, refinement_prompt: str) -> dict:
    """Refine existing lesson plan based on admin's natural language instruction.

    Args:
        notebook_id: Notebook record ID
        refinement_prompt: Natural language instruction for how to change the plan

    Returns:
        Dict with status field
    """
    logger.info(f"Refining lesson plan for notebook {notebook_id}: {refinement_prompt[:50]}")

    try:
        steps = await LessonStep.get_for_notebook(notebook_id, ordered=True)
        if not steps:
            return {"status": "failed", "error": "No lesson steps found to refine"}

        steps_data = [
            {
                "id": str(s.id),
                "title": s.title,
                "step_type": s.step_type,
                "source_id": s.source_id,
                "discussion_prompt": s.discussion_prompt,
                "ai_instructions": s.ai_instructions,
                "order": s.order,
            }
            for s in steps
        ]

        prompt = Prompter(prompt_template="lesson_plan/refine").render(
            data={"steps": steps_data, "refinement_prompt": refinement_prompt}
        )

        model = await provision_langchain_model(prompt, None, "chat", max_tokens=4096)
        response = await model.ainvoke(prompt)
        content = clean_thinking_content(extract_text_from_response(response.content)).strip()

        try:
            revised_steps = extract_json_array(content)
        except ValueError:
            logger.error(f"No JSON array found in refine response: {content[:200]}")
            return {"status": "failed", "error": "AI returned unexpected format"}

        # Build lookup accepting both "lesson_step:abc" and bare "abc" from LLM
        existing_by_id = build_dual_key_lookup(steps)

        valid_step_types = {"watch", "read", "quiz", "discuss", "podcast"}

        async def _save_revised(i: int, step_data: dict):
            step_id = step_data.get("id")
            if not step_id or step_id not in existing_by_id:
                return
            step = existing_by_id[step_id]
            step.title = step_data.get("title") or step.title
            step.discussion_prompt = step_data.get("discussion_prompt") or None
            step.ai_instructions = step_data.get("ai_instructions") or step.ai_instructions
            new_type = step_data.get("step_type")
            if new_type and new_type in valid_step_types:
                step.step_type = new_type
            step.order = i
            await step.save()

        await asyncio.gather(*[_save_revised(i, sd) for i, sd in enumerate(revised_steps)])

        logger.info(f"Refined {len(revised_steps)} lesson steps for notebook {notebook_id}")
        return {"status": "completed"}

    except json.JSONDecodeError as e:
        logger.error(f"JSON parse error in lesson plan refinement: {str(e)}")
        return {"status": "failed", "error": "Failed to parse AI response"}
    except Exception as e:
        logger.error(f"Error refining lesson plan for notebook {notebook_id}: {str(e)}")
        return {"status": "failed", "error": str(e)}
