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
from open_notebook.database.repository import ensure_record_id, repo_query
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


async def _fetch_sources_with_insights(notebook_id: str) -> list[dict]:
    """Fetch all sources for a notebook enriched with their pre-generated insights."""
    notebook = await Notebook.get(notebook_id)
    if not notebook:
        return []
    sources = await notebook.get_sources()
    if not sources:
        return []

    async def _enrich(source) -> dict:
        source_id = str(source.id) if source.id else ""
        entry = {
            "id": source_id,
            "title": getattr(source, "title", None) or "Untitled",
            "source_type": "video" if _is_video_source(source) else "document",
            "insights": [],
        }
        try:
            insights = await source.get_insights()
            entry["insights"] = [
                {"insight_type": i.insight_type, "content": i.content}
                for i in insights
                if i.content and i.content.strip()
            ]
        except Exception as e:
            logger.warning("Failed to fetch insights for {}: {}", source_id, e)
        return entry

    return await asyncio.gather(*[_enrich(s) for s in sources])


async def _generate_outline(sources_with_insights: list[dict]) -> list[dict]:
    """Phase 1: LLM groups sources into thematic podcast episodes."""
    prompt = Prompter(prompt_template="lesson_plan/outline").render(
        data={"sources": sources_with_insights}
    )
    model = await provision_langchain_model(
        prompt, model_id=None, default_type="chat", max_tokens=8000
    )
    response = await model.ainvoke(prompt)
    content = clean_thinking_content(
        extract_text_from_response(response.content)
    ).strip()

    outline = extract_json_array(content)

    def _clean_str(v) -> str:
        """Collapse multi-line LLM strings to a single line to avoid JSON escaping issues."""
        return " ".join(str(v or "").split())

    valid_ids = {s["id"] for s in sources_with_insights}
    sanitized = []
    for ep in outline:
        if not isinstance(ep, dict):
            continue
        valid_ep_ids = [sid for sid in ep.get("source_ids", []) if sid in valid_ids]
        if not valid_ep_ids:
            logger.warning("Episode '{}' has no valid source IDs — skipping", ep.get("episode_title", "?"))
            continue

        sanitized.append({
            "episode_title": _clean_str(ep.get("episode_title", "Untitled Episode")),
            "source_ids": valid_ep_ids,
            "podcast_topic": _clean_str(ep.get("podcast_topic", "")),
            "key_concepts": ep.get("key_concepts", []),
            "ai_summary": _clean_str(ep.get("ai_summary", "")),
        })

    if not sanitized:
        raise ValueError("Outline phase produced no valid episodes.")

    logger.info("Outline phase: {} episodes from {} sources", len(sanitized), len(sources_with_insights))
    return sanitized


async def _generate_step_instructions(ep: dict, sources_with_insights: list[dict]) -> str:
    """Generate ai_instructions for a single episode via a focused LLM call.

    The LLM only produces teacher-guidance text — structured fields (source_ids,
    podcast_topic) are set by the caller from the outline, never from LLM output.
    """
    ep_source_ids = set(ep["source_ids"])
    relevant_insights = []
    for source in sources_with_insights:
        if source["id"] in ep_source_ids:
            for insight in source.get("insights", []):
                content = (insight.get("content") or "").strip()
                if content:
                    relevant_insights.append({
                        "source_id": source["id"],
                        "content": content[:600],
                    })

    prompt = Prompter(prompt_template="lesson_plan/step").render(
        data={
            "episode_title": ep["episode_title"],
            "podcast_topic": ep["podcast_topic"],
            "key_concepts": ep["key_concepts"],
            "ai_summary": ep["ai_summary"],
            "source_ids": ep["source_ids"],
            "source_insights": relevant_insights,
        }
    )
    model = await provision_langchain_model(
        prompt, model_id=None, default_type="chat", max_tokens=600
    )
    response = await model.ainvoke(prompt)
    return clean_thinking_content(extract_text_from_response(response.content)).strip()


