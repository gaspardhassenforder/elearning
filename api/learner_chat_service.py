"""Learner Chat Service - Business Logic for AI Teacher Conversations.

Handles learner profile loading, prompt assembly, and access validation for chat.

Story: 4.1 - Learner Chat Interface & SSE Streaming
"""

from typing import Optional, Tuple

from fastapi import HTTPException
from loguru import logger

from api.auth import LearnerContext
from open_notebook.domain.notebook import Notebook
from open_notebook.graphs.prompt import assemble_system_prompt


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
    try:
        notebook = await Notebook.get(notebook_id)
    except Exception as e:
        logger.error(f"Error fetching notebook {notebook_id}: {e}")
        raise HTTPException(status_code=404, detail="Notebook not found")

    if not notebook:
        logger.error(f"Notebook {notebook_id} not found")
        raise HTTPException(status_code=404, detail="Notebook not found")

    # Check published status (learners cannot see unpublished modules)
    if not getattr(notebook, "published", True):
        logger.warning(
            f"Learner {learner_context.user.id} attempted to access unpublished notebook {notebook_id}"
        )
        # Consistent 403 - don't leak existence of unpublished modules
        raise HTTPException(
            status_code=403, detail="You do not have access to this module"
        )

    # Check company assignment (from Story 2.3)
    # Query module_assignment table to check if notebook is assigned to learner's company
    from open_notebook.database.repository import repo_query

    assignment_query = await repo_query(
        """
        SELECT * FROM module_assignment
        WHERE company_id = $company_id AND notebook_id = $notebook_id
        LIMIT 1
        """,
        {"company_id": learner_context.company_id, "notebook_id": notebook_id},
    )

    if not assignment_query:
        logger.warning(
            f"Learner {learner_context.user.id} attempted to access unassigned notebook {notebook_id}"
        )
        # Consistent 403 - don't leak existence of other companies' modules
        raise HTTPException(
            status_code=403, detail="You do not have access to this module"
        )

    # Check locked status (Story 2.3)
    assignment = assignment_query[0]
    if assignment.get("is_locked", False):
        logger.warning(
            f"Learner {learner_context.user.id} attempted to access locked notebook {notebook_id}"
        )
        # Consistent 403 - locked modules are inaccessible
        raise HTTPException(
            status_code=403,
            detail="This module is currently locked and not available",
        )

    logger.info(
        f"Learner {learner_context.user.id} validated access to notebook {notebook_id}"
    )
    return notebook


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
    # Story 4.4 will implement objective tracking - for now pass empty list
    objectives_with_status = []

    # TODO Story 4.4: Load from LearnerObjectiveProgress table
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
        raise

    return system_prompt, learner_profile
