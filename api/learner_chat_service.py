"""Learner Chat Service - Business Logic for AI Teacher Conversations.

Handles learner profile loading, prompt assembly, and access validation for chat.

Story: 4.1 - Learner Chat Interface & SSE Streaming
Story: 4.2 - Two-Layer Prompt System & Proactive AI Teacher
"""

import asyncio
from typing import Optional, Tuple

from fastapi import HTTPException
from loguru import logger

from api.auth import LearnerContext
from open_notebook.database.repository import ensure_record_id
from open_notebook.domain.notebook import Notebook
from open_notebook.domain.module_assignment import ModuleAssignment
from open_notebook.domain.learning_objective import LearningObjective
from open_notebook.domain.learner_objective_progress import LearnerObjectiveProgress
from open_notebook.domain.lesson_step import LessonStep
from open_notebook.graphs.prompt import assemble_system_prompt

def build_intro_message(learner_profile: dict, language: str = "en-US") -> str:
    """Build hidden intro message for first-visit greeting.

    Creates a personalized introduction from the learner profile that is sent
    as a hidden HumanMessage to the graph, triggering a natural AI greeting.
    This message is filtered out in the /history endpoint (never shown to user).

    Args:
        learner_profile: Dict with 'name', 'role', 'job_description', 'ai_familiarity'
        language: UI language code (e.g., 'en-US', 'fr-FR')

    Returns:
        Intro message string in the appropriate language
    """
    name = learner_profile.get("name", "there")
    role = learner_profile.get("role", "a learner")
    job = learner_profile.get("job_description", "")
    familiarity = learner_profile.get("ai_familiarity", "intermediate")

    if language == "fr-FR":
        parts = [f"Bonjour ! Je m'appelle {name}."]
        parts.append(f"Je travaille comme {role}.")
        if job:
            parts.append(job)
        parts.append(f"Mon expérience avec l'IA est : {familiarity}.")
        parts.append("Commençons le cours.")
    elif language == "pt-BR":
        parts = [f"Olá! Meu nome é {name}."]
        parts.append(f"Trabalho como {role}.")
        if job:
            parts.append(job)
        parts.append(f"Minha experiência com IA é: {familiarity}.")
        parts.append("Vamos começar a aula.")
    elif language == "zh-CN":
        parts = [f"你好！我叫{name}。"]
        parts.append(f"我的职业是{role}。")
        if job:
            parts.append(job)
        parts.append(f"我对AI的熟悉程度：{familiarity}。")
        parts.append("让我们开始课程吧。")
    elif language == "zh-TW":
        parts = [f"你好！我叫{name}。"]
        parts.append(f"我的職業是{role}。")
        if job:
            parts.append(job)
        parts.append(f"我對AI的熟悉程度：{familiarity}。")
        parts.append("讓我們開始課程吧。")
    else:
        # Default: English
        parts = [f"Hello! My name is {name}."]
        parts.append(f"I work as {role}.")
        if job:
            parts.append(job)
        parts.append(f"My experience with AI is {familiarity}.")
        parts.append("Let's start the lesson.")

    parts.append(
        "Note to AI: For this welcome greeting, do NOT call search_knowledge_base. "
        "All module context is already provided in your system prompt. "
        "Greet the learner based on that information. "
        "You may call surface_document if you want to highlight a specific resource."
    )
    return " ".join(parts)