async def generate_lesson_plan(notebook_id: str) -> Dict:
    """Generate a structured lesson plan for a notebook using AI.

    Two-phase approach:
    1. Phase 1 (outline): fetch sources + insights → LLM groups them into thematic episodes
    2. Phase 2 (steps): N parallel LLM calls (one per episode) generate ai_instructions text only;
       source_ids and podcast_topic are always set from the outline in Python, never from LLM output

    Args:
        notebook_id: Notebook record ID

    Returns:
        Dict with status, step_ids (if successful), and error (if failed)
    """
    logger.info(f"Generating lesson plan for notebook {notebook_id}")

    try:
        # Phase 1: fetch sources with insights → thematic outline
        sources_with_insights = await _fetch_sources_with_insights(notebook_id)
        if not sources_with_insights:
            return {
                "status": "failed",
                "error": "No sources found in this notebook. Please add sources before generating a lesson plan.",
            }

        no_insight_count = sum(1 for s in sources_with_insights if not s["insights"])
        if no_insight_count:
            logger.warning(
                "{}/{} sources have no insights — outline quality may be reduced",
                no_insight_count, len(sources_with_insights),
            )

        outline = await _generate_outline(sources_with_insights)

        # Phase 2: generate ai_instructions per episode in parallel (one LLM call each)
        # source_ids and podcast_topic are set from outline in Python — never from LLM output
        logger.debug(f"Generating step instructions for {len(outline)} episodes in parallel")
        step_instructions = await asyncio.gather(*[
            _generate_step_instructions(ep, sources_with_insights)
            for ep in outline
        ])

        deleted = await LessonStep.delete_auto_generated_for_notebook(notebook_id)
        logger.info(f"Deleted {deleted} existing auto-generated steps")

        step_ids = []

        for i, (ep, ai_instructions) in enumerate(zip(outline, step_instructions)):

            step = LessonStep(
                notebook_id=notebook_id,
                title=ep["episode_title"],
                step_type="podcast",
                source_id=None,
                source_ids=ep["source_ids"] if ep["source_ids"] else None,
                podcast_topic=ep["podcast_topic"] if ep["podcast_topic"] else None,
                ai_instructions=ai_instructions,
                discussion_prompt=None,
                order=i,
                required=True,
                auto_generated=True,
            )
            await step.save()
            if step.id:
                step_ids.append(str(step.id))

        # Add quiz step at the end covering all key concepts
        all_concepts = ", ".join(c for ep in outline for c in ep["key_concepts"])
        quiz_count = len(outline) * 2
        quiz_step = LessonStep(
            notebook_id=notebook_id,
            title="Module Knowledge Check",
            step_type="quiz",
            source_id=None,
            source_ids=None,
            podcast_topic=None,
            ai_instructions=f"Generate a {quiz_count}-question quiz covering: {all_concepts}. Test understanding and application, not just recall.",
            discussion_prompt=None,
            order=len(outline),
            required=True,
            auto_generated=True,
        )
        await quiz_step.save()
        if quiz_step.id:
            step_ids.append(str(quiz_step.id))

        logger.info(f"Generated {len(step_ids)} lesson steps for notebook {notebook_id}")
        return {"status": "completed", "step_ids": step_ids}

    except json.JSONDecodeError as e:
        logger.error(f"Unexpected JSON parse error in lesson plan generation: {str(e)}")
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
                "source_ids": s.source_ids,
                "podcast_topic": s.podcast_topic,
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


async def complete_step_with_objectives(
    user_id: str, step_id: str, notebook_id: str, score_percentage: Optional[float] = None
) -> dict:
    """Mark a lesson step complete and auto-complete objectives if all required steps are done.

    Shared logic used by both the HTTP endpoint and the chat tool.

    Args:
        user_id: Learner user record ID
        step_id: Lesson step record ID
        notebook_id: Notebook record ID (used for objective auto-completion check)

    Returns:
        Dict with message and all_objectives_completed flag
    """
    # Idempotency check: detect first-time completion before marking complete
    uid = user_id if user_id.startswith("user:") else f"user:{user_id}"
    sid = step_id if step_id.startswith("lesson_step:") else f"lesson_step:{step_id}"

    existing = await LearnerStepProgress._get_by_user_and_step(uid, sid)
    already_completed = existing is not None and existing.completed_at is not None

    await LearnerStepProgress.mark_complete(user_id=user_id, step_id=step_id)

    import math
    points_awarded = 0
    if not already_completed:
        step_points = math.ceil(50 * score_percentage / 100) if score_percentage is not None else 50
        points_awarded += step_points
        if step_points > 0:
            await repo_query(
                "UPDATE $uid SET points = (points ?? 0) + $pts",
                {"uid": ensure_record_id(uid), "pts": step_points},
            )

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
            if not already_completed:
                points_awarded += 50
                await repo_query(
                    "UPDATE $uid SET points = (points ?? 0) + 50",
                    {"uid": ensure_record_id(uid)},
                )
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

    return {"message": "Step marked complete", "all_objectives_completed": all_objectives_completed, "points_awarded": points_awarded}


