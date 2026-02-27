"""Learner Chat Service - Business Logic for AI Teacher Conversations.

Handles learner profile loading, prompt assembly, and access validation for chat.

Story: 4.1 - Learner Chat Interface & SSE Streaming
Story: 4.2 - Two-Layer Prompt System & Proactive AI Teacher
"""

import json as _json
import re as _re
from typing import AsyncGenerator, Optional, Tuple

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
from open_notebook.ai.provision import provision_langchain_model
from open_notebook.utils import extract_text_from_response


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


async def generate_quick_replies(
    user_message: str,
    ai_response: str,
) -> list[str]:
    """Generate 3 contextual quick-reply suggestions using a cheap Gemini model.

    Runs after each AI response to produce clickable buttons that guide the
    learner toward useful next actions without revealing answers.

    Args:
        user_message: The learner's last message
        ai_response: The AI tutor's full response (truncated for cost)

    Returns:
        List of 3 short reply strings, or [] on failure
    """
    from esperanto import AIFactory
    from langchain_core.messages import HumanMessage

    # Truncate to keep the call cheap
    response_preview = ai_response[:600] if len(ai_response) > 600 else ai_response
    user_preview = user_message[:200] if len(user_message) > 200 else user_message

    prompt = (
        "You generate 3 short reply suggestions for a learner in an educational chat.\n\n"
        f'The learner said: "{user_preview}"\n'
        f'The AI tutor responded: "{response_preview}"\n\n'
        "Generate exactly 3 short follow-up options the learner might want to send:\n"
        "- Maximum 8 words each\n"
        "- Do NOT suggest anything that reveals answers or does the thinking for them\n"
        "- Vary them: one showing readiness/progress, one requesting help/clarification, "
        "one going deeper or asking a genuine question\n"
        "- Keep them natural and concise\n\n"
        'Respond ONLY with a JSON array of 3 strings, no other text:\n["option 1", "option 2", "option 3"]'
    )

    try:
        model = AIFactory.create_language(
            model_name="gemini-2.0-flash-lite",
            provider="google",
        )
        lc_model = model.to_langchain()
        response = await lc_model.ainvoke([HumanMessage(content=prompt)])
        text = response.content if hasattr(response, "content") else str(response)
        # Strip extended-thinking tags if present
        text = _re.sub(r"<think>.*?</think>", "", text, flags=_re.DOTALL).strip()
        match = _re.search(r"\[.*?\]", text, _re.DOTALL)
        if match:
            replies = _json.loads(match.group())
            if isinstance(replies, list) and len(replies) >= 3:
                return [str(r).strip() for r in replies[:3]]
    except Exception as e:
        logger.warning("Quick replies generation failed: {}", str(e))

    return []


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
            "\n\n**For detailed content, use the search_knowledge_base tool.**"
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


