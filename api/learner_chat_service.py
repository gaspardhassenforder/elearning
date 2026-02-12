"""Learner Chat Service - Business Logic for AI Teacher Conversations.

Handles learner profile loading, prompt assembly, and access validation for chat.

Story: 4.1 - Learner Chat Interface & SSE Streaming
Story: 4.2 - Two-Layer Prompt System & Proactive AI Teacher
"""

from typing import Optional, Tuple

from ai_prompter import Prompter
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

    # 3. Assemble system prompt (global + per-module from Story 3.4)
    try:
        system_prompt = await assemble_system_prompt(
            notebook_id=notebook_id,
            learner_profile=learner_profile,
            objectives_with_status=objectives_with_status,
            context=None,  # Context built by LangGraph chat workflow
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
    """Generate personalized proactive greeting for first visit.

    Uses greeting_template.j2 to create a personalized message that:
    1. References learner's role and AI familiarity
    2. Mentions their job context
    3. Introduces the first learning objective
    4. Asks an opening question to engage them

    Args:
        notebook_id: Notebook/module record ID
        learner_profile: Learner profile dict with role, ai_familiarity, job_description
        notebook: Notebook instance
        language: UI language code (e.g., 'en-US', 'fr-FR') for greeting language

    Returns:
        Personalized greeting string

    Raises:
        Exception: If greeting generation fails
    """
    logger.info(f"Generating proactive greeting for notebook {notebook_id}")

    # 1. Load learning objectives for this notebook
    try:
        objectives = await LearningObjective.get_for_notebook(notebook_id)
        logger.debug(f"Found {len(objectives)} learning objectives for notebook {notebook_id}")
    except Exception as e:
        logger.warning("Failed to load learning objectives for notebook {}: {}", notebook_id, str(e))
        objectives = []

    # 2. Determine first objective to introduce
    first_objective_text = objectives[0].text if objectives else "exploring this module's content"
    logger.debug(f"First objective: {first_objective_text}")

    # 3. Generate opening question based on first objective
    # Use LLM to create contextual opening question
    # Map language codes to display names for LLM instruction
    language_names = {
        "fr-FR": "French (Français)",
        "en-US": "English",
        "pt-BR": "Brazilian Portuguese (Português)",
        "zh-CN": "Simplified Chinese (简体中文)",
        "zh-TW": "Traditional Chinese (繁體中文)",
    }
    language_display = language_names.get(language, "English")
    language_instruction = f"\nIMPORTANT: You MUST respond in {language_display}." if language != "en-US" else ""

    opening_question_prompt = f"""Generate a thought-provoking opening question to engage a learner starting to explore this learning objective:

"{first_objective_text}"

The learner's role is: {learner_profile.get('role', 'Unknown')}
The learner's job: {learner_profile.get('job_description', 'N/A')}

Create a question that:
- Connects to their work context
- Encourages them to think about what they already know
- Sets up exploration of the objective
- Is open-ended (not yes/no)
{language_instruction}
Return ONLY the question, nothing else."""

    try:
        model = await provision_langchain_model(
            opening_question_prompt,
            model_id=None,  # Use default chat model
            default_type="chat",
            max_tokens=150,  # Short response
        )
        opening_question = await model.ainvoke(opening_question_prompt)
        # Extract text from AIMessage (handles structured content blocks)
        if hasattr(opening_question, "content"):
            opening_question = extract_text_from_response(opening_question.content)
        opening_question = str(opening_question).strip()
        logger.debug(f"Generated opening question: {opening_question}")
    except Exception as e:
        logger.warning("Failed to generate opening question, using fallback: {}", str(e))
        opening_question = f"What comes to mind when you think about {first_objective_text.lower()}?"

    # 4. Render greeting template
    try:
        greeting_text = Prompter(prompt_template="greeting_template").render(
            data={
                "learner_profile": learner_profile,
                "module_title": notebook.name,
                "first_objective_text": first_objective_text,
                "opening_question": opening_question,
                "language": language,
                "language_display": language_display,
            }
        )
        logger.info(f"Proactive greeting generated: {len(greeting_text)} chars")
        return greeting_text
    except Exception as e:
        logger.error("Failed to render greeting template: {}", str(e))
        # Fallback to simple greeting
        if language == "fr-FR":
            return f"Bonjour {learner_profile.get('role', 'apprenant')} ! Bienvenue dans {notebook.name}. Commençons !"
        return f"Hello {learner_profile.get('role', 'learner')}! Welcome to {notebook.name}. Let's get started!"
