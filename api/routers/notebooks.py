from typing import List, Optional
from pathlib import Path
from pydantic import BaseModel, Field

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from loguru import logger

from api.auth import get_current_user, require_admin
from open_notebook.domain.user import User

from api.models import (
    NotebookCreate,
    NotebookResponse,
    NotebookUpdate,
    DocumentUploadResponse,
    DocumentStatusResponse,
    BatchGenerationRequest,
    BatchGenerationResponse,
    ArtifactGenerationResult,
)
from open_notebook.database.repository import ensure_record_id, repo_query
from open_notebook.domain.notebook import Notebook, Source, Note, Asset
from open_notebook.domain.transformation import Transformation
from open_notebook.domain.artifact import Artifact
from open_notebook.domain.learning_objective import LearningObjective
from open_notebook.domain.module_prompt import ModulePrompt
from open_notebook.exceptions import InvalidInputError
from open_notebook.graphs.transformation import graph as transformation_graph

router = APIRouter(dependencies=[Depends(get_current_user)])


@router.get("/notebooks", response_model=List[NotebookResponse])
async def get_notebooks(
    archived: Optional[bool] = Query(None, description="Filter by archived status"),
    order_by: str = Query("updated desc", description="Order by field and direction"),
):
    """Get all notebooks with optional filtering and ordering."""
    try:
        # Build the query with counts
        query = f"""
            SELECT *,
            count(<-reference.in) as source_count,
            count(<-artifact.in) as note_count
            FROM notebook
            ORDER BY {order_by}
        """

        result = await repo_query(query)

        # Filter by archived status if specified
        if archived is not None:
            result = [nb for nb in result if nb.get("archived") == archived]

        # Get objectives counts for all notebooks
        objectives_counts = {}
        for nb in result:
            nb_id = str(nb.get("id", ""))
            try:
                count = await LearningObjective.count_for_notebook(nb_id)
                objectives_counts[nb_id] = count
            except Exception as e:
                logger.warning("Failed to get objectives count for {}: {}", nb_id, str(e))
                objectives_counts[nb_id] = 0

        return [
            NotebookResponse(
                id=str(nb.get("id", "")),
                name=nb.get("name", ""),
                description=nb.get("description", ""),
                archived=nb.get("archived", False),
                published=nb.get("published", False),
                created=str(nb.get("created", "")),
                updated=str(nb.get("updated", "")),
                source_count=nb.get("source_count", 0),
                note_count=nb.get("note_count", 0),
                objectives_count=objectives_counts.get(str(nb.get("id", "")), 0),
            )
            for nb in result
        ]
    except Exception as e:
        logger.error("Error fetching notebooks: {}", str(e))
        raise HTTPException(
            status_code=500, detail=f"Error fetching notebooks: {str(e)}"
        )


@router.post("/notebooks", response_model=NotebookResponse)
async def create_notebook(notebook: NotebookCreate, admin: User = Depends(require_admin)):
    """Create a new notebook."""
    try:
        new_notebook = Notebook(
            name=notebook.name,
            description=notebook.description,
        )
        await new_notebook.save()

        return NotebookResponse(
            id=new_notebook.id or "",
            name=new_notebook.name,
            description=new_notebook.description,
            archived=new_notebook.archived or False,
            published=new_notebook.published,  # Default: False (unpublished)
            created=str(new_notebook.created),
            updated=str(new_notebook.updated),
            source_count=0,  # New notebook has no sources
            note_count=0,  # New notebook has no notes
            objectives_count=0,  # New notebook has no objectives
        )
    except InvalidInputError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Error creating notebook: {}", str(e))
        raise HTTPException(
            status_code=500, detail=f"Error creating notebook: {str(e)}"
        )


