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

    # Check published status (learners cannot see unpublished modules)
    if not notebook_data.get("published", True):
        logger.warning(
            f"Learner {learner_context.user.id} attempted to access unpublished notebook {notebook_id}"
        )
        raise HTTPException(
            status_code=403, detail="You do not have access to this module"
        )

    # Check locked status (Story 2.3)
    if notebook_data.get("is_locked", False):
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
        # Generic error message - don't leak internal details
        raise HTTPException(
            status_code=500,
            detail="Internal server error. Please try again later."
        )

    return system_prompt, learner_profile
