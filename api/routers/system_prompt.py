"""System Prompt API endpoints.

Admin-only endpoints for viewing and editing the global AI teacher system prompt.
"""

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from loguru import logger

from api.auth import require_admin
from api.models import SystemPromptResponse, SystemPromptUpdate
from open_notebook.domain.user import User

PROMPT_FILE = Path("prompts/global_teacher_prompt.j2")

router = APIRouter(dependencies=[Depends(require_admin)])


@router.get("/system-prompt", response_model=SystemPromptResponse)
async def get_system_prompt():
    """Read the global AI teacher system prompt file.

    Returns:
        SystemPromptResponse with the file content

    Raises:
        HTTPException 404: Prompt file not found
        HTTPException 500: Failed to read file
    """
    logger.info("GET /system-prompt")

    if not PROMPT_FILE.exists():
        raise HTTPException(status_code=404, detail="System prompt file not found")

    try:
        content = PROMPT_FILE.read_text(encoding="utf-8")
    except Exception as e:
        logger.error(f"Failed to read system prompt file: {e}")
        raise HTTPException(status_code=500, detail="Failed to read system prompt file")

    return SystemPromptResponse(content=content)


@router.put("/system-prompt", response_model=SystemPromptResponse)
async def update_system_prompt(
    data: SystemPromptUpdate,
    admin: User = Depends(require_admin),
):
    """Overwrite the global AI teacher system prompt file.

    Args:
        data: SystemPromptUpdate with new content
        admin: Authenticated admin user (injected)

    Returns:
        SystemPromptResponse with the saved content

    Raises:
        HTTPException 500: Failed to write file
    """
    logger.info(f"PUT /system-prompt by admin {admin.id}")

    try:
        PROMPT_FILE.write_text(data.content, encoding="utf-8")
    except Exception as e:
        logger.error(f"Failed to write system prompt file: {e}")
        raise HTTPException(status_code=500, detail="Failed to save system prompt file")

    return SystemPromptResponse(content=data.content)
