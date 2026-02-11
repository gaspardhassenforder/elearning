"""Artifacts API router."""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from loguru import logger

from api.auth import get_current_user, get_current_learner, LearnerContext, require_admin
from open_notebook.domain.user import User
from api import artifacts_service
from api.models import ArtifactListResponse
from open_notebook.database.repository import repo_query, ensure_record_id

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


# ==============================================================================
# Story 5.2: Learner-Scoped Artifact Endpoints
# ==============================================================================


async def validate_learner_access_to_notebook(
    notebook_id: str, learner_context: LearnerContext
) -> bool:
    """Validate learner has access to a notebook via their company's module assignment.

    Story 5.2: Company-scoped access control for artifacts.

    Validates:
    1. Notebook is assigned to learner's company
    2. Notebook is published
    3. Assignment is not locked

    Args:
        notebook_id: Notebook record ID
        learner_context: Authenticated learner context with company_id

    Returns:
        True if access is granted

    Raises:
        HTTPException 403: Access denied (not assigned, locked, or unpublished)
    """
    # Check assignment exists, is unlocked, and notebook is published
    result = await repo_query(
        """
        SELECT VALUE true FROM module_assignment
        WHERE notebook_id = $notebook_id
          AND company_id = $company_id
          AND is_locked = false
        LIMIT 1
        """,
        {"notebook_id": ensure_record_id(notebook_id), "company_id": ensure_record_id(learner_context.company_id)},
    )

    if not result:
        logger.warning(
            f"Learner {learner_context.user.id} attempted to access artifacts for unauthorized notebook {notebook_id}"
        )
        raise HTTPException(
            status_code=403, detail="You do not have access to this module"
        )

    # Verify notebook is published
    notebook_result = await repo_query(
        "SELECT VALUE published FROM notebook WHERE id = $notebook_id LIMIT 1",
        {"notebook_id": ensure_record_id(notebook_id)},
    )
    if not notebook_result or notebook_result[0] != True:
        raise HTTPException(
            status_code=403, detail="You do not have access to this module"
        )

    return True


@router.get("/learner/notebooks/{notebook_id}/artifacts", response_model=List[ArtifactListResponse])
async def get_learner_notebook_artifacts(
    notebook_id: str,
    learner: LearnerContext = Depends(get_current_learner),
) -> List[ArtifactListResponse]:
    """Get artifacts for a notebook assigned to learner's company.

    Story 5.2: Artifacts Browsing in Side Panel.

    Returns a list of artifacts (quizzes, podcasts, summaries, transformations)
    for a notebook that is assigned to the learner's company.

    Company scoping: Validates notebook is assigned to learner's company,
    is published, and is not locked.

    Args:
        notebook_id: Notebook record ID (e.g., "notebook:abc123")
        learner: Authenticated learner context (injected via dependency)

    Returns:
        List of ArtifactListResponse with artifact metadata

    Raises:
        HTTPException 403: Notebook not accessible (not assigned, locked, unpublished)
    """
    try:
        # Validate learner access to this notebook via company assignment
        await validate_learner_access_to_notebook(notebook_id, learner)

        # Get artifacts for the notebook
        artifacts = await artifacts_service.get_notebook_artifacts(notebook_id)

        logger.info(
            f"Learner {learner.user.id} fetched {len(artifacts)} artifacts for notebook {notebook_id}"
        )

        return [
            ArtifactListResponse(
                id=a.id or "",
                artifact_type=a.artifact_type,
                title=a.title or "Untitled",
                created=str(a.created),
            )
            for a in artifacts
        ]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching artifacts for notebook {notebook_id}: {str(e)}")
        raise HTTPException(
            status_code=500, detail="Error fetching artifacts"
        )


async def validate_learner_access_to_artifact(
    artifact_id: str, learner_context: LearnerContext
) -> None:
    """Validate learner has access to an artifact via their company's module assignment.

    Story 5.2: Company-scoped access control for artifact preview.

    Validates:
    1. Artifact exists
    2. Artifact's notebook is assigned to learner's company
    3. Notebook is published
    4. Assignment is not locked

    Args:
        artifact_id: Artifact record ID
        learner_context: Authenticated learner context with company_id

    Raises:
        HTTPException 403: Access denied (not assigned, locked, or unpublished)
    """
    # Step 1: Get the artifact and its notebook_id
    artifact_result = await repo_query(
        "SELECT id, notebook_id FROM artifact WHERE id = $artifact_id LIMIT 1",
        {"artifact_id": ensure_record_id(artifact_id)},
    )

    if not artifact_result:
        raise HTTPException(
            status_code=403, detail="You do not have access to this artifact"
        )

    artifact_notebook_id = artifact_result[0].get("notebook_id")

    # Step 2: Check assignment + published + unlocked
    access_result = await repo_query(
        """
        SELECT VALUE true FROM module_assignment
        WHERE notebook_id = $notebook_id
          AND company_id = $company_id
          AND is_locked = false
        LIMIT 1
        """,
        {"notebook_id": ensure_record_id(artifact_notebook_id), "company_id": ensure_record_id(learner_context.company_id)},
    )

    if not access_result:
        logger.warning(
            f"Learner {learner_context.user.id} attempted to access unauthorized artifact {artifact_id}"
        )
        raise HTTPException(
            status_code=403, detail="You do not have access to this artifact"
        )

    # Verify notebook is published
    pub_result = await repo_query(
        "SELECT VALUE published FROM notebook WHERE id = $notebook_id LIMIT 1",
        {"notebook_id": ensure_record_id(artifact_notebook_id)},
    )
    if not pub_result or pub_result[0] != True:
        raise HTTPException(
            status_code=403, detail="You do not have access to this artifact"
        )


@router.get("/learner/artifacts/{artifact_id}/preview")
async def get_learner_artifact_preview(
    artifact_id: str,
    learner: LearnerContext = Depends(get_current_learner),
):
    """Get artifact preview with company scoping validation.

    Story 5.2: Artifacts Browsing in Side Panel.

    Returns type-specific preview data for an artifact:
    - Quiz: questions with answers, question count
    - Podcast: audio URL, transcript, duration
    - Summary: content, word count
    - Transformation: content, word count, transformation name

    Company scoping: Validates artifact belongs to a notebook assigned
    to the learner's company, is published, and is not locked.

    Args:
        artifact_id: Artifact record ID (e.g., "artifact:abc123")
        learner: Authenticated learner context (injected via dependency)

    Returns:
        Type-specific preview data

    Raises:
        HTTPException 403: Artifact not accessible (not assigned, locked, unpublished)
        HTTPException 404: Artifact not found (after access validation)
    """
    try:
        # Validate learner access to this artifact via company assignment
        await validate_learner_access_to_artifact(artifact_id, learner)

        # Get artifact preview (reuse existing service method)
        preview = await artifacts_service.get_artifact_with_preview(artifact_id)
        if not preview:
            raise HTTPException(status_code=404, detail="Artifact not found")

        if preview.get("error"):
            raise HTTPException(status_code=500, detail=preview["error"])

        logger.info(
            f"Learner {learner.user.id} fetched preview for artifact {artifact_id}"
        )

        return preview

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching preview for artifact {artifact_id}: {str(e)}")
        raise HTTPException(
            status_code=500, detail="Error fetching artifact preview"
        )