async def get_learner_objectives_with_status(
    notebook_id: str, user_id: str
) -> list[dict]:
    """Load learning objectives with learner's completion status.

    Story 4.4: Fetches objectives with progress status for prompt injection.
    Uses LEFT JOIN to include objectives with no progress (not_started).

    Args:
        notebook_id: Notebook/module record ID
        user_id: Learner's user record ID

    Returns:
        List of dicts with 'text', 'status', 'order', 'completed_at', 'evidence'
        Status is: 'not_started', 'in_progress', or 'completed'
    """
    from open_notebook.database.repository import repo_query

    # Ensure IDs have correct format
    if not notebook_id.startswith("notebook:"):
        notebook_id = f"notebook:{notebook_id}"
    if not user_id.startswith("user:"):
        user_id = f"user:{user_id}"

    try:
        # Two separate queries to avoid unsupported LEFT JOIN syntax in SurrealDB
        # Query 1: Load all objectives for notebook
        objectives_result = await repo_query(
            """
            SELECT * FROM learning_objective
            WHERE notebook_id = $notebook_id
            ORDER BY order ASC
            """,
            {"notebook_id": ensure_record_id(notebook_id)},
        )

        # Query 2: Load progress for this user in this notebook
        progress_result = await repo_query(
            """
            SELECT * FROM learner_objective_progress
            WHERE user_id = $user_id
              AND objective_id IN (
                SELECT VALUE id FROM learning_objective WHERE notebook_id = $notebook_id
              )
            """,
            {"notebook_id": ensure_record_id(notebook_id), "user_id": ensure_record_id(user_id)},
        )

        # Build progress lookup map
        progress_map = {}
        for p in progress_result:
            obj_id = str(p.get("objective_id", ""))
            progress_map[obj_id] = p

        # Merge objectives with progress
        objectives_with_status = []
        for row in objectives_result:
            obj_id = str(row.get("id", ""))
            progress = progress_map.get(obj_id)
            objectives_with_status.append({
                "id": row.get("id"),
                "text": row.get("text", ""),
                "order": row.get("order", 0),
                "auto_generated": row.get("auto_generated", False),
                "status": (progress.get("status") if progress else None) or "not_started",
                "completed_at": progress.get("completed_at") if progress else None,
                "evidence": progress.get("evidence") if progress else None,
            })

        logger.debug(
            f"Loaded {len(objectives_with_status)} objectives for user {user_id} in notebook {notebook_id}"
        )
        return objectives_with_status

    except Exception as e:
        logger.error("Error loading objectives with progress: {}", str(e))
        # Fallback to objectives without progress on error
        try:
            objectives = await LearningObjective.get_for_notebook(notebook_id)
            return [
                {
                    "id": obj.id,
                    "text": obj.text,
                    "order": obj.order,
                    "auto_generated": getattr(obj, "auto_generated", False),
                    "status": "not_started",
                    "completed_at": None,
                    "evidence": None,
                }
                for obj in objectives
            ]
        except Exception as e2:
            logger.error(f"Fallback objectives load also failed: {e2}")
            return []


async def get_lesson_steps_with_status(
    notebook_id: str, user_id: str
) -> tuple[list[dict], Optional[dict]]:
    """Load lesson steps with learner's completion status.

    Fetches ordered lesson steps and merges with learner progress to
    assign status: completed | current | upcoming. The first incomplete
    required step is marked "current".

    Args:
        notebook_id: Notebook/module record ID
        user_id: Learner's user record ID

    Returns:
        Tuple of (steps_with_status, current_step)
        steps_with_status: List of step dicts with 'status' field
        current_step: The first incomplete required step (or None)
    """
    from open_notebook.database.repository import repo_query

    # Ensure IDs have correct format
    if not notebook_id.startswith("notebook:"):
        notebook_id = f"notebook:{notebook_id}"
    if not user_id.startswith("user:"):
        user_id = f"user:{user_id}"

    try:
        # Load all steps for notebook ordered by position
        steps = await LessonStep.get_for_notebook(notebook_id, ordered=True)
        if not steps:
            return [], None

        # Load completed step IDs for this user in this notebook
        step_ids = [str(s.id) for s in steps if s.id]
        if step_ids:
            completed_result = await repo_query(
                """
                SELECT VALUE type::string(step_id) FROM learner_step_progress
                WHERE user_id = $user_id
                  AND step_id IN $step_ids
                """,
                {
                    "user_id": ensure_record_id(user_id),
                    "step_ids": [ensure_record_id(sid) for sid in step_ids],
                },
            )
            completed_ids = set(completed_result or [])
        else:
            completed_ids = set()

        # Build steps with status
        steps_with_status = []
        current_step_found = False
        current_step = None

        for step in steps:
            step_id = str(step.id) if step.id else ""
            is_completed = step_id in completed_ids

            if is_completed:
                status = "completed"
            elif not current_step_found and step.required:
                status = "current"
                current_step_found = True
                current_step = {
                    "id": step_id,
                    "title": step.title,
                    "step_type": step.step_type,
                    "source_id": step.source_id,
                    "discussion_prompt": step.discussion_prompt,
                    "ai_instructions": step.ai_instructions,
                    "artifact_id": step.artifact_id,
                    "status": "current",
                }
            else:
                status = "upcoming"

            steps_with_status.append({
                "id": step_id,
                "title": step.title,
                "step_type": step.step_type,
                "source_id": step.source_id,
                "discussion_prompt": step.discussion_prompt,
                "ai_instructions": step.ai_instructions,
                "artifact_id": step.artifact_id,
                "order": step.order,
                "required": step.required,
                "status": status,
            })

        logger.debug(
            f"Loaded {len(steps_with_status)} lesson steps for user {user_id} in notebook {notebook_id}; "
            f"current: {current_step['title'] if current_step else 'none'}"
        )
        return steps_with_status, current_step

    except Exception as e:
        logger.error("Error loading lesson steps with status: {}", str(e))
        return [], None


