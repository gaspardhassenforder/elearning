"""
Unit tests for the open_notebook.graphs module.

This test suite focuses on testing graph structures, tools, and validation
without heavy mocking of the actual processing logic.
"""

from datetime import datetime

import pytest

from open_notebook.graphs.prompt import PatternChainState, graph
from open_notebook.graphs.tools import get_current_timestamp, surface_document
from open_notebook.graphs.transformation import (
    TransformationState,
    run_transformation,
)
from open_notebook.graphs.transformation import (
    graph as transformation_graph,
)

# ============================================================================
# TEST SUITE 1: Graph Tools
# ============================================================================


class TestGraphTools:
    """Test suite for graph tool definitions."""

    def test_get_current_timestamp_format(self):
        """Test timestamp tool returns correct format."""
        timestamp = get_current_timestamp.func()

        assert isinstance(timestamp, str)
        assert len(timestamp) == 14  # YYYYMMDDHHmmss format
        assert timestamp.isdigit()

    def test_get_current_timestamp_validity(self):
        """Test timestamp represents valid datetime."""
        timestamp = get_current_timestamp.func()

        # Parse it back to datetime to verify validity
        year = int(timestamp[0:4])
        month = int(timestamp[4:6])
        day = int(timestamp[6:8])
        hour = int(timestamp[8:10])
        minute = int(timestamp[10:12])
        second = int(timestamp[12:14])

        # Should be valid date components
        assert 2020 <= year <= 2100
        assert 1 <= month <= 12
        assert 1 <= day <= 31
        assert 0 <= hour <= 23
        assert 0 <= minute <= 59
        assert 0 <= second <= 59

        # Should parse as datetime
        dt = datetime.strptime(timestamp, "%Y%m%d%H%M%S")
        assert isinstance(dt, datetime)

    def test_get_current_timestamp_is_tool(self):
        """Test that function is properly decorated as a tool."""
        # Check it has tool attributes
        assert hasattr(get_current_timestamp, "name")
        assert hasattr(get_current_timestamp, "description")

    @pytest.mark.asyncio
    async def test_surface_document_is_tool(self):
        """Test that surface_document is properly decorated as a tool."""
        # Check it has tool attributes
        assert hasattr(surface_document, "name")
        assert hasattr(surface_document, "description")
        assert surface_document.name == "surface_document"

    @pytest.mark.asyncio
    async def test_surface_document_with_valid_source(self):
        """Test surface_document with valid source returns structured data."""
        from unittest.mock import AsyncMock, patch
        from datetime import datetime
        from open_notebook.domain.notebook import Source, Asset

        # Mock source data
        mock_source = Source(
            id="source:test123",
            notebook_id="notebook:nb1",
            title="Test Document",
            asset=Asset(file_path="/path/to/document.pdf"),
            created=datetime(2024, 1, 1, 12, 0, 0),
        )

        with patch("open_notebook.domain.notebook.Source.get", new=AsyncMock(return_value=mock_source)):
            result = await surface_document.ainvoke({
                "source_id": "source:test123",
                "excerpt_text": "This is a test excerpt from the document.",
                "relevance_reason": "Explains the core concept"
            })

        # Verify structure
        assert isinstance(result, dict)
        assert result["source_id"] == "source:test123"
        assert result["title"] == "Test Document"
        assert result["source_type"] == "pdf"
        assert result["excerpt"] == "This is a test excerpt from the document."
        assert result["relevance"] == "Explains the core concept"
        assert "metadata" in result

    @pytest.mark.asyncio
    async def test_surface_document_truncates_long_excerpt(self):
        """Test surface_document truncates excerpts longer than 200 chars."""
        from unittest.mock import AsyncMock, patch
        from open_notebook.domain.notebook import Source, Asset

        mock_source = Source(
            id="source:test123",
            notebook_id="notebook:nb1",
            title="Test Document",
            asset=Asset(file_path="/path/to/document.pdf"),
        )

        long_excerpt = "A" * 250  # 250 characters

        with patch("open_notebook.domain.notebook.Source.get", new=AsyncMock(return_value=mock_source)):
            result = await surface_document.ainvoke({
                "source_id": "source:test123",
                "excerpt_text": long_excerpt,
                "relevance_reason": "Test truncation"
            })

        # Should be truncated to 200 chars (197 + "...")
        assert len(result["excerpt"]) == 200
        assert result["excerpt"].endswith("...")

    @pytest.mark.asyncio
    async def test_surface_document_with_nonexistent_source(self):
        """Test surface_document with nonexistent source returns error."""
        from unittest.mock import AsyncMock, patch

        with patch("open_notebook.domain.notebook.Source.get", new=AsyncMock(return_value=None)):
            result = await surface_document.ainvoke({
                "source_id": "source:nonexistent",
                "excerpt_text": "Test",
                "relevance_reason": "Test"
            })

        # Should return error structure
        assert "error" in result
        assert result["error"] == "Source not found"
        assert result["source_id"] == "source:nonexistent"

    @pytest.mark.asyncio
    async def test_surface_document_handles_exceptions(self):
        """Test surface_document gracefully handles exceptions."""
        from unittest.mock import AsyncMock, patch

        with patch("open_notebook.domain.notebook.Source.get", new=AsyncMock(side_effect=Exception("Database error"))):
            result = await surface_document.ainvoke({
                "source_id": "source:test123",
                "excerpt_text": "Test",
                "relevance_reason": "Test"
            })

        # Should return error structure
        assert "error" in result
        assert "Failed to surface document" in result["error"]
        assert result["source_id"] == "source:test123"