async def prepare_chat_context(
    notebook_id: str, learner: LearnerContext, language: Optional[str] = None
) -> Tuple[str, dict, list]:
    """Prepare context for learner chat.

    Assembles:
    1. Learner profile (role, AI familiarity, job description)
    2. Learning objectives with completion status
    3. Lightweight source context (~5K tokens instead of 50K)
    4. System prompt (global + per-module via Story 3.4 assemble_system_prompt)

    Args:
        notebook_id: Notebook/module record ID
        learner: Authenticated learner context
        language: UI language code

    Returns:
        Tuple of (system_prompt, learner_profile_dict, objectives_with_status)

    Raises:
        Exception: If prompt assembly fails
    """
    logger.info(f"Preparing chat context for notebook {notebook_id}")

    # 1. Load learner profile from User.profile field (Story 1.4 questionnaire)
    learner_profile = {
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

    logger.debug(f"Learner profile: {learner_profile}")

    # 2. Load learning objectives with completion status (Story 4.4)
    # Load actual progress from LearnerObjectiveProgress table
    try:
        objectives_with_status = await get_learner_objectives_with_status(
            notebook_id=notebook_id,
            user_id=learner.user.id
        )
        logger.debug(f"Loaded {len(objectives_with_status)} learning objectives with progress")
    except Exception as e:
        logger.warning("Failed to load learning objectives for notebook {}: {}", notebook_id, str(e))
        objectives_with_status = []

    # 3. Build lightweight source context (~5K tokens) for ReAct chat
    try:
        source_context = await build_lightweight_context(notebook_id)
    except Exception as e:
        logger.warning("Failed to build source context for notebook {}: {}", notebook_id, str(e))
        source_context = None

    # 4. Load lesson steps with completion status (if notebook has a lesson plan)
    try:
        lesson_steps, current_step = await get_lesson_steps_with_status(
            notebook_id=notebook_id,
            user_id=learner.user.id,
        )
        logger.debug(f"Loaded {len(lesson_steps)} lesson steps for notebook {notebook_id}")
    except Exception as e:
        logger.warning("Failed to load lesson steps for notebook {}: {}", notebook_id, str(e))
        lesson_steps, current_step = [], None

    # 5. Assemble system prompt (global + per-module from Story 3.4)
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
        # Generic error message - don't leak internal details
        raise HTTPException(
            status_code=500,
            detail="Internal server error. Please try again later."
        )

    return system_prompt, learner_profile, objectives_with_status


async def generate_proactive_greeting(
    notebook_id: str, learner_profile: dict, notebook: Notebook, language: str = "en-US"
) -> str:
    """Generate personalized proactive greeting for first visit via LLM.

    Uses a single LLM call to generate a natural, personalized greeting that:
    1. References learner's role and AI familiarity
    2. Mentions their job context
    3. Introduces the first learning objective
    4. Asks an engaging opening question
    5. Handles language naturally (no rigid template)

    Follows the same pattern as generate_re_engagement_greeting() in prompt.py.

    Args:
        notebook_id: Notebook/module record ID
        learner_profile: Learner profile dict with role, ai_familiarity, job_description
        notebook: Notebook instance
        language: UI language code (e.g., 'en-US', 'fr-FR') for greeting language

    Returns:
        Personalized greeting string
    """
    logger.info(f"Generating proactive greeting for notebook {notebook_id}")

    # 1. Load learning objectives
    try:
        objectives = await LearningObjective.get_for_notebook(notebook_id)
        logger.debug(f"Found {len(objectives)} learning objectives for notebook {notebook_id}")
    except Exception as e:
        logger.warning("Failed to load learning objectives for notebook {}: {}", notebook_id, str(e))
        objectives = []

    objectives_text = "\n".join(
        f"- {obj.text}" for obj in objectives
    ) if objectives else "No specific objectives defined yet."

    # 2. Language instruction
    language_names = {
        "fr-FR": "French (Français)",
        "en-US": "English",
        "pt-BR": "Brazilian Portuguese (Português)",
        "zh-CN": "Simplified Chinese (简体中文)",
        "zh-TW": "Traditional Chinese (繁體中文)",
    }
    language_display = language_names.get(language, "English")
    language_instruction = (
        f"\n6. IMPORTANT: You MUST write the entire greeting in {language_display}."
        if language != "en-US" else ""
    )

    # 3. Build prompt (same pattern as generate_re_engagement_greeting)
    prompt = f"""Generate a warm, personalized first greeting for a learner starting a new learning module.

**Learner Context:**
- Role: {learner_profile.get('role', 'learner')}
- AI Familiarity: {learner_profile.get('ai_familiarity', 'intermediate')}
- Job: {learner_profile.get('job_description', 'N/A')}

**Module:** {notebook.name}

**Learning Objectives:**
{objectives_text}

**Guidelines:**
1. Welcome them warmly and reference their role/background
2. Briefly acknowledge their AI familiarity level (adjust tone accordingly)
3. Introduce the first learning objective naturally
4. End with an engaging, open-ended question that connects to their work
5. Keep it concise (3-5 sentences), conversational tone{language_instruction}

Generate the greeting now:"""

    # 4. Call LLM
    try:
        model = await provision_langchain_model(
            prompt, model_id=None, default_type="chat", max_tokens=1024
        )
        response = await model.ainvoke(prompt)
        greeting = extract_text_from_response(response.content).strip()
        logger.info(f"Proactive greeting generated: {len(greeting)} chars")
        return greeting
    except Exception as e:
        logger.error("Failed to generate proactive greeting: {}", str(e))
        # Fallback to simple greeting
        if language == "fr-FR":
            return f"Bonjour ! Bienvenue dans {notebook.name}. Commençons !"
        return f"Hello! Welcome to {notebook.name}. Let's get started!"


async def stream_proactive_greeting(
    notebook_id: str, learner_profile: dict, notebook: Notebook, language: str = "en-US"
) -> AsyncGenerator[str, None]:
    """Stream greeting tokens directly from LLM (not pre-generated then word-split).

    Uses the same prompt as generate_proactive_greeting but streams tokens
    as they arrive from the model, providing a smoother UX.

    Args:
        notebook_id: Notebook/module record ID
        learner_profile: Learner profile dict
        notebook: Notebook instance
        language: UI language code

    Yields:
        Text chunks as they arrive from the LLM
    """
    logger.info(f"Streaming proactive greeting for notebook {notebook_id}")

    # 1. Load learning objectives
    try:
        objectives = await LearningObjective.get_for_notebook(notebook_id)
    except Exception as e:
        logger.warning("Failed to load learning objectives for notebook {}: {}", notebook_id, str(e))
        objectives = []

    objectives_text = "\n".join(
        f"- {obj.text}" for obj in objectives
    ) if objectives else "No specific objectives defined yet."

    # 2. Language instruction
    language_names = {
        "fr-FR": "French (Français)",
        "en-US": "English",
        "pt-BR": "Brazilian Portuguese (Português)",
        "zh-CN": "Simplified Chinese (简体中文)",
        "zh-TW": "Traditional Chinese (繁體中文)",
    }
    language_display = language_names.get(language, "English")
    language_instruction = (
        f"\n6. IMPORTANT: You MUST write the entire greeting in {language_display}."
        if language != "en-US" else ""
    )

    # 3. Build prompt (same as generate_proactive_greeting)
    prompt = f"""Generate a warm, personalized first greeting for a learner starting a new learning module.

**Learner Context:**
- Role: {learner_profile.get('role', 'learner')}
- AI Familiarity: {learner_profile.get('ai_familiarity', 'intermediate')}
- Job: {learner_profile.get('job_description', 'N/A')}

**Module:** {notebook.name}

**Learning Objectives:**
{objectives_text}

**Guidelines:**
1. Welcome them warmly and reference their role/background
2. Briefly acknowledge their AI familiarity level (adjust tone accordingly)
3. Introduce the first learning objective naturally
4. End with an engaging, open-ended question that connects to their work
5. Keep it concise (3-5 sentences), conversational tone{language_instruction}

Generate the greeting now:"""

    # 4. Stream from LLM
    try:
        model = await provision_langchain_model(
            prompt, model_id=None, default_type="chat", max_tokens=1024
        )
        async for chunk in model.astream(prompt):
            text = extract_text_from_response(chunk.content)
            if text:
                yield text
    except Exception as e:
        logger.error("Failed to stream proactive greeting: {}", str(e))
        # Fallback to simple greeting
        if language == "fr-FR":
            yield f"Bonjour ! Bienvenue dans {notebook.name}. Commençons !"
        else:
            yield f"Hello! Welcome to {notebook.name}. Let's get started!"
