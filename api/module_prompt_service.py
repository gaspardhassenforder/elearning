"""Module prompt service layer.

Story 3.4: AI Teacher Prompt Configuration
Business logic for managing per-module AI teacher prompts.
"""

from typing import Optional

from fastapi import HTTPException
from loguru import logger

from open_notebook.domain.module_prompt import ModulePrompt
from open_notebook.domain.notebook import Notebook


async def get_module_prompt(notebook_id: str) -> Optional[ModulePrompt]:
    """Get module prompt for a notebook.

    Args:
        notebook_id: Notebook record ID

    Returns:
        ModulePrompt instance if exists, None if no prompt configured

    Raises:
        HTTPException: 404 if notebook not found
    """
    logger.info(f"Getting module prompt for notebook {notebook_id}")

    # Verify notebook exists
    notebook = await Notebook.get(notebook_id)
    if not notebook:
        logger.error(f"Notebook {notebook_id} not found")
        raise HTTPException(status_code=404, detail=f"Notebook {notebook_id} not found")

    # Get prompt (may be None)
    prompt = await ModulePrompt.get_by_notebook(notebook_id)

    if prompt:
        logger.info(f"Found module prompt for notebook {notebook_id}")
    else:
        logger.info(f"No module prompt configured for notebook {notebook_id}")

    return prompt


async def update_module_prompt(
    notebook_id: str,
    system_prompt: Optional[str],
    updated_by: str
) -> ModulePrompt:
    """Create or update module prompt for a notebook.

    Args:
        notebook_id: Notebook record ID
        system_prompt: Optional Jinja2 template (None to clear prompt)
        updated_by: Admin user ID performing the update

    Returns:
        ModulePrompt instance (created or updated)

    Raises:
        HTTPException: 404 if notebook not found, 500 if save fails
    """
    logger.info(f"Updating module prompt for notebook {notebook_id}")

    # Verify notebook exists
    notebook = await Notebook.get(notebook_id)
    if not notebook:
        logger.error(f"Notebook {notebook_id} not found")
        raise HTTPException(status_code=404, detail=f"Notebook {notebook_id} not found")

    try:
        # Create or update prompt
        prompt = await ModulePrompt.create_or_update(
            notebook_id=notebook_id,
            system_prompt=system_prompt,
            updated_by=updated_by
        )

        action = "created" if not prompt.id else "updated"
        logger.info(f"Module prompt {action} for notebook {notebook_id}")

        return prompt

    except Exception as e:
        logger.error(f"Failed to update module prompt for notebook {notebook_id}: {e}")
        logger.exception(e)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update module prompt: {str(e)}"
        )
