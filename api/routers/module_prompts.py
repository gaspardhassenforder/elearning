"""Module Prompts API endpoints.

Story 3.4: AI Teacher Prompt Configuration
Admin-only endpoints for managing per-module AI teacher prompts.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from loguru import logger

from api import module_prompt_service
from api.auth import require_admin
from api.models import ModulePromptResponse, ModulePromptUpdate
from open_notebook.domain.user import User

router = APIRouter(dependencies=[Depends(require_admin)])


@router.get("/notebooks/{notebook_id}/prompt", response_model=Optional[ModulePromptResponse])
async def get_prompt(notebook_id: str):
    """Get module prompt for a notebook.

    Returns None if no prompt configured (admin has not customized AI teacher for this module).

    Args:
        notebook_id: Notebook record ID

    Returns:
        ModulePromptResponse if prompt exists, None otherwise

    Raises:
        HTTPException 404: Notebook not found
    """
    logger.info(f"GET /notebooks/{notebook_id}/prompt")

    prompt = await module_prompt_service.get_module_prompt(notebook_id)

    if not prompt:
        return None

    return ModulePromptResponse(
        id=prompt.id,
        notebook_id=prompt.notebook_id,
        system_prompt=prompt.system_prompt,
        updated_by=prompt.updated_by,
        updated_at=getattr(prompt, "updated_at", None),
    )


@router.put("/notebooks/{notebook_id}/prompt", response_model=ModulePromptResponse)
async def update_prompt(
    notebook_id: str,
    data: ModulePromptUpdate,
    admin: User = Depends(require_admin),
):
    """Create or update module prompt for a notebook.

    If system_prompt is None or empty string, clears the prompt (falls back to global-only behavior).

    Args:
        notebook_id: Notebook record ID
        data: ModulePromptUpdate with optional system_prompt
        admin: Authenticated admin user (injected)

    Returns:
        ModulePromptResponse with created/updated prompt

    Raises:
        HTTPException 404: Notebook not found
        HTTPException 500: Save operation failed
    """
    logger.info(f"PUT /notebooks/{notebook_id}/prompt by admin {admin.id}")

    # Get admin user ID for updated_by field
    admin_id = admin.id if hasattr(admin, "id") else str(admin)

    prompt = await module_prompt_service.update_module_prompt(
        notebook_id=notebook_id,
        system_prompt=data.system_prompt,
        updated_by=admin_id,
    )

    return ModulePromptResponse(
        id=prompt.id,
        notebook_id=prompt.notebook_id,
        system_prompt=prompt.system_prompt,
        updated_by=prompt.updated_by,
        updated_at=getattr(prompt, "updated_at", None),
    )
