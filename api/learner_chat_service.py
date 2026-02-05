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
from open_notebook.domain.notebook import Notebook
from open_notebook.domain.module_assignment import ModuleAssignment
from open_notebook.domain.learning_objective import LearningObjective
from open_notebook.graphs.prompt import assemble_system_prompt
from open_notebook.ai.provision import provision_langchain_model


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

    # Single query with JOIN to check all conditions at once (avoids N+1)
    # This checks: notebook exists, assignment exists, published status, locked status
    result = await repo_query(
        """
        SELECT notebook.*, assignment.is_locked
        FROM notebook
        LEFT JOIN module_assignment AS assignment
        ON assignment.notebook_id = notebook.id
        WHERE notebook.id = $notebook_id
        AND assignment.company_id = $company_id
        LIMIT 1
        """,
        {"notebook_id": notebook_id, "company_id": learner_context.company_id},
    )

    if not result:
        # Either notebook doesn't exist OR not assigned to company
        # Use consistent 403 to avoid leaking existence
        logger.warning(
            f"Learner {learner_context.user.id} attempted to access non-existent or unassigned notebook {notebook_id}"
        )
        raise HTTPException(
            status_code=403, detail="You do not have access to this module"
        )

    notebook_data = result[0]

    # Validate published status (learners cannot see unpublished modules)
    # Use .get() with explicit default for backward compatibility with old data
    published = notebook_data.get("published", True)
    if not published:
        logger.warning(
            f"Learner {learner_context.user.id} attempted to access unpublished notebook {notebook_id}"
        )
        raise HTTPException(
            status_code=403, detail="You do not have access to this module"
        )

    # Validate locked status using typed check (Story 2.3)
    # Extract is_locked from the JOIN result and validate type safety
    is_locked = notebook_data.get("is_locked", False)
    if not isinstance(is_locked, bool):
        logger.warning(f"Invalid is_locked type for notebook {notebook_id}: {type(is_locked)}")
        is_locked = bool(is_locked)  # Coerce to bool

    if is_locked:
        logger.warning(
            f"Learner {learner_context.user.id} attempted to access locked notebook {notebook_id}"
        )
        raise HTTPException(
            status_code=403,
            detail="This module is currently locked and not available",
        )

    # Fetch full Notebook object (already validated via JOIN above)
    # Note: Future optimization (Story 4.8+) could cache this per session
    try:
        notebook = await Notebook.get(notebook_id)
        logger.info(
            f"Learner {learner_context.user.id} validated access to notebook {notebook_id}"
        )
        return notebook
    except Exception as e:
        logger.error(f"Error fetching notebook {notebook_id} after validation: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


async def prepare_chat_context(
    notebook_id: str, learner: LearnerContext
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

    # 2. Load learning objectives with completion status
    # Story 4.2: Load learning objectives for this module
    # Story 4.4 will add LearnerObjectiveProgress tracking for actual completion status
    try:
        objectives = await LearningObjective.list_by_notebook(notebook_id)
        objectives_with_status = [
            {
                "text": obj.text,
                "status": "not_started",  # Story 4.4 will load actual progress
                "order": obj.order,
            }
            for obj in objectives
        ]
        logger.debug(f"Loaded {len(objectives_with_status)} learning objectives")
    except Exception as e:
        logger.warning(f"Failed to load learning objectives for notebook {notebook_id}: {e}")
        objectives_with_status = []

    # TODO Story 4.4: Replace "not_started" with actual learner progress
    # objectives_with_status = await get_learner_objectives_with_status(
    #     notebook_id=notebook_id,
    #     user_id=learner.user.id
    # )

    # 3. Assemble system prompt (global + per-module from Story 3.4)
    try:
        system_prompt = await assemble_system_prompt(
            notebook_id=notebook_id,
            learner_profile=learner_profile,
            objectives_with_status=objectives_with_status,
            context=None,  # Context built by LangGraph chat workflow
        )
        logger.info(
            f"System prompt assembled: {len(system_prompt)} chars for notebook {notebook_id}"
        )
    except Exception as e:
        logger.error(f"Failed to assemble system prompt for notebook {notebook_id}: {e}")
        # Generic error message - don't leak internal details
        raise HTTPException(
            status_code=500,
            detail="Internal server error. Please try again later."
        )

    return system_prompt, learner_profile


async def generate_proactive_greeting(
    notebook_id: str, learner_profile: dict, notebook: Notebook
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

    Returns:
        Personalized greeting string

    Raises:
        Exception: If greeting generation fails
    """
    logger.info(f"Generating proactive greeting for notebook {notebook_id}")

    # 1. Load learning objectives for this notebook
    try:
        objectives = await LearningObjective.list_by_notebook(notebook_id)
        logger.debug(f"Found {len(objectives)} learning objectives for notebook {notebook_id}")
    except Exception as e:
        logger.warning(f"Failed to load learning objectives for notebook {notebook_id}: {e}")
        objectives = []

    # 2. Determine first objective to introduce
    first_objective_text = objectives[0].text if objectives else "exploring this module's content"
    logger.debug(f"First objective: {first_objective_text}")

    # 3. Generate opening question based on first objective
    # Use LLM to create contextual opening question
    opening_question_prompt = f"""Generate a thought-provoking opening question to engage a learner starting to explore this learning objective:

"{first_objective_text}"

The learner's role is: {learner_profile.get('role', 'Unknown')}
The learner's job: {learner_profile.get('job_description', 'N/A')}

Create a question that:
- Connects to their work context
- Encourages them to think about what they already know
- Sets up exploration of the objective
- Is open-ended (not yes/no)

Return ONLY the question, nothing else."""

    try:
        model = await provision_langchain_model(
            opening_question_prompt,
            model_id=None,  # Use default chat model
            context_type="chat",
            max_tokens=150,  # Short response
        )
        opening_question = await model.ainvoke(opening_question_prompt)
        # Extract text from AIMessage
        if hasattr(opening_question, "content"):
            opening_question = opening_question.content
        opening_question = str(opening_question).strip()
        logger.debug(f"Generated opening question: {opening_question}")
    except Exception as e:
        logger.warning(f"Failed to generate opening question, using fallback: {e}")
        opening_question = f"What comes to mind when you think about {first_objective_text.lower()}?"

    # 4. Render greeting template
    try:
        greeting_text = Prompter(prompt_template="greeting_template").render(
            data={
                "learner_profile": learner_profile,
                "module_title": notebook.title,
                "first_objective_text": first_objective_text,
                "opening_question": opening_question,
            }
        )
        logger.info(f"Proactive greeting generated: {len(greeting_text)} chars")
        return greeting_text
    except Exception as e:
        logger.error(f"Failed to render greeting template: {e}")
        # Fallback to simple greeting
        return f"Hello {learner_profile.get('role', 'learner')}! Welcome to {notebook.title}. Let's get started!"
