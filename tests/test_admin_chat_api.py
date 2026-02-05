"""Tests for admin chat API endpoints."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException


class TestAdminChatRouter:
    """Test admin chat router logic and access control."""

    @pytest.mark.asyncio
    async def test_admin_chat_endpoint_exists(self):
        """Test that admin_chat router can be imported."""
        try:
            from api.routers import admin_chat
            assert hasattr(admin_chat, 'router')
        except ImportError:
            pytest.fail("admin_chat router module should exist")

    @pytest.mark.asyncio
    async def test_require_admin_dependency_blocks_learners(self):
        """Test require_admin dependency blocks learner users."""
        from api.auth import require_admin

        # Mock learner user
        mock_learner = MagicMock()
        mock_learner.id = "user:learner123"
        mock_learner.role = "learner"

        # Should raise HTTPException for learner
        with pytest.raises(HTTPException) as exc_info:
            await require_admin(mock_learner)

        assert exc_info.value.status_code == 403
        assert "Admin access required" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_require_admin_dependency_allows_admins(self):
        """Test require_admin dependency allows admin users."""
        from api.auth import require_admin

        # Mock admin user
        mock_admin = MagicMock()
        mock_admin.id = "user:admin123"
        mock_admin.role = "admin"

        # Should return user for admin
        result = await require_admin(mock_admin)
        assert result == mock_admin
        assert result.role == "admin"


class TestAdminChatContextAssembly:
    """Test context assembly logic for admin assistant."""

    @pytest.mark.asyncio
    @patch("api.routers.admin_chat.Notebook.get")
    @patch("api.routers.admin_chat.LearningObjective.get_for_notebook")
    @patch("api.routers.admin_chat.ModulePrompt.get_by_notebook")
    async def test_assemble_context_loads_notebook_and_sources(
        self, mock_get_prompt, mock_get_objectives, mock_get_notebook
    ):
        """Test context assembly loads notebook and sources with content for RAG grounding."""
        from api.routers.admin_chat import assemble_admin_context

        # Mock notebook
        mock_notebook = MagicMock()
        mock_notebook.id = "notebook:123"
        mock_notebook.title = "Test Module"

        # Mock notebook.get_sources() with source that has get_context()
        mock_source = MagicMock()
        mock_source.title = "Intro Doc"
        mock_source.get_context = AsyncMock(return_value={
            "summary": "Introduction to AI concepts",
            "content": "This document covers machine learning, neural networks, and deep learning fundamentals."
        })
        mock_notebook.get_sources = AsyncMock(return_value=[mock_source])

        mock_get_notebook.return_value = mock_notebook

        # Mock learning objectives
        mock_get_objectives.return_value = []

        # Mock module prompt
        mock_get_prompt.return_value = None

        # Call context assembly
        context = await assemble_admin_context("notebook:123")

        # Verify context structure includes content (AC#3: grounded in documents)
        assert context["module_title"] == "Test Module"
        assert len(context["documents"]) == 1
        assert context["documents"][0]["title"] == "Intro Doc"
        # CRITICAL: Verify document content is included (not just title)
        assert context["documents"][0]["summary"] == "Introduction to AI concepts"
        assert "excerpt" in context["documents"][0]
        assert len(context["documents"][0]["excerpt"]) > 0

    @pytest.mark.asyncio
    @patch("api.routers.admin_chat.Notebook.get")
    async def test_assemble_context_handles_missing_notebook(self, mock_get_notebook):
        """Test context assembly handles missing notebook gracefully."""
        from api.routers.admin_chat import assemble_admin_context

        mock_get_notebook.return_value = None

        # Should raise HTTPException for missing notebook
        with pytest.raises(HTTPException) as exc_info:
            await assemble_admin_context("notebook:nonexistent")

        assert exc_info.value.status_code == 404
        assert "Notebook not found" in exc_info.value.detail

    @pytest.mark.asyncio
    @patch("api.routers.admin_chat.Notebook.get")
    @patch("api.routers.admin_chat.LearningObjective.get_for_notebook")
    @patch("api.routers.admin_chat.ModulePrompt.get_by_notebook")
    async def test_assemble_context_includes_document_content_for_rag(
        self, mock_get_prompt, mock_get_objectives, mock_get_notebook
    ):
        """Test AC#3: Context includes actual document content (not just titles) for RAG grounding."""
        from api.routers.admin_chat import assemble_admin_context

        # Mock notebook
        mock_notebook = MagicMock()
        mock_notebook.id = "notebook:456"
        mock_notebook.title = "AI in Healthcare"

        # Mock multiple sources with rich content
        mock_source1 = MagicMock()
        mock_source1.title = "Medical AI Ethics"
        mock_source1.get_context = AsyncMock(return_value={
            "summary": "Discusses ethical considerations in medical AI systems",
            "content": "AI in healthcare must prioritize patient privacy, avoid algorithmic bias, and ensure transparency in diagnostic recommendations."
        })

        mock_source2 = MagicMock()
        mock_source2.title = "Clinical Decision Support"
        mock_source2.get_context = AsyncMock(return_value={
            "summary": "Overview of AI-powered clinical decision support systems",
            "content": "CDSS tools analyze patient data to provide evidence-based treatment recommendations. Integration with EHR systems is critical."
        })

        mock_notebook.get_sources = AsyncMock(return_value=[mock_source1, mock_source2])
        mock_get_notebook.return_value = mock_notebook
        mock_get_objectives.return_value = []
        mock_get_prompt.return_value = None

        # Call context assembly
        context = await assemble_admin_context("notebook:456")

        # Verify AC#3: Documents contain content, not just metadata
        assert len(context["documents"]) == 2

        # First document
        doc1 = context["documents"][0]
        assert doc1["title"] == "Medical AI Ethics"
        assert doc1["summary"] == "Discusses ethical considerations in medical AI systems"
        assert "patient privacy" in doc1["excerpt"] or "algorithmic bias" in doc1["excerpt"]

        # Second document
        doc2 = context["documents"][1]
        assert doc2["title"] == "Clinical Decision Support"
        assert doc2["summary"] == "Overview of AI-powered clinical decision support systems"
        assert "CDSS" in doc2["excerpt"] or "patient data" in doc2["excerpt"]

        # Verify both sources' get_context() was called (RAG retrieval happened)
        mock_source1.get_context.assert_called_once_with(context_size="short")
        mock_source2.get_context.assert_called_once_with(context_size="short")