# ============================================================================
# TEST SUITE 2: Prompt Graph State
# ============================================================================


class TestPromptGraph:
    """Test suite for prompt pattern chain graph."""

    def test_pattern_chain_state_structure(self):
        """Test PatternChainState structure and fields."""
        state = PatternChainState(
            prompt="Test prompt", parser=None, input_text="Test input", output=""
        )

        assert state["prompt"] == "Test prompt"
        assert state["parser"] is None
        assert state["input_text"] == "Test input"
        assert state["output"] == ""

    def test_prompt_graph_compilation(self):
        """Test that prompt graph compiles correctly."""
        assert graph is not None

        # Graph should have the expected structure
        assert hasattr(graph, "invoke")
        assert hasattr(graph, "ainvoke")


# ============================================================================
# TEST SUITE 3: Transformation Graph
# ============================================================================


class TestTransformationGraph:
    """Test suite for transformation graph workflows."""

    def test_transformation_state_structure(self):
        """Test TransformationState structure and fields."""
        from unittest.mock import MagicMock

        from open_notebook.domain.notebook import Source
        from open_notebook.domain.transformation import Transformation

        mock_source = MagicMock(spec=Source)
        mock_transformation = MagicMock(spec=Transformation)

        state = TransformationState(
            input_text="Test text",
            source=mock_source,
            transformation=mock_transformation,
            output="",
        )

        assert state["input_text"] == "Test text"
        assert state["source"] == mock_source
        assert state["transformation"] == mock_transformation
        assert state["output"] == ""

    @pytest.mark.asyncio
    async def test_run_transformation_assertion_no_content(self):
        """Test transformation raises assertion with no content."""
        from unittest.mock import MagicMock

        from open_notebook.domain.transformation import Transformation

        mock_transformation = MagicMock(spec=Transformation)

        state = {
            "input_text": None,
            "transformation": mock_transformation,
            "source": None,
        }

        config = {"configurable": {"model_id": None}}

        with pytest.raises(AssertionError, match="No content to transform"):
            await run_transformation(state, config)

    def test_transformation_graph_compilation(self):
        """Test that transformation graph compiles correctly."""
        assert transformation_graph is not None
        assert hasattr(transformation_graph, "invoke")
        assert hasattr(transformation_graph, "ainvoke")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