@router.get("/notebooks/{notebook_id}", response_model=NotebookResponse)
async def get_notebook(notebook_id: str):
    """Get a specific notebook by ID."""
    try:
        # Query with counts for single notebook
        query = """
            SELECT *,
            count(<-reference.in) as source_count,
            count(<-artifact.in) as note_count
            FROM $notebook_id
        """
        result = await repo_query(query, {"notebook_id": ensure_record_id(notebook_id)})

        if not result:
            raise HTTPException(status_code=404, detail="Notebook not found")

        nb = result[0]
        nb_id = str(nb.get("id", ""))

        # Get objectives count for this notebook
        objectives_count = 0
        try:
            objectives_count = await LearningObjective.count_for_notebook(nb_id)
        except Exception as e:
            logger.warning("Failed to get objectives count for {}: {}", nb_id, str(e))

        return NotebookResponse(
            id=nb_id,
            name=nb.get("name", ""),
            description=nb.get("description", ""),
            archived=nb.get("archived", False),
            published=nb.get("published", False),
            created=str(nb.get("created", "")),
            updated=str(nb.get("updated", "")),
            source_count=nb.get("source_count", 0),
            note_count=nb.get("note_count", 0),
            objectives_count=objectives_count,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error fetching notebook {}: {}", notebook_id, str(e))
        raise HTTPException(
            status_code=500, detail=f"Error fetching notebook: {str(e)}"
        )


@router.put("/notebooks/{notebook_id}", response_model=NotebookResponse)
async def update_notebook(notebook_id: str, notebook_update: NotebookUpdate, admin: User = Depends(require_admin)):
    """Update a notebook."""
    try:
        notebook = await Notebook.get(notebook_id)
        if not notebook:
            raise HTTPException(status_code=404, detail="Notebook not found")

        # Update only provided fields
        if notebook_update.name is not None:
            notebook.name = notebook_update.name
        if notebook_update.description is not None:
            notebook.description = notebook_update.description
        if notebook_update.archived is not None:
            notebook.archived = notebook_update.archived

        await notebook.save()

        # Query with counts after update
        query = """
            SELECT *,
            count(<-reference.in) as source_count,
            count(<-artifact.in) as note_count
            FROM $notebook_id
        """
        result = await repo_query(query, {"notebook_id": ensure_record_id(notebook_id)})

        if result:
            nb = result[0]
            nb_id = str(nb.get("id", ""))

            # Get objectives count for this notebook
            objectives_count = 0
            try:
                objectives_count = await LearningObjective.count_for_notebook(nb_id)
            except Exception as e:
                logger.warning("Failed to get objectives count for {}: {}", nb_id, str(e))

            return NotebookResponse(
                id=nb_id,
                name=nb.get("name", ""),
                description=nb.get("description", ""),
                archived=nb.get("archived", False),
                published=nb.get("published", False),
                created=str(nb.get("created", "")),
                updated=str(nb.get("updated", "")),
                source_count=nb.get("source_count", 0),
                note_count=nb.get("note_count", 0),
                objectives_count=objectives_count,
            )

        # Fallback if query fails
        return NotebookResponse(
            id=notebook.id or "",
            name=notebook.name,
            description=notebook.description,
            archived=notebook.archived or False,
            published=notebook.published,
            created=str(notebook.created),
            updated=str(notebook.updated),
            source_count=0,
            note_count=0,
            objectives_count=0,
        )
    except HTTPException:
        raise
    except InvalidInputError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Error updating notebook {}: {}", notebook_id, str(e))
        raise HTTPException(
            status_code=500, detail=f"Error updating notebook: {str(e)}"
        )


@router.post("/notebooks/{notebook_id}/sources/{source_id}")
async def add_source_to_notebook(notebook_id: str, source_id: str, admin: User = Depends(require_admin)):
    """Add an existing source to a notebook (create the reference)."""
    try:
        # Check if notebook exists
        notebook = await Notebook.get(notebook_id)
        if not notebook:
            raise HTTPException(status_code=404, detail="Notebook not found")

        # Check if source exists
        source = await Source.get(source_id)
        if not source:
            raise HTTPException(status_code=404, detail="Source not found")

        # Check if reference already exists (idempotency)
        existing_ref = await repo_query(
            "SELECT * FROM reference WHERE out = $source_id AND in = $notebook_id",
            {
                "notebook_id": ensure_record_id(notebook_id),
                "source_id": ensure_record_id(source_id),
            },
        )

        # If reference doesn't exist, create it
        if not existing_ref:
            await repo_query(
                "RELATE $source_id->reference->$notebook_id",
                {
                    "notebook_id": ensure_record_id(notebook_id),
                    "source_id": ensure_record_id(source_id),
                },
            )

        return {"message": "Source linked to notebook successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error linking source {} to notebook {}: {}", source_id, notebook_id, str(e)
        )
        raise HTTPException(
            status_code=500, detail=f"Error linking source to notebook: {str(e)}"
        )


@router.delete("/notebooks/{notebook_id}/sources/{source_id}")
async def remove_source_from_notebook(notebook_id: str, source_id: str, admin: User = Depends(require_admin)):
    """Remove a source from a notebook (delete the reference)."""
    try:
        # Check if notebook exists
        notebook = await Notebook.get(notebook_id)
        if not notebook:
            raise HTTPException(status_code=404, detail="Notebook not found")

        # Delete the reference record linking source to notebook
        await repo_query(
            "DELETE FROM reference WHERE out = $notebook_id AND in = $source_id",
            {
                "notebook_id": ensure_record_id(notebook_id),
                "source_id": ensure_record_id(source_id),
            },
        )

        return {"message": "Source removed from notebook successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error removing source {} from notebook {}: {}", source_id, notebook_id, str(e)
        )
        raise HTTPException(
            status_code=500, detail=f"Error removing source from notebook: {str(e)}"
        )


@router.post("/notebooks/{notebook_id}/documents", response_model=DocumentUploadResponse)
async def upload_document_to_notebook(
    notebook_id: str,
    file: UploadFile = File(...),
    admin: User = Depends(require_admin)
):
    """
    Upload a document to a notebook (Story 3.1, Task 2).

    This endpoint:
    1. Saves the uploaded file with a unique name
    2. Creates a Source record
    3. Submits an async processing job (content extraction + embedding)
    4. Returns immediately with processing status and command_id for polling
    """
    try:
        # Verify notebook exists
        notebook = await Notebook.get(notebook_id)
        if not notebook:
            logger.error(f"Notebook not found: {notebook_id}")
            raise HTTPException(status_code=404, detail="Notebook not found")

        # Import file upload utility from sources router
        from api.routers.sources import save_uploaded_file

        # Save uploaded file
        file_path = await save_uploaded_file(file)
        logger.info(f"Saved uploaded file to: {file_path}")

        # Extract title from filename (without extension)
        title = Path(file.filename or "untitled").stem

        # Create Source record
        source = Source(
            title=title,
            asset=Asset(
                url=f"file://{file_path}",
                file_type=file.content_type or "application/octet-stream",
                file_path=file_path,
            )
        )
        await source.save()
        logger.info(f"Created source: {source.id}")

        # Link source to notebook
        await source.add_to_notebook(notebook_id)
        logger.info(f"Linked source {source.id} to notebook {notebook_id}")

        # Submit async processing job (content extraction + embedding)
        # Import command modules to ensure they're registered
        import commands.source_commands  # noqa: F401
        from api.command_service import CommandService
        from commands.source_commands import SourceProcessingInput

        # Prepare content state for processing
        content_state: dict = {
            "source_id": source.id or "",
            "notebook_ids": [notebook_id],
            "file_path": file_path,
            "type": "file",
            "title": title,
            "transformations": [],
            "embed": True,
        }

        command_input = SourceProcessingInput(
            source_id=source.id or "",
            content_state=content_state,
            notebook_ids=[notebook_id],
            transformations=[],
            embed=True,
        )

        command_id = await CommandService.submit_command_job(
            "open_notebook",  # app name
            "process_source",  # command name
            command_input.model_dump(),
        )

        logger.info(f"Submitted async processing command: {command_id} for source {source.id}")

        # Update source with command reference
        source.command = ensure_record_id(command_id)
        await source.save()

        # Return response immediately with command_id for polling
        return DocumentUploadResponse(
            id=source.id or "",
            title=source.title or title,
            status="processing",
            command_id=command_id
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error uploading document to notebook {}: {}", notebook_id, str(e))
        logger.exception(e)
        raise HTTPException(
            status_code=500, detail=f"Error uploading document: {str(e)}"
        )


@router.get("/notebooks/{notebook_id}/documents", response_model=List[DocumentStatusResponse])
async def get_notebook_documents(
    notebook_id: str,
    admin: User = Depends(require_admin)
):
    """
    Get list of documents (sources) in a notebook with processing status (Story 3.1, Task 3).

    Returns all sources with their processing status for the UI to poll and update.
    """
    try:
        # Verify notebook exists
        notebook = await Notebook.get(notebook_id)
        if not notebook:
            logger.error(f"Notebook not found: {notebook_id}")
            raise HTTPException(status_code=404, detail="Notebook not found")

        # Get all sources for this notebook
        sources = await notebook.get_sources()

        # Build response list with status for each source
        documents = []
        for source in sources:
            # Get processing status
            try:
                status = await source.get_status()
            except Exception as e:
                logger.warning("Failed to get status for source {}: {}", source.id, str(e))
                status = "unknown"

            # Extract error message if available (from command result)
            error_message = None
            if status == "error" and source.command:
                try:
                    from api.command_service import CommandService
                    command_status = await CommandService.get_command_status(str(source.command))
                    if command_status and command_status.get("result"):
                        result = command_status["result"]
                        if isinstance(result, dict) and "error" in result:
                            error_message = str(result["error"])
                except Exception as e:
                    logger.warning("Failed to extract error message: {}", str(e))

            documents.append(
                DocumentStatusResponse(
                    id=source.id or "",
                    title=source.title or "Untitled",
                    status=status or "unknown",
                    command_id=str(source.command) if source.command else None,
                    error_message=error_message,
                    created=str(source.created) if source.created else None,
                    updated=str(source.updated) if source.updated else None,
                )
            )

        return documents

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error fetching documents for notebook {}: {}", notebook_id, str(e))
        logger.exception(e)
        raise HTTPException(
            status_code=500, detail=f"Error fetching documents: {str(e)}"
        )


class NotebookTransformationRequest(BaseModel):
    """Request body for notebook transformation generation."""
    transformation_id: str = Field(..., description="ID of the transformation to apply")
    model_id: Optional[str] = Field(None, description="Optional model ID to use")


@router.post("/notebooks/{notebook_id}/transformations/generate")
async def generate_transformation(notebook_id: str, request: NotebookTransformationRequest, admin: User = Depends(require_admin)):
    """
    Generate a transformation artifact for a notebook.
    
    This endpoint:
    1. Gathers all sources from the notebook (with full text)
    2. Combines their text content
    3. Executes the transformation
    4. Creates a Note artifact with the result
    """
    try:
        # Validate notebook exists
        notebook = await Notebook.get(notebook_id)
        if not notebook:
            raise HTTPException(status_code=404, detail="Notebook not found")

        # Validate transformation exists
        transformation = await Transformation.get(request.transformation_id)
        if not transformation:
            raise HTTPException(status_code=404, detail="Transformation not found")

        # Fetch sources WITH full_text (notebook.get_sources() omits it)
        srcs = await repo_query(
            """
            select in as source from reference where out=$id
            fetch source
            """,
            {"id": ensure_record_id(notebook_id)},
        )
        sources = [Source(**src["source"]) for src in srcs] if srcs else []

        if not sources:
            raise HTTPException(
                status_code=400,
                detail="No sources found in notebook. Please add sources before generating a transformation."
            )

        # Combine source content
        content_parts = []
        for source in sources:
            if source.full_text:
                text = source.full_text[:10000] if len(source.full_text) > 10000 else source.full_text
                title = source.title or "Untitled Source"
                content_parts.append(f"## {title}\n\n{text}")

        if not content_parts:
            raise HTTPException(
                status_code=400,
                detail="No text content found in sources."
            )

        combined_content = "\n\n---\n\n".join(content_parts)
        
        # Limit total content
        max_content_length = 50000
        if len(combined_content) > max_content_length:
            combined_content = combined_content[:max_content_length] + "\n\n[Content truncated...]"

        logger.info(f"Executing transformation {request.transformation_id} on notebook {notebook_id}")

        # Get default transformation model if not specified
        model_id = request.model_id
        if not model_id:
            from open_notebook.ai.models import DefaultModels
            defaults = await DefaultModels.get_instance()
            if defaults and defaults.default_transformation_model:
                model_id = defaults.default_transformation_model
            elif defaults and defaults.default_chat_model:
                model_id = defaults.default_chat_model

        # Execute transformation
        result = await transformation_graph.ainvoke(
            dict(
                input_text=combined_content,
                transformation=transformation,
            ),
            config=dict(configurable={"model_id": model_id}),
        )

        transformed_content = result.get("output", "")
        if not transformed_content:
            raise HTTPException(status_code=500, detail="Transformation returned empty result")

        # Create note with transformation result
        note_title = f"{transformation.title or transformation.name} - {notebook.name}"
        note = Note(
            title=note_title,
            content=transformed_content,
            note_type="ai",
        )
        await note.save()

        # Create artifact tracker
        await Artifact.create_for_artifact(
            notebook_id=notebook_id,
            artifact_type="transformation",
            artifact_id=note.id,
            title=note_title,
        )

        logger.info(f"Transformation artifact created: note {note.id}")

        return {
            "note_id": note.id,
            "artifact_id": note.id,
            "title": note_title,
            "content": transformed_content,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error generating transformation: {}", str(e))
        logger.exception(e)
        raise HTTPException(status_code=500, detail=f"Failed to generate transformation: {str(e)}")


@router.delete("/notebooks/{notebook_id}")
async def delete_notebook(notebook_id: str, admin: User = Depends(require_admin)):
    """Delete a notebook."""
    try:
        notebook = await Notebook.get(notebook_id)
        if not notebook:
            raise HTTPException(status_code=404, detail="Notebook not found")

        await notebook.delete()

        return {"message": "Notebook deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error deleting notebook {}: {}", notebook_id, str(e))
        raise HTTPException(
            status_code=500, detail=f"Error deleting notebook: {str(e)}"
        )


@router.post("/notebooks/{notebook_id}/generate-artifacts", response_model=BatchGenerationResponse)
async def generate_artifacts(
    notebook_id: str,
    request: Optional[BatchGenerationRequest] = None,
    admin: User = Depends(require_admin)
):
    """
    Generate all artifacts for a notebook (Story 3.2, Task 1).

    This endpoint orchestrates parallel artifact generation:
    - Quiz: sync workflow (30-60s)
    - Summary: sync transformation (10-30s)
    - Podcast: async job (2-5min, fire-and-forget)

    Uses asyncio.gather with error isolation so one failure doesn't break others.

    Returns:
        Batch generation status with artifact IDs and command IDs for async jobs
    """
    try:
        # Verify notebook exists
        notebook = await Notebook.get(notebook_id)
        if not notebook:
            logger.error(f"Notebook not found: {notebook_id}")
            raise HTTPException(status_code=404, detail="Notebook not found")

        # Import artifact generation service
        from api import artifact_generation_service

        # Execute batch generation
        logger.info(f"Starting batch artifact generation for notebook {notebook_id}")
        status = await artifact_generation_service.generate_all_artifacts(notebook_id)

        # Convert to response model
        response = BatchGenerationResponse(
            notebook_id=notebook_id,
            quiz=ArtifactGenerationResult(
                status=status.quiz_status,  # type: ignore
                id=status.quiz_id,
                error=status.quiz_error,
            ),
            summary=ArtifactGenerationResult(
                status=status.summary_status,  # type: ignore
                id=status.summary_id,
                error=status.summary_error,
            ),
            transformations={
                "status": status.transformations_status,
                "ids": status.transformation_ids,
                "errors": status.transformation_errors,
            },
            podcast={
                "status": status.podcast_status,
                "command_id": status.podcast_command_id,
                "artifact_ids": status.podcast_artifact_ids,
                "error": status.podcast_error,
            },
        )

        logger.info(f"Batch artifact generation completed for notebook {notebook_id}")
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error generating artifacts for notebook {}: {}", notebook_id, str(e))
        logger.exception(e)
        raise HTTPException(
            status_code=500, detail=f"Error generating artifacts: {str(e)}"
        )


@router.post("/notebooks/{notebook_id}/publish", response_model=NotebookResponse)
async def publish_notebook(
    notebook_id: str,
    admin: User = Depends(require_admin)
):
    """
    Publish a module after validation (Story 3.5, Task 2).

    Validates:
        - At least 1 document (source)
        - At least 1 learning objective

    Returns:
        Updated notebook with published=True

    Raises:
        400: Validation failed
        404: Notebook not found
    """
    try:
        # 1. Validate module is ready for publishing
        # Get notebook with source count
        query = """
            SELECT *,
            count(<-reference.in) as source_count,
            count(<-artifact.in) as note_count
            FROM $notebook_id
        """
        result = await repo_query(query, {"notebook_id": ensure_record_id(notebook_id)})
        notebook_data = result[0] if result else None

        if not notebook_data:
            logger.error(f"Notebook {notebook_id} not found for publishing")
            raise HTTPException(status_code=404, detail="Notebook not found")

        source_count = notebook_data.get("source_count", 0)
        note_count = notebook_data.get("note_count", 0)

        # Get objective count
        objective_count = await LearningObjective.count_for_notebook(notebook_id)

        # Check for module prompt (optional, display only)
        module_prompt = await ModulePrompt.get_by_notebook(notebook_id)
        has_prompt = module_prompt is not None and bool(module_prompt.system_prompt)

        # Validate requirements
        errors = []
        if source_count < 1:
            errors.append({
                "field": "sources",
                "message": "At least 1 document is required to publish"
            })

        if objective_count < 1:
            errors.append({
                "field": "objectives",
                "message": "At least 1 learning objective is required to publish"
            })

        if errors:
            logger.error(f"Publish validation failed for notebook {notebook_id}: {errors}")
            raise HTTPException(
                status_code=400,
                detail={
                    "message": "Module cannot be published - validation failed",
                    "errors": errors
                }
            )

        # 2. Get notebook and update published status
        notebook = await Notebook.get(notebook_id)
        if not notebook:
            logger.error(f"Notebook {notebook_id} not found for publishing")
            raise HTTPException(status_code=404, detail="Notebook not found")

        notebook.published = True
        await notebook.save()

        logger.info(f"Notebook {notebook_id} published by admin {admin.id}")

        # 3. Return updated notebook with counts
        return NotebookResponse(
            id=notebook.id or "",
            name=notebook.name,
            description=notebook.description,
            archived=notebook.archived or False,
            published=True,
            created=str(notebook.created),
            updated=str(notebook.updated),
            source_count=source_count,
            note_count=note_count,
            objectives_count=objective_count,
            has_prompt=has_prompt,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error publishing notebook {}: {}", notebook_id, str(e))
        logger.exception(e)
        raise HTTPException(
            status_code=500, detail=f"Error publishing notebook: {str(e)}"
        )


@router.post("/notebooks/{notebook_id}/unpublish", response_model=NotebookResponse)
async def unpublish_notebook(
    notebook_id: str,
    admin: User = Depends(require_admin)
):
    """
    Unpublish a module to allow editing (Story 3.6, Task 1).

    Sets published=false, which:
    - Hides module from learners (existing behavior from Story 2.3)
    - Allows admin to edit content
    - Preserves all existing data (sources, artifacts, objectives)

    Returns:
        Updated notebook with published=False

    Raises:
        404: Notebook not found
        400: Notebook not published (can't unpublish draft)
    """
    try:
        notebook = await Notebook.get(notebook_id)
        if not notebook:
            logger.error(f"Notebook {notebook_id} not found for unpublishing")
            raise HTTPException(status_code=404, detail="Notebook not found")

        if not notebook.published:
            logger.error(f"Notebook {notebook_id} is not published - cannot unpublish")
            raise HTTPException(
                status_code=400,
                detail="Module is not published - nothing to unpublish"
            )

        notebook.published = False
        await notebook.save()

        logger.info(f"Notebook {notebook_id} unpublished by admin {admin.id}")

        # Query with counts after unpublish
        query = """
            SELECT *,
            count(<-reference.in) as source_count,
            count(<-artifact.in) as note_count
            FROM $notebook_id
        """
        result = await repo_query(query, {"notebook_id": ensure_record_id(notebook_id)})

        if result:
            nb = result[0]
            nb_id = str(nb.get("id", ""))

            # Get objectives count for this notebook
            objectives_count = 0
            try:
                objectives_count = await LearningObjective.count_for_notebook(nb_id)
            except Exception as e:
                logger.warning("Failed to get objectives count for {}: {}", nb_id, str(e))

            # Check for module prompt
            has_prompt = False
            try:
                module_prompt = await ModulePrompt.get_by_notebook(nb_id)
                has_prompt = module_prompt is not None and bool(module_prompt.system_prompt)
            except Exception as e:
                logger.warning("Failed to check prompt status for {}: {}", nb_id, str(e))

            return NotebookResponse(
                id=nb_id,
                name=nb.get("name", ""),
                description=nb.get("description", ""),
                archived=nb.get("archived", False),
                published=False,  # Explicitly False after unpublish
                created=str(nb.get("created", "")),
                updated=str(nb.get("updated", "")),
                source_count=nb.get("source_count", 0),
                note_count=nb.get("note_count", 0),
                objectives_count=objectives_count,
                has_prompt=has_prompt,
            )

        # Fallback if query fails
        return NotebookResponse(
            id=notebook.id or "",
            name=notebook.name,
            description=notebook.description,
            archived=notebook.archived or False,
            published=False,
            created=str(notebook.created),
            updated=str(notebook.updated),
            source_count=0,
            note_count=0,
            objectives_count=0,
            has_prompt=False,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error unpublishing notebook {}: {}", notebook_id, str(e))
        raise HTTPException(
            status_code=500, detail=f"Error unpublishing notebook: {str(e)}"
        )
