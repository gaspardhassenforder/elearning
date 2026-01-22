from typing import List, Optional
from pydantic import BaseModel, Field

from fastapi import APIRouter, HTTPException, Query
from loguru import logger

from api.models import NotebookCreate, NotebookResponse, NotebookUpdate
from open_notebook.database.repository import ensure_record_id, repo_query
from open_notebook.domain.notebook import Notebook, Source, Note
from open_notebook.domain.transformation import Transformation
from open_notebook.domain.artifact import Artifact
from open_notebook.exceptions import InvalidInputError
from open_notebook.graphs.transformation import graph as transformation_graph

router = APIRouter()


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

        return [
            NotebookResponse(
                id=str(nb.get("id", "")),
                name=nb.get("name", ""),
                description=nb.get("description", ""),
                archived=nb.get("archived", False),
                created=str(nb.get("created", "")),
                updated=str(nb.get("updated", "")),
                source_count=nb.get("source_count", 0),
                note_count=nb.get("note_count", 0),
            )
            for nb in result
        ]
    except Exception as e:
        logger.error(f"Error fetching notebooks: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error fetching notebooks: {str(e)}"
        )


@router.post("/notebooks", response_model=NotebookResponse)
async def create_notebook(notebook: NotebookCreate):
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
            created=str(new_notebook.created),
            updated=str(new_notebook.updated),
            source_count=0,  # New notebook has no sources
            note_count=0,  # New notebook has no notes
        )
    except InvalidInputError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating notebook: {str(e)}")
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
        return NotebookResponse(
            id=str(nb.get("id", "")),
            name=nb.get("name", ""),
            description=nb.get("description", ""),
            archived=nb.get("archived", False),
            created=str(nb.get("created", "")),
            updated=str(nb.get("updated", "")),
            source_count=nb.get("source_count", 0),
            note_count=nb.get("note_count", 0),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching notebook {notebook_id}: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error fetching notebook: {str(e)}"
        )


@router.put("/notebooks/{notebook_id}", response_model=NotebookResponse)
async def update_notebook(notebook_id: str, notebook_update: NotebookUpdate):
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
            return NotebookResponse(
                id=str(nb.get("id", "")),
                name=nb.get("name", ""),
                description=nb.get("description", ""),
                archived=nb.get("archived", False),
                created=str(nb.get("created", "")),
                updated=str(nb.get("updated", "")),
                source_count=nb.get("source_count", 0),
                note_count=nb.get("note_count", 0),
            )

        # Fallback if query fails
        return NotebookResponse(
            id=notebook.id or "",
            name=notebook.name,
            description=notebook.description,
            archived=notebook.archived or False,
            created=str(notebook.created),
            updated=str(notebook.updated),
            source_count=0,
            note_count=0,
        )
    except HTTPException:
        raise
    except InvalidInputError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating notebook {notebook_id}: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error updating notebook: {str(e)}"
        )


@router.post("/notebooks/{notebook_id}/sources/{source_id}")
async def add_source_to_notebook(notebook_id: str, source_id: str):
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
            f"Error linking source {source_id} to notebook {notebook_id}: {str(e)}"
        )
        raise HTTPException(
            status_code=500, detail=f"Error linking source to notebook: {str(e)}"
        )


@router.delete("/notebooks/{notebook_id}/sources/{source_id}")
async def remove_source_from_notebook(notebook_id: str, source_id: str):
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
            f"Error removing source {source_id} from notebook {notebook_id}: {str(e)}"
        )
        raise HTTPException(
            status_code=500, detail=f"Error removing source from notebook: {str(e)}"
        )


class NotebookTransformationRequest(BaseModel):
    """Request body for notebook transformation generation."""
    transformation_id: str = Field(..., description="ID of the transformation to apply")
    model_id: Optional[str] = Field(None, description="Optional model ID to use")


@router.post("/notebooks/{notebook_id}/transformations/generate")
async def generate_transformation(notebook_id: str, request: NotebookTransformationRequest):
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
        logger.error(f"Error generating transformation: {e}")
        logger.exception(e)
        raise HTTPException(status_code=500, detail=f"Failed to generate transformation: {str(e)}")


@router.delete("/notebooks/{notebook_id}")
async def delete_notebook(notebook_id: str):
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
        logger.error(f"Error deleting notebook {notebook_id}: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error deleting notebook: {str(e)}"
        )
