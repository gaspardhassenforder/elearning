"""
Simplified navigation assistant tests (Story 6.1).

Tests search_available_modules tool logic with config parameter pattern.
"""

import pytest
from unittest.mock import AsyncMock, patch


class TestSearchAvailableModulesSimple:
    """Simplified tests for search_available_modules tool."""

    @pytest.mark.asyncio
    async def test_search_with_company_id(self):
        """Test search extracts company_id from config and queries correctly."""
        # Mock the repo_query function
        mock_results = [
            {"id": "notebook:ml101", "title": "Machine Learning", "description": "ML fundamentals", "created": "2024-01-01"},
        ]

        config = {"configurable": {"company_id": "company:test", "current_notebook_id": None}}

        with patch("open_notebook.database.repository.repo_query", new=AsyncMock(return_value=mock_results)):
            # Import after patching
            from open_notebook.graphs.tools import search_available_modules

            # Call via ainvoke with config as separate parameter (LangChain pattern)
            result = await search_available_modules.ainvoke(
                input={"query": "machine learning", "limit": 5},
                config=config
            )

        # Tool should return list of modules
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["id"] == "notebook:ml101"

    @pytest.mark.asyncio
    async def test_search_without_company_id_returns_empty(self):
        """Test search returns empty list when company_id not in config."""
        with patch("open_notebook.database.repository.repo_query", new=AsyncMock(return_value=[])):
            from open_notebook.graphs.tools import search_available_modules

            # Call without company_id in config
            result = await search_available_modules.ainvoke(
                input={"query": "test", "limit": 5},
                config={}  # Empty config, no company_id
            )

        # Should return empty list (logged warning about missing company_id)
        assert result == []

    @pytest.mark.asyncio
    async def test_search_relevance_scoring(self):
        """Test relevance scoring based on title vs description matches."""
        mock_results = [
            {"id": "notebook:ml101", "title": "Machine Learning Fundamentals", "description": "Core concepts", "created": "2024-01-01"},
            {"id": "notebook:ai101", "title": "AI Basics", "description": "Introduction to machine learning", "created": "2024-01-02"},
        ]

        config = {"configurable": {"company_id": "company:test", "current_notebook_id": None}}

        with patch("open_notebook.database.repository.repo_query", new=AsyncMock(return_value=mock_results)):
            from open_notebook.graphs.tools import search_available_modules

            result = await search_available_modules.ainvoke(
                input={"query": "machine learning", "limit": 5},
                config=config
            )

        # Title match should have higher relevance score
        assert result[0]["relevance_score"] == 1.0  # Title contains query
        assert result[1]["relevance_score"] == 0.5  # Only description contains query


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
