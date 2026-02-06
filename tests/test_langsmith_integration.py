"""
Integration tests for LangSmith tracing.

Tests that LangGraph workflows properly integrate with LangSmith callback handlers.
Validates that traces are created with correct metadata when tracing is enabled,
and that workflows continue normally when tracing is disabled.
"""

import os
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from open_notebook.observability.langsmith_handler import get_langsmith_callback


class TestLangSmithIntegration:
    """Integration tests for LangSmith tracing across workflows."""

    @pytest.mark.asyncio
    @patch("open_notebook.observability.langsmith_handler.LangChainTracer")
    async def test_chat_workflow_with_tracing_enabled(self, mock_tracer_class):
        """Chat workflow creates trace with correct metadata when tracing enabled."""
        # Setup mock tracer
        mock_tracer = MagicMock()
        mock_tracer_class.return_value = mock_tracer

        # Enable LangSmith
        with patch.dict(
            os.environ,
            {
                "LANGCHAIN_TRACING_V2": "true",
                "LANGCHAIN_PROJECT": "Test Project",
            },
            clear=False,
        ):
            # Create callback for learner chat
            callback = get_langsmith_callback(
                user_id="user:test123",
                company_id="company:test456",
                notebook_id="notebook:test789",
                workflow_name="learner_chat",
                run_name="chat:session:test",
            )

            # Verify callback was created
            assert callback is not None
            mock_tracer_class.assert_called_once()

            # Verify metadata
            call_kwargs = mock_tracer_class.call_args[1]
            assert call_kwargs["project_name"] == "Test Project"
            assert "user:user:test123" in call_kwargs["tags"]
            assert "company:company:test456" in call_kwargs["tags"]
            assert "notebook:notebook:test789" in call_kwargs["tags"]
            assert "workflow:learner_chat" in call_kwargs["tags"]

            assert call_kwargs["metadata"]["user_id"] == "user:test123"
            assert call_kwargs["metadata"]["company_id"] == "company:test456"
            assert call_kwargs["metadata"]["notebook_id"] == "notebook:test789"
            assert call_kwargs["metadata"]["workflow_name"] == "learner_chat"

            assert callback.run_name == "chat:session:test"

    @pytest.mark.asyncio
    async def test_navigation_workflow_with_tracing_enabled(self):
        """Navigation assistant creates trace with company metadata."""
        with patch.dict(
            os.environ,
            {"LANGCHAIN_TRACING_V2": "true"},
            clear=False,
        ):
            with patch("open_notebook.observability.langsmith_handler.LangChainTracer") as mock_tracer_class:
                mock_tracer = MagicMock()
                mock_tracer_class.return_value = mock_tracer

                callback = get_langsmith_callback(
                    user_id="user:nav123",
                    company_id="company:nav456",
                    notebook_id="notebook:current789",
                    workflow_name="navigation_assistant",
                    run_name="nav:user:nav123",
                )

                assert callback is not None
                call_kwargs = mock_tracer_class.call_args[1]

                # Verify navigation-specific metadata
                assert "company:company:nav456" in call_kwargs["tags"]
                assert "workflow:navigation_assistant" in call_kwargs["tags"]
                assert callback.run_name == "nav:user:nav123"

    @pytest.mark.asyncio
    async def test_transformation_workflow_with_tracing(self):
        """Transformation workflow creates trace without user/company context."""
        with patch.dict(
            os.environ,
            {"LANGCHAIN_TRACING_V2": "true"},
            clear=False,
        ):
            with patch("open_notebook.observability.langsmith_handler.LangChainTracer") as mock_tracer_class:
                mock_tracer = MagicMock()
                mock_tracer_class.return_value = mock_tracer

                callback = get_langsmith_callback(
                    user_id=None,
                    company_id=None,
                    notebook_id=None,
                    workflow_name="transformation",
                    run_name="transformation:test",
                )

                assert callback is not None
                call_kwargs = mock_tracer_class.call_args[1]

                # Verify no user/company tags when None
                user_tags = [t for t in call_kwargs["tags"] if t.startswith("user:")]
                company_tags = [t for t in call_kwargs["tags"] if t.startswith("company:")]
                assert len(user_tags) == 0
                assert len(company_tags) == 0

                # But workflow tag should be present
                assert "workflow:transformation" in call_kwargs["tags"]

    @pytest.mark.asyncio
    async def test_workflow_runs_without_langsmith(self):
        """Workflow executes normally when LangSmith is disabled."""
        with patch.dict(
            os.environ,
            {"LANGCHAIN_TRACING_V2": "false"},
            clear=False,
        ):
            callback = get_langsmith_callback(
                user_id="user:test",
                company_id="company:test",
                notebook_id="notebook:test",
                workflow_name="test_workflow",
            )

            # Should return None when tracing disabled
            assert callback is None

    @pytest.mark.asyncio
    async def test_source_processing_background_job_tracing(self):
        """Source processing background job creates trace with source_id."""
        with patch.dict(
            os.environ,
            {"LANGCHAIN_TRACING_V2": "true"},
            clear=False,
        ):
            with patch("open_notebook.observability.langsmith_handler.LangChainTracer") as mock_tracer_class:
                mock_tracer = MagicMock()
                mock_tracer_class.return_value = mock_tracer

                # Background job - no user context
                callback = get_langsmith_callback(
                    user_id=None,
                    company_id=None,
                    notebook_id="notebook:bg123",
                    workflow_name="source_processing",
                    run_name="source:source:bg456",
                )

                assert callback is not None
                call_kwargs = mock_tracer_class.call_args[1]

                # Verify background job metadata
                assert "notebook:notebook:bg123" in call_kwargs["tags"]
                assert "workflow:source_processing" in call_kwargs["tags"]
                assert callback.run_name == "source:source:bg456"