async def build_source_context_for_learner(notebook_id: str) -> Optional[str]:
    """Build FULL source context string for the learner system prompt (legacy).

    Loads sources for the notebook and formats their insights into a context
    string that populates the {{ context }} variable in the system prompt template.
    ~50K chars. Kept for backward compatibility but superseded by
    build_lightweight_context for learner ReAct chat.

    Args:
        notebook_id: Notebook/module record ID

    Returns:
        Formatted context string with source titles and insights, or None on failure
    """
    try:
        notebook = await Notebook.get(notebook_id)
        if not notebook:
            logger.warning("Notebook {} not found for source context", notebook_id)
            return None

        sources = await notebook.get_sources()
        if not sources:
            logger.debug("No sources found for notebook {}", notebook_id)
            return None

        context_parts = []
        total_chars = 0
        max_total_chars = 50_000
        max_insight_chars = 500

        for source in sources:
            if total_chars >= max_total_chars:
                break

            try:
                source_context = await source.get_context("short")
                source_id = source_context.get("id", "unknown")
                # Strip table prefix (e.g. "source:m02eadg..." → "m02eadg...")
                # because the format string already adds "source:" prefix
                if isinstance(source_id, str) and ":" in source_id:
                    source_id = source_id.split(":", 1)[1]
                source_title = source_context.get("title", "Untitled")
                insights = source_context.get("insights", [])

                section = f'## [source:{source_id}] - "{source_title}"\n'

                if insights:
                    section += "Insights:\n"
                    for insight in insights:
                        insight_type = insight.get("insight_type", "summary")
                        content = insight.get("content", "")
                        if len(content) > max_insight_chars:
                            content = content[:max_insight_chars] + "..."
                        section += f"  - {insight_type}: {content}\n"
                else:
                    section += "  (No insights available)\n"

                if total_chars + len(section) > max_total_chars:
                    break

                context_parts.append(section)
                total_chars += len(section)

            except Exception as e:
                logger.warning("Failed to get context for source {}: {}", source.id, str(e))
                continue

        if not context_parts:
            return None

        result = "\n".join(context_parts)
        logger.info(
            "Built source context for notebook {}: {} sources, {} chars",
            notebook_id, len(context_parts), len(result)
        )
        return result

    except Exception as e:
        logger.error("Failed to build source context for notebook {}: {}", notebook_id, str(e))
        return None


