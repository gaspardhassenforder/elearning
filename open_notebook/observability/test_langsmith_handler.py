"""
Unit tests for LangSmith callback handler utility.

Tests the get_langsmith_callback() function for:
- Callback creation with metadata
- Optional activation (returns None when disabled)
- Partial metadata handling
- Project name configuration
- Tags and metadata formatting
"""

import os
import pytest
from unittest.mock import patch, MagicMock
from open_notebook.observability.langsmith_handler import get_langsmith_callback


class TestLangSmithCallbackHandler:
    """Test suite for LangSmith callback handler utility."""

    def test_callback_returns_none_when_disabled(self):
        """Returns None if LANGCHAIN_TRACING_V2 != 'true'"""
        with patch.dict(os.environ, {"LANGCHAIN_TRACING_V2": "false"}, clear=False):
            callback = get_langsmith_callback(
                user_id="user:123",
                company_id="company:456",
                notebook_id="notebook:789",
                workflow_name="test_workflow",
            )
            assert callback is None

    def test_callback_returns_none_when_env_missing(self):
        """Returns None if LANGCHAIN_TRACING_V2 env var not set"""
        with patch.dict(os.environ, {}, clear=False):
            # Remove the env var if it exists
            os.environ.pop("LANGCHAIN_TRACING_V2", None)
            callback = get_langsmith_callback(
                user_id="user:123",
                workflow_name="test_workflow",
            )
            assert callback is None

    @patch("open_notebook.observability.langsmith_handler.LangChainTracer")
    def test_callback_creation_with_full_metadata(self, mock_tracer_class):
        """Callback includes all metadata tags when all parameters provided"""
        mock_tracer = MagicMock()
        mock_tracer_class.return_value = mock_tracer

        with patch.dict(
            os.environ,
            {
                "LANGCHAIN_TRACING_V2": "true",
                "LANGCHAIN_PROJECT": "Test Project",
            },
            clear=False,
        ):
            callback = get_langsmith_callback(
                user_id="user:123",
                company_id="company:456",
                notebook_id="notebook:789",
                workflow_name="test_workflow",
                run_name="custom_run",
            )

            # Verify tracer was created with correct parameters
            mock_tracer_class.assert_called_once()
            call_kwargs = mock_tracer_class.call_args[1]

            assert call_kwargs["project_name"] == "Test Project"
            assert "user:user:123" in call_kwargs["tags"]
            assert "company:company:456" in call_kwargs["tags"]
            assert "notebook:notebook:789" in call_kwargs["tags"]
            assert "workflow:test_workflow" in call_kwargs["tags"]

            assert call_kwargs["metadata"]["user_id"] == "user:123"
            assert call_kwargs["metadata"]["company_id"] == "company:456"
            assert call_kwargs["metadata"]["notebook_id"] == "notebook:789"
            assert call_kwargs["metadata"]["workflow_name"] == "test_workflow"

            # Verify run_name was set
            assert callback.run_name == "custom_run"

    @patch("open_notebook.observability.langsmith_handler.LangChainTracer")
    def test_callback_with_partial_metadata(self, mock_tracer_class):
        """Works with missing user_id, company_id, notebook_id"""
        mock_tracer = MagicMock()
        mock_tracer_class.return_value = mock_tracer

        with patch.dict(
            os.environ,
            {"LANGCHAIN_TRACING_V2": "true"},
            clear=False,
        ):
            callback = get_langsmith_callback(
                workflow_name="test_workflow",
            )

            # Verify tracer was created
            assert callback is not None
            call_kwargs = mock_tracer_class.call_args[1]

            # Only workflow tag should be present
            assert len([t for t in call_kwargs["tags"] if t.startswith("user:")]) == 0
            assert len([t for t in call_kwargs["tags"] if t.startswith("company:")]) == 0
            assert len([t for t in call_kwargs["tags"] if t.startswith("notebook:")]) == 0
            assert "workflow:test_workflow" in call_kwargs["tags"]

            # Metadata should only include workflow_name
            assert "user_id" not in call_kwargs["metadata"]
            assert "company_id" not in call_kwargs["metadata"]
            assert "notebook_id" not in call_kwargs["metadata"]
            assert call_kwargs["metadata"]["workflow_name"] == "test_workflow"

    @patch("open_notebook.observability.langsmith_handler.LangChainTracer")
    def test_callback_project_name_from_env(self, mock_tracer_class):
        """Uses LANGCHAIN_PROJECT env var for project name"""
        mock_tracer = MagicMock()
        mock_tracer_class.return_value = mock_tracer

        with patch.dict(
            os.environ,
            {
                "LANGCHAIN_TRACING_V2": "true",
                "LANGCHAIN_PROJECT": "Custom Project Name",
            },
            clear=False,
        ):
            callback = get_langsmith_callback(workflow_name="test_workflow")

            assert callback is not None
            call_kwargs = mock_tracer_class.call_args[1]
            assert call_kwargs["project_name"] == "Custom Project Name"

    @patch("open_notebook.observability.langsmith_handler.LangChainTracer")
    def test_callback_default_project_name(self, mock_tracer_class):
        """Uses default project name 'Open Notebook' when LANGCHAIN_PROJECT not set"""
        mock_tracer = MagicMock()
        mock_tracer_class.return_value = mock_tracer

        with patch.dict(
            os.environ,
            {"LANGCHAIN_TRACING_V2": "true"},
            clear=False,
        ):
            # Remove LANGCHAIN_PROJECT if it exists
            os.environ.pop("LANGCHAIN_PROJECT", None)

            callback = get_langsmith_callback(workflow_name="test_workflow")

            assert callback is not None
            call_kwargs = mock_tracer_class.call_args[1]
            assert call_kwargs["project_name"] == "Open Notebook"

    @patch("open_notebook.observability.langsmith_handler.LangChainTracer")
    def test_callback_tags_format(self, mock_tracer_class):
        """Tags formatted as user:id, company:id, workflow:name"""
        mock_tracer = MagicMock()
        mock_tracer_class.return_value = mock_tracer

        with patch.dict(
            os.environ,
            {"LANGCHAIN_TRACING_V2": "true"},
            clear=False,
        ):
            callback = get_langsmith_callback(
                user_id="user123",
                company_id="company456",
                notebook_id="notebook789",
                workflow_name="test_workflow",
            )

            assert callback is not None
            call_kwargs = mock_tracer_class.call_args[1]

            # Verify exact tag format
            assert "user:user123" in call_kwargs["tags"]
            assert "company:company456" in call_kwargs["tags"]
            assert "notebook:notebook789" in call_kwargs["tags"]
            assert "workflow:test_workflow" in call_kwargs["tags"]

    @patch("open_notebook.observability.langsmith_handler.LangChainTracer")
    def test_run_name_defaults_to_none(self, mock_tracer_class):
        """Run name is not set when run_name parameter is None"""
        mock_tracer = MagicMock()
        # Set run_name attribute to None initially
        mock_tracer.run_name = None
        mock_tracer_class.return_value = mock_tracer

        with patch.dict(
            os.environ,
            {"LANGCHAIN_TRACING_V2": "true"},
            clear=False,
        ):
            callback = get_langsmith_callback(
                workflow_name="test_workflow",
                run_name=None,
            )

            assert callback is not None
            # Verify run_name was not set (remains None)
            assert callback.run_name is None
