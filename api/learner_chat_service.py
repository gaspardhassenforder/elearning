"""Learner Chat Service - Business Logic for AI Teacher Conversations.

Handles learner profile loading, prompt assembly, and access validation for chat.

Story: 4.1 - Learner Chat Interface & SSE Streaming
Story: 4.2 - Two-Layer Prompt System & Proactive AI Teacher
"""

from typing import Optional, Tuple

from fastapi import HTTPException
from loguru import logger

from api.auth import LearnerContext
from open_notebook.database.repository import ensure_record_id
from open_notebook.domain.notebook import Notebook
from open_notebook.domain.module_assignment import ModuleAssignment
from open_notebook.domain.learning_objective import LearningObjective
from open_notebook.domain.learner_objective_progress import LearnerObjectiveProgress
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
                    "status": "not_started",
                    "completed_at": None,
                    "evidence": None,
                }
                for obj in objectives
            ]
        except Exception as e2:
            logger.error(f"Fallback objectives load also failed: {e2}")
            return []


async def build_source_context_for_learner(notebook_id: str) -> Optional[str]:
    """Build source context string for the learner system prompt.

    Loads sources for the notebook and formats their insights into a context
    string that populates the {{ context }} variable in the system prompt template.

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
) -> Tuple[str, dict]:
    """Prepare context for learner chat.

    Assembles:
    1. Learner profile (role, AI familiarity, job description)
    2. Learning objectives with completion status (Story 4.4 - empty for now)
    3. System prompt (global + per-module via Story 3.4 assemble_system_prompt)

    Args:
        notebook_id: Notebook/module record ID
        learner: Authenticated learner context

    Returns:
        Tuple of (system_prompt, learner_profile_dict)

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

    # 3. Build source context for grounded AI responses
    try:
        source_context = await build_source_context_for_learner(notebook_id)
    except Exception as e:
        logger.warning("Failed to build source context for notebook {}: {}", notebook_id, str(e))
        source_context = None

    # 4. Assemble system prompt (global + per-module from Story 3.4)
    try:
        system_prompt = await assemble_system_prompt(
            notebook_id=notebook_id,
            learner_profile=learner_profile,
            objectives_with_status=objectives_with_status,
            context=source_context,
            language=language,
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

    return system_prompt, learner_profile


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
