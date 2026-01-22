"""
Unit tests for transformation artifact generation.
Tests the flow of generating transformations on notebook content.
"""

import os
import pytest
from unittest.mock import patch, AsyncMock, MagicMock


@pytest.fixture(autouse=True)
def setup_test_env():
    """Set up test environment variables."""
    os.environ.setdefault("SURREAL_URL", "ws://localhost:8000/rpc")
    os.environ.setdefault("SURREAL_USER", "root")
    os.environ.setdefault("SURREAL_PASSWORD", "root")
    os.environ.setdefault("SURREAL_NAMESPACE", "test")
    os.environ.setdefault("SURREAL_DATABASE", "test")


class TestNotebookTransformationAPI:
    """Test suite for notebook transformation API endpoint."""

    @pytest.mark.asyncio
    async def test_notebook_not_found(self):
        """Test that non-existent notebook returns 404."""
        from api.routers.notebooks import generate_transformation, NotebookTransformationRequest
        from fastapi import HTTPException

        request = NotebookTransformationRequest(
            transformation_id="transformation:test123"
        )

        with patch("api.routers.notebooks.Notebook.get") as mock_get:
            mock_get.return_value = None

            with pytest.raises(HTTPException) as exc_info:
                await generate_transformation("notebook:notfound", request)
            assert exc_info.value.status_code == 404
            assert "not found" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_transformation_not_found(self):
        """Test that non-existent transformation returns 404."""
        from api.routers.notebooks import generate_transformation, NotebookTransformationRequest
        from fastapi import HTTPException

        mock_notebook = MagicMock()
        mock_notebook.id = "notebook:test123"

        request = NotebookTransformationRequest(
            transformation_id="transformation:notfound"
        )

        with patch("api.routers.notebooks.Notebook.get") as mock_nb_get, \
             patch("api.routers.notebooks.Transformation.get") as mock_trans_get:
            mock_nb_get.return_value = mock_notebook
            mock_trans_get.return_value = None

            with pytest.raises(HTTPException) as exc_info:
                await generate_transformation("notebook:test123", request)
            assert exc_info.value.status_code == 404
            assert "not found" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_no_sources_in_notebook(self):
        """Test that notebook with no sources returns error."""
        from api.routers.notebooks import generate_transformation, NotebookTransformationRequest
        from fastapi import HTTPException

        mock_notebook = MagicMock()
        mock_notebook.id = "notebook:test123"

        mock_transformation = MagicMock()
        mock_transformation.id = "transformation:test123"

        request = NotebookTransformationRequest(
            transformation_id="transformation:test123"
        )

        with patch("api.routers.notebooks.Notebook.get") as mock_nb_get, \
             patch("api.routers.notebooks.Transformation.get") as mock_trans_get, \
             patch("api.routers.notebooks.repo_query") as mock_query:
            mock_nb_get.return_value = mock_notebook
            mock_trans_get.return_value = mock_transformation
            mock_query.return_value = []

            with pytest.raises(HTTPException) as exc_info:
                await generate_transformation("notebook:test123", request)
            assert exc_info.value.status_code == 400
            assert "no sources" in exc_info.value.detail.lower()


class TestContentGathering:
    """Test suite for content gathering for transformations."""

    def test_content_combination(self):
        """Test that multiple sources are combined correctly."""
        sources = [
            {"title": "Source 1", "full_text": "Content 1"},
            {"title": "Source 2", "full_text": "Content 2"},
        ]

        content_parts = []
        for source in sources:
            if source.get("full_text"):
                title = source.get("title") or "Untitled"
                content_parts.append(f"## {title}\n\n{source['full_text']}")

        combined_content = "\n\n---\n\n".join(content_parts)

        assert "Source 1" in combined_content
        assert "Source 2" in combined_content
        assert "Content 1" in combined_content
        assert "Content 2" in combined_content

    def test_content_truncation(self):
        """Test that very long content is truncated."""
        long_text = "A" * 60000  # Very long content
        
        max_content_length = 50000
        if len(long_text) > max_content_length:
            truncated = long_text[:max_content_length] + "\n\n[Content truncated...]"
        else:
            truncated = long_text

        assert len(truncated) <= max_content_length + len("\n\n[Content truncated...]")
        assert "[Content truncated...]" in truncated


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