async def build_lightweight_context(notebook_id: str) -> Optional[str]:
    """Build lightweight source context (~5K tokens) for learner ReAct chat.

    Instead of stuffing ~50K chars of full insights, includes only summaries,
    key_concepts, and topics. The LLM uses search_knowledge_base tool for
    detailed content retrieval on demand.

    Args:
        notebook_id: Notebook/module record ID

    Returns:
        Formatted lightweight context string, or None on failure
    """
    LIGHTWEIGHT_INSIGHT_TYPES = {"summary", "key_concepts", "topics"}
    MAX_TOTAL_CHARS = 8_000  # ~5K tokens
    MAX_INSIGHT_CHARS = 200

    try:
        notebook = await Notebook.get(notebook_id)
        if not notebook:
            logger.warning("Notebook {} not found for lightweight context", notebook_id)
            return None

        sources = await notebook.get_sources()
        if not sources:
            logger.debug("No sources found for notebook {}", notebook_id)
            return None

        context_parts = []
        total_chars = 0

        for source in sources:
            if total_chars >= MAX_TOTAL_CHARS:
                break

            try:
                source_context = await source.get_context("short")
                source_id = source_context.get("id", "unknown")
                if isinstance(source_id, str) and ":" in source_id:
                    source_id = source_id.split(":", 1)[1]
                source_title = source_context.get("title", "Untitled")
                insights = source_context.get("insights", [])

                section = f'## [source:{source_id}] - "{source_title}"\n'

                # Only include lightweight insight types
                relevant_insights = [
                    i for i in insights
                    if i.get("insight_type", "") in LIGHTWEIGHT_INSIGHT_TYPES
                ]

                if relevant_insights:
                    for insight in relevant_insights:
                        insight_type = insight.get("insight_type", "summary")
                        content = insight.get("content", "")
                        if len(content) > MAX_INSIGHT_CHARS:
                            content = content[:MAX_INSIGHT_CHARS] + "..."
                        section += f"  - {insight_type}: {content}\n"
                else:
                    section += "  (Use search_knowledge_base to explore this source)\n"

                if total_chars + len(section) > MAX_TOTAL_CHARS:
                    break

                context_parts.append(section)
                total_chars += len(section)

            except Exception as e:
                logger.warning(
                    "Failed to get context for source {}: {}", source.id, str(e)
                )
                continue

        if not context_parts:
            return None

        result = "\n".join(context_parts)
        result += (
            "\n\nThese summaries contain the key information for each source. Do NOT call search_knowledge_base unless the learner asks a very specific question not covered above."
        )

        logger.info(
            "Built lightweight context for notebook {}: {} sources, {} chars",
            notebook_id, len(context_parts), len(result),
        )
        return result

    except Exception as e:
        logger.error(
            "Failed to build lightweight context for notebook {}: {}",
            notebook_id, str(e),
        )
        return None


