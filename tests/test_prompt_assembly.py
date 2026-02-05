"""
Unit tests for prompt assembly logic.

Story 3.4: AI Teacher Prompt Configuration
Tests global + per-module template rendering and merging.
"""

from unittest.mock import AsyncMock, MagicMock, mock_open, patch

import pytest

from open_notebook.graphs.prompt import assemble_system_prompt, get_default_template


class TestPromptAssembly:
    """Test suite for two-layer prompt assembly."""

    @pytest.mark.asyncio
    async def test_assemble_global_only(self):
        """Test assembly with no module prompt (global-only)."""
        mock_global_template = "Global: {{ learner_profile.role }}"

        with patch("open_notebook.graphs.prompt.Path.exists", return_value=True):
            with patch("builtins.open", mock_open(read_data=mock_global_template)):
                with patch("open_notebook.graphs.prompt.ModulePrompt.get_by_notebook", new_callable=AsyncMock) as mock_get:
                    mock_get.return_value = None

                    result = await assemble_system_prompt(
                        notebook_id="notebook:abc123",
                        learner_profile={"role": "Engineer"},
                        objectives_with_status=[],
                        context="Test context"
                    )

                    assert "Global: Engineer" in result
                    assert "MODULE-SPECIFIC" not in result

    @pytest.mark.asyncio
    async def test_assemble_with_module_prompt(self):
        """Test assembly with module prompt (global + module)."""
        mock_global_template = "Global: {{ learner_profile.role }}"
        mock_module_prompt_obj = MagicMock()
        mock_module_prompt_obj.system_prompt = "Module: Focus on {{ learner_profile.role }}"

        with patch("open_notebook.graphs.prompt.Path.exists", return_value=True):
            with patch("builtins.open", mock_open(read_data=mock_global_template)):
                with patch("open_notebook.graphs.prompt.ModulePrompt.get_by_notebook", new_callable=AsyncMock) as mock_get:
                    mock_get.return_value = mock_module_prompt_obj

                    result = await assemble_system_prompt(
                        notebook_id="notebook:abc123",
                        learner_profile={"role": "Manager"},
                        objectives_with_status=[],
                        context=None
                    )

                    assert "Global: Manager" in result
                    assert "MODULE-SPECIFIC CUSTOMIZATION" in result
                    assert "Module: Focus on Manager" in result

    @pytest.mark.asyncio
    async def test_assemble_with_empty_module_prompt(self):
        """Test assembly when module prompt exists but system_prompt is None."""
        mock_global_template = "Global: Test"
        mock_module_prompt_obj = MagicMock()
        mock_module_prompt_obj.system_prompt = None

        with patch("open_notebook.graphs.prompt.Path.exists", return_value=True):
            with patch("builtins.open", mock_open(read_data=mock_global_template)):
                with patch("open_notebook.graphs.prompt.ModulePrompt.get_by_notebook", new_callable=AsyncMock) as mock_get:
                    mock_get.return_value = mock_module_prompt_obj

                    result = await assemble_system_prompt(
                        notebook_id="notebook:abc123"
                    )

                    assert "Global: Test" in result
                    assert "MODULE-SPECIFIC" not in result

    @pytest.mark.asyncio
    async def test_assemble_with_objectives(self):
        """Test objectives injection in global template."""
        mock_global_template = "{% for obj in objectives %}{{ obj.text }}\n{% endfor %}"

        with patch("open_notebook.graphs.prompt.Path.exists", return_value=True):
            with patch("builtins.open", mock_open(read_data=mock_global_template)):
                with patch("open_notebook.graphs.prompt.ModulePrompt.get_by_notebook", new_callable=AsyncMock) as mock_get:
                    mock_get.return_value = None

                    objectives = [
                        {"text": "Learn Python", "status": "completed"},
                        {"text": "Learn Django", "status": "in-progress"}
                    ]

                    result = await assemble_system_prompt(
                        notebook_id="notebook:abc123",
                        objectives_with_status=objectives
                    )

                    assert "Learn Python" in result
                    assert "Learn Django" in result

    @pytest.mark.asyncio
    async def test_assemble_global_template_not_found(self):
        """Test error handling when global template file not found."""
        with patch("open_notebook.graphs.prompt.Path.exists", return_value=False):
            with pytest.raises(FileNotFoundError):
                await assemble_system_prompt(notebook_id="notebook:abc123")

    @pytest.mark.asyncio
    async def test_assemble_module_template_rendering_error(self):
        """Test fallback to global-only when module template fails to render."""
        mock_global_template = "Global: Valid"
        mock_module_prompt_obj = MagicMock()
        mock_module_prompt_obj.system_prompt = "{% invalid jinja %}"

        with patch("open_notebook.graphs.prompt.Path.exists", return_value=True):
            with patch("builtins.open", mock_open(read_data=mock_global_template)):
                with patch("open_notebook.graphs.prompt.ModulePrompt.get_by_notebook", new_callable=AsyncMock) as mock_get:
                    mock_get.return_value = mock_module_prompt_obj

                    # Should fall back to global-only
                    result = await assemble_system_prompt(
                        notebook_id="notebook:abc123"
                    )

                    assert "Global: Valid" in result
                    assert "MODULE-SPECIFIC" not in result

    @pytest.mark.asyncio
    async def test_assemble_with_default_values(self):
        """Test assembly with all optional parameters as None."""
        mock_global_template = "Global"

        with patch("open_notebook.graphs.prompt.Path.exists", return_value=True):
            with patch("builtins.open", mock_open(read_data=mock_global_template)):
                with patch("open_notebook.graphs.prompt.ModulePrompt.get_by_notebook", new_callable=AsyncMock) as mock_get:
                    mock_get.return_value = None

                    result = await assemble_system_prompt(notebook_id="notebook:abc123")

                    assert "Global" in result


class TestDefaultTemplate:
    """Test suite for default template helper."""

    @pytest.mark.asyncio
    async def test_get_default_template(self):
        """Test default template returns valid string with guidance."""
        template = await get_default_template()

        assert isinstance(template, str)
        assert len(template) > 100
        assert "Module-Specific Teaching Focus" in template
        assert "Available Template Variables" in template
        assert "learner_profile.role" in template
