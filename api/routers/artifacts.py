"""Artifacts API router."""

from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from api import artifacts_service

router = APIRouter()


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
async def delete_artifact(artifact_id: str):
    """Delete an artifact and its associated content."""
    success = await artifacts_service.delete_artifact(artifact_id)
    if not success:
        raise HTTPException(
            status_code=404, detail="Artifact not found or could not be deleted"
        )
    return {"status": "deleted", "artifact_id": artifact_id}
