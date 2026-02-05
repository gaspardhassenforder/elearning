"""Artifacts API router."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from api.auth import get_current_user, require_admin
from open_notebook.domain.user import User
from api import artifacts_service

router = APIRouter(dependencies=[Depends(get_current_user)])


@router.get("/notebooks/{notebook_id}/artifacts")
async def get_notebook_artifacts(
    notebook_id: str,
    artifact_type: Optional[str] = Query(None, description="Filter by artifact type"),
):
    """
    Get all artifacts for a notebook.
    
    Optionally filter by type: quiz, podcast, note, transformation
    """
    if artifact_type:
        artifacts = await artifacts_service.get_notebook_artifacts_by_type(
            notebook_id, artifact_type
        )
    else:
        artifacts = await artifacts_service.get_notebook_artifacts(notebook_id)

    return [
        {
            "id": a.id,
            "artifact_type": a.artifact_type,
            "artifact_id": a.artifact_id,
            "title": a.title,
            "created": a.created,
        }
        for a in artifacts
    ]


@router.get("/artifacts/{artifact_id}")
async def get_artifact(artifact_id: str):
    """Get an artifact by ID."""
    artifact = await artifacts_service.get_artifact(artifact_id)
    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found")

    return {
        "id": artifact.id,
        "notebook_id": artifact.notebook_id,
        "artifact_type": artifact.artifact_type,
        "artifact_id": artifact.artifact_id,
        "title": artifact.title,
        "created": artifact.created,
    }


@router.delete("/artifacts/{artifact_id}")
async def delete_artifact(artifact_id: str, admin: User = Depends(require_admin)):
    """Delete an artifact and its associated content."""
    success = await artifacts_service.delete_artifact(artifact_id)
    if not success:
        raise HTTPException(
            status_code=404, detail="Artifact not found or could not be deleted"
        )
    return {"status": "deleted", "artifact_id": artifact_id}


@router.get("/artifacts/{artifact_id}/preview")
async def get_artifact_preview(artifact_id: str):
    """
    Get artifact with type-specific preview data (Story 3.2, Task 2).

    Returns formatted preview data based on artifact type:
    - Quiz: questions with answers, question count
    - Podcast: audio URL, transcript, duration
    - Summary: markdown content, word count
    - Transformation: transformed content, word count, transformation name
    """
    preview = await artifacts_service.get_artifact_with_preview(artifact_id)
    if not preview:
        raise HTTPException(status_code=404, detail="Artifact not found")

    if preview.get("error"):
        raise HTTPException(status_code=500, detail=preview["error"])

    return preview


@router.post("/artifacts/{artifact_id}/regenerate")
async def regenerate_artifact(artifact_id: str, admin: User = Depends(require_admin)):
    """
    Regenerate an artifact (Story 3.2, Task 3).

    This endpoint:
    1. Retrieves the existing artifact metadata
    2. Deletes the old artifact and its content
    3. Generates a new artifact with the same parameters
    4. Returns the new artifact ID and status

    For async operations (podcasts), returns command_id for polling.
    """
    result = await artifacts_service.regenerate_artifact(artifact_id)

    if result["status"] == "error":
        status_code = 404 if "not found" in result.get("error", "").lower() else 500
        raise HTTPException(status_code=status_code, detail=result["error"])

    return result
