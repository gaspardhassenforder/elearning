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
        """Test surface_document with valid source returns LLM content string.

        Note: surface_document uses content_and_artifact response format.
        When called via ainvoke() directly (not through ToolNode), only the
        content string is returned. The artifact dict is only accessible
        when running through ToolNode (which creates a ToolMessage with .artifact).
        """
        from unittest.mock import AsyncMock, patch, MagicMock
        from datetime import datetime

        # Use MagicMock instead of real Source (Pydantic model doesn't allow arbitrary attrs)
        mock_source = MagicMock()
        mock_source.title = "Test Document"
        mock_source.asset = MagicMock()
        mock_source.asset.file_path = "/path/to/document.pdf"
        mock_source.asset.url = None
        mock_source.created = datetime(2024, 1, 1, 12, 0, 0)
        mock_source.get_context = AsyncMock(return_value={
            "id": "source:test123",
            "title": "Test Document",
            "insights": [{"insight_type": "summary", "content": "A short summary"}],
        })

        with patch("open_notebook.domain.notebook.Source.get", new=AsyncMock(return_value=mock_source)):
            result = await surface_document.ainvoke({
                "source_id": "source:test123",
                "excerpt_text": "This is a test excerpt from the document.",
                "relevance_reason": "Explains the core concept"
            })

        # ainvoke returns only the content string (artifact is ToolNode-only)
        assert isinstance(result, str)
        assert "Test Document" in result
        assert "source:test123" in result

    @pytest.mark.asyncio
    async def test_surface_document_truncates_long_excerpt(self):
        """Test surface_document truncates excerpts in content_and_artifact mode."""
        from unittest.mock import AsyncMock, patch, MagicMock

        mock_source = MagicMock()
        mock_source.title = "Test Document"
        mock_source.asset = MagicMock()
        mock_source.asset.file_path = "/path/to/document.pdf"
        mock_source.asset.url = None
        mock_source.created = None
        mock_source.get_context = AsyncMock(return_value={
            "id": "source:test123",
            "title": "Test Document",
            "insights": [],
        })

        long_excerpt = "A" * 250  # 250 characters

        with patch("open_notebook.domain.notebook.Source.get", new=AsyncMock(return_value=mock_source)):
            result = await surface_document.ainvoke({
                "source_id": "source:test123",
                "excerpt_text": long_excerpt,
                "relevance_reason": "Test truncation"
            })

        # ainvoke returns content string containing the document info
        assert isinstance(result, str)
        assert "Test Document" in result

    @pytest.mark.asyncio
    async def test_surface_document_with_nonexistent_source(self):
        """Test surface_document with nonexistent source returns error content."""
        from unittest.mock import AsyncMock, patch

        with patch("open_notebook.domain.notebook.Source.get", new=AsyncMock(return_value=None)):
            result = await surface_document.ainvoke({
                "source_id": "source:nonexistent",
                "excerpt_text": "Test",
                "relevance_reason": "Test"
            })

        # ainvoke returns content string on error
        assert isinstance(result, str)
        assert "not found" in result

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

        # ainvoke returns content string on error
        assert isinstance(result, str)
        assert "trouble" in result


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