async def validate_learner_access_to_notebook(
    notebook_id: str, learner_context: LearnerContext
) -> Notebook:
    """Validate learner has access to a notebook.

    Checks:
    1. Notebook exists
    2. Notebook is published (learners cannot see drafts)
    3. Notebook is assigned to learner's company
    4. Notebook is not locked (Story 2.3)

    Args:
        notebook_id: Notebook/module record ID
        learner_context: Authenticated learner context

    Returns:
        Notebook instance if access is granted

    Raises:
        HTTPException 403: Access denied (not assigned, locked, or unpublished)
        HTTPException 404: Notebook not found
    """
    from open_notebook.database.repository import repo_query

    # Step 1: Check assignment exists for learner's company
    assignment_result = await repo_query(
        """
        SELECT * FROM module_assignment
        WHERE notebook_id = $notebook_id
          AND company_id = $company_id
        LIMIT 1
        """,
        {"notebook_id": ensure_record_id(notebook_id), "company_id": ensure_record_id(learner_context.company_id)},
    )

    if not assignment_result:
        logger.warning(
            f"Learner {learner_context.user.id} attempted to access unassigned notebook {notebook_id}"
        )
        raise HTTPException(
            status_code=403, detail="You do not have access to this module"
        )

    assignment_data = assignment_result[0]

    # Validate locked status (Story 2.3)
    is_locked = assignment_data.get("is_locked", False)
    if not isinstance(is_locked, bool):
        logger.warning(f"Invalid is_locked type for notebook {notebook_id}: {type(is_locked)}")
        is_locked = bool(is_locked)

    if is_locked:
        logger.warning(
            f"Learner {learner_context.user.id} attempted to access locked notebook {notebook_id}"
        )
        raise HTTPException(
            status_code=403,
            detail="This module is currently locked and not available",
        )

    # Step 2: Fetch notebook and validate published status
    try:
        notebook = await Notebook.get(notebook_id)
    except Exception as e:
        logger.error("Error fetching notebook {}: {}", notebook_id, str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

    if not notebook:
        logger.warning(
            f"Learner {learner_context.user.id} attempted to access non-existent notebook {notebook_id}"
        )
        raise HTTPException(
            status_code=403, detail="You do not have access to this module"
        )

    published = getattr(notebook, "published", True)
    if not published:
        logger.warning(
            f"Learner {learner_context.user.id} attempted to access unpublished notebook {notebook_id}"
        )
        raise HTTPException(
            status_code=403, detail="You do not have access to this module"
        )

    logger.info(
        f"Learner {learner_context.user.id} validated access to notebook {notebook_id}"
    )
    return notebook


def extract_learner_profile(learner: LearnerContext) -> dict:
    """Extract learner profile dict from LearnerContext.

    Args:
        learner: Authenticated learner context

    Returns:
        Dict with 'name', 'role', 'ai_familiarity', 'job_description'
    """
    return {
        "name": learner.user.profile.get("name", learner.user.username)
        if learner.user.profile
        else learner.user.username,
        "role": learner.user.profile.get("role", "Unknown")
        if learner.user.profile
        else "Unknown",
        "ai_familiarity": learner.user.profile.get("ai_familiarity", "beginner")
        if learner.user.profile
        else "beginner",
        "job_description": learner.user.profile.get("job_description", "")
        if learner.user.profile
        else "",
    }


async def init_thread_context(
    notebook_id: str, learner: LearnerContext, language: Optional[str] = None
) -> Tuple[str, dict, list, list]:
    """Full context load for new thread initialization only.

    Assembles all context needed for a new conversation thread (11 queries).
    Called only once per thread lifetime; subsequent turns use lightweight reconciliation.

    Args:
        notebook_id: Notebook/module record ID
        learner: Authenticated learner context
        language: UI language code

    Returns:
        Tuple of (system_prompt, learner_profile_dict, objectives_with_status, lesson_steps)

    Raises:
        HTTPException: If prompt assembly fails
    """
    logger.info(f"Initializing new thread context for notebook {notebook_id}")

    # 1. Load learner profile from User.profile field
    learner_profile = extract_learner_profile(learner)
    logger.debug(f"Learner profile: {learner_profile}")

    # 2-4. Load objectives, source context, and lesson steps in parallel
    async def _safe_get_objectives():
        try:
            result = await get_learner_objectives_with_status(notebook_id=notebook_id, user_id=learner.user.id)
            logger.debug(f"Loaded {len(result)} learning objectives with progress")
            return result
        except Exception as e:
            logger.warning("Failed to load learning objectives for notebook {}: {}", notebook_id, str(e))
            return []

    async def _safe_get_context():
        try:
            return await build_lightweight_context(notebook_id)
        except Exception as e:
            logger.warning("Failed to build source context for notebook {}: {}", notebook_id, str(e))
            return None

    async def _safe_get_steps():
        try:
            steps, current = await get_lesson_steps_with_status(notebook_id=notebook_id, user_id=learner.user.id)
            logger.debug(f"Loaded {len(steps)} lesson steps for notebook {notebook_id}")
            return steps, current
        except Exception as e:
            logger.warning("Failed to load lesson steps for notebook {}: {}", notebook_id, str(e))
            return [], None

    objectives_with_status, source_context, (lesson_steps, current_step) = await asyncio.gather(
        _safe_get_objectives(),
        _safe_get_context(),
        _safe_get_steps(),
    )

    # 5. Assemble system prompt (global + per-module)
    try:
        system_prompt = await assemble_system_prompt(
            notebook_id=notebook_id,
            learner_profile=learner_profile,
            objectives_with_status=objectives_with_status,
            context=source_context,
            language=language,
            lesson_steps=lesson_steps if lesson_steps else None,
            current_step=current_step,
        )
        logger.info(
            f"System prompt assembled: {len(system_prompt)} chars for notebook {notebook_id}"
        )
    except Exception as e:
        logger.error("Failed to assemble system prompt for notebook {}: {}", notebook_id, str(e))
        raise HTTPException(
            status_code=500,
            detail="Internal server error. Please try again later."
        )

    return system_prompt, learner_profile, objectives_with_status, lesson_steps