async def trigger_podcast_for_step(
    step_id: str,
    title: Optional[str] = None,
    ai_instructions: Optional[str] = None,
    source_ids: Optional[List[str]] = None,
    episode_profile_name: Optional[str] = None,
    language: Optional[str] = "en",
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

    # Source selection: caller override → step.source_ids → parsed from ai_instructions → all sources
    # Fallback parsing handles cases where source_ids field wasn't persisted to DB
    effective_source_ids = source_ids or step.source_ids or []
    if not effective_source_ids and step.ai_instructions:
        parsed = re.findall(r'\[([a-z_]+:[a-zA-Z0-9]+)\]', step.ai_instructions)
        if parsed:
            effective_source_ids = parsed
            logger.info("Parsed {} source IDs from ai_instructions (source_ids field was null)", len(parsed))

    if effective_source_ids:
        effective_source_id_strs = {str(sid) for sid in effective_source_ids}
        selected = [s for s in all_sources if str(s.id) in effective_source_id_strs]
        if not selected:
            logger.warning("source_ids filter matched no sources — falling back to all sources")
            selected = all_sources
    else:
        selected = all_sources

    logger.info("Podcast for step {}: using {}/{} sources", step_id, len(selected), len(all_sources))

    # Build content from up to 5 sources
    texts = []
    for source in selected[:5]:
        text = (source.full_text or "").strip()
        if text:
            texts.append(text)
    content = "\n\n---\n\n".join(texts) if texts else ""

    # Fetch profiles — use caller-specified profile or fall back to first available
    if episode_profile_name:
        episode_profiles = await repo_query(
            "SELECT * FROM episode_profile WHERE name = $name LIMIT 1",
            {"name": episode_profile_name},
        )
        if not episode_profiles:
            raise ValueError(f"Episode profile '{episode_profile_name}' not found")
    else:
        episode_profiles = await repo_query("SELECT * FROM episode_profile LIMIT 1", {})

    if not episode_profiles:
        raise ValueError("No podcast profiles configured. Please configure episode and speaker profiles first.")

    episode_profile_name = episode_profiles[0]["name"]
    speaker_profile_name = episode_profiles[0].get("speaker_config", "")

    if not speaker_profile_name:
        speaker_profiles = await repo_query("SELECT * FROM speaker_profile LIMIT 1", {})
        if not speaker_profiles:
            raise ValueError("No speaker profiles configured.")
        speaker_profile_name = speaker_profiles[0]["name"]

    # Briefing: caller override → step.podcast_topic → step.title
    # Never use the full ai_instructions as briefing (it's for AI teacher post-summary, not the podcast generator)
    briefing = ai_instructions or step.podcast_topic or step.title

    job_id, artifact_ids = await PodcastService.submit_generation_job(
        episode_profile_name=episode_profile_name,
        speaker_profile_name=speaker_profile_name,
        episode_name=step.title,
        notebook_id=step.notebook_id,
        briefing_suffix=briefing,
        created_by="admin",
        content=content if content else None,
        language=language or "en",
    )

    step.command_id = job_id
    step.artifact_id = artifact_ids[0] if artifact_ids else None
    await step.save()

    logger.info("Triggered podcast generation for step {}: job {}", step.id, job_id)
    return step


async def refine_lesson_plan(notebook_id: str, refinement_prompt: str) -> dict:
    """Refine existing lesson plan based on admin's natural language instruction.

    Supports full structural editing: modify, add, remove, and reorder steps.
    New steps (id=null) are created; steps omitted from AI response are deleted.

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

        # steps[0].notebook_id is guaranteed normalized by the field_validator
        nb_record_id = ensure_record_id(steps[0].notebook_id)

        # Fetch sources and existing podcast artifacts in parallel
        notebook, raw_podcasts = await asyncio.gather(
            Notebook.get(notebook_id),
            repo_query(
                "SELECT id, title FROM artifact WHERE notebook_id = $nb_id AND artifact_type = 'podcast'",
                {"nb_id": nb_record_id},
            ),
        )
        all_sources = await notebook.get_sources() if notebook else []
        valid_source_ids = {str(s.id) for s in all_sources}
        sources_data = [
            {
                "id": str(s.id),
                "title": getattr(s, "title", None) or "Untitled",
                "source_type": "video" if _is_video_source(s) else "document",
            }
            for s in all_sources
        ]

        # Build podcast list with 1-based integer refs so the AI never has to echo raw IDs.
        # step.artifact_id stores the artifact tracker id (artifact:xxx).
        artifact_ref_map: dict[int, str] = {}  # ref → artifact tracker id
        artifact_id_to_ref: dict[str, int] = {}  # tracker id → ref (for existing step display)
        podcasts_data = []
        for row in raw_podcasts:
            if not row.get("id"):
                continue
            tracker_id = str(row["id"])
            ref = len(podcasts_data) + 1
            artifact_ref_map[ref] = tracker_id
            artifact_id_to_ref[tracker_id] = ref
            podcasts_data.append({"ref": ref, "title": row.get("title") or "Untitled"})

        steps_data = [
            {
                "id": str(s.id),
                "title": s.title,
                "step_type": s.step_type,
                "source_ids": s.source_ids or [],
                "podcast_topic": s.podcast_topic,
                "discussion_prompt": s.discussion_prompt,
                "ai_instructions": s.ai_instructions,
                # Show the podcast ref number rather than the raw tracker ID
                "podcast_ref": artifact_id_to_ref.get(s.artifact_id) if s.artifact_id else None,
                "order": s.order,
            }
            for s in steps
        ]

        prompt = Prompter(prompt_template="lesson_plan/refine").render(
            data={"steps": steps_data, "sources": sources_data, "podcasts": podcasts_data, "refinement_prompt": refinement_prompt}
        )

        model = await provision_langchain_model(prompt, None, "chat", max_tokens=8192)
        response = await model.ainvoke(prompt)
        content = clean_thinking_content(extract_text_from_response(response.content)).strip()

        try:
            revised_steps = extract_json_array(content)
        except ValueError:
            logger.error(f"No JSON array found in refine response: {content[:200]}")
            return {"status": "failed", "error": "AI returned unexpected format"}

        logger.debug("AI revised_steps: {}", revised_steps)

        # Build lookup accepting both "lesson_step:abc" and bare "abc" from LLM
        existing_by_id = build_dual_key_lookup(steps)
        valid_step_types = {"watch", "read", "quiz", "discuss", "podcast"}

        # Pre-scan: mutate objects in-memory, collect save coroutines, and populate returned_ids.
        # Sequential categorization ensures returned_ids is complete before the deletion pass.
        returned_ids: set[str] = set()
        save_coros = []

        for i, step_data in enumerate(revised_steps):
            step_id = step_data.get("id")
            step_type = step_data.get("step_type", "read")
            if step_type not in valid_step_types:
                step_type = "read"

            # Filter source_ids to only valid notebook sources.
            # Empty list from AI means "clear"; non-empty but all-invalid means "keep old".
            raw_source_ids = step_data.get("source_ids") or []
            filtered_source_ids = [sid for sid in raw_source_ids if sid in valid_source_ids]

            # Resolve podcast_ref (integer) → artifact tracker id; ignore invalid/missing refs
            podcast_ref = step_data.get("podcast_ref")
            try:
                artifact_id = artifact_ref_map.get(int(podcast_ref)) if podcast_ref else None
            except (TypeError, ValueError):
                artifact_id = None

            if step_id and step_id in existing_by_id:
                # UPDATE existing step
                returned_ids.add(step_id)
                step = existing_by_id[step_id]
                step.title = step_data.get("title") or step.title
                step.step_type = step_type
                step.discussion_prompt = step_data.get("discussion_prompt") or None
                step.ai_instructions = step_data.get("ai_instructions") or step.ai_instructions
                # Respect intentional empty list (clear); fall back only when AI hallucinated IDs
                step.source_ids = [] if not raw_source_ids else (filtered_source_ids or step.source_ids)
                step.podcast_topic = step_data.get("podcast_topic") or step.podcast_topic
                if artifact_id is not None:
                    step.artifact_id = artifact_id
                step.order = i
                save_coros.append(step.save())
            else:
                # CREATE new step (id is null/missing/unknown)
                title = (step_data.get("title") or "").strip()
                if not title:
                    logger.warning("Skipping new step with empty title at position {}", i)
                    continue
                new_step = LessonStep(
                    notebook_id=notebook_id,
                    title=title,
                    step_type=step_type,
                    source_id=None,
                    source_ids=filtered_source_ids or None,
                    podcast_topic=step_data.get("podcast_topic") or None,
                    ai_instructions=step_data.get("ai_instructions") or None,
                    discussion_prompt=step_data.get("discussion_prompt") or None,
                    artifact_id=artifact_id,
                    order=i,
                    required=True,
                    auto_generated=True,
                )
                logger.info("Creating new lesson step '{}' (type: {}) at position {}", title, step_type, i)
                save_coros.append(new_step.save())

        # Persist all updates and creates in parallel
        await asyncio.gather(*save_coros)

        # Bulk-delete steps omitted from AI response (single round-trip)
        ids_to_delete = []
        for step in steps:
            sid = str(step.id)
            bare = sid.split(":", 1)[1] if ":" in sid else sid
            if sid not in returned_ids and bare not in returned_ids:
                ids_to_delete.append(ensure_record_id(sid))
        if ids_to_delete:
            await repo_query("DELETE lesson_step WHERE id IN $ids", {"ids": ids_to_delete})
            logger.info("Bulk deleted {} omitted lesson steps", len(ids_to_delete))

        logger.info(
            f"Refined lesson plan for {notebook_id}: {len(revised_steps)} steps returned, "
            f"{len(ids_to_delete)} deleted"
        )
        return {"status": "completed"}

    except json.JSONDecodeError as e:
        logger.error(f"JSON parse error in lesson plan refinement: {str(e)}")
        return {"status": "failed", "error": "Failed to parse AI response"}
    except Exception as e:
        logger.error(f"Error refining lesson plan for notebook {notebook_id}: {str(e)}")
        return {"status": "failed", "error": str(e)}
