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
    async def test_assemble_handles_database_error_gracefully(self):
        """Test graceful fallback when ModulePrompt.get_by_notebook fails."""
        mock_global_template = "Global: Safe Fallback"

        with patch("open_notebook.graphs.prompt.Path.exists", return_value=True):
            with patch("builtins.open", mock_open(read_data=mock_global_template)):
                with patch("open_notebook.graphs.prompt.ModulePrompt.get_by_notebook", new_callable=AsyncMock) as mock_get:
                    # Simulate database connection error
                    mock_get.side_effect = Exception("Database connection timeout")

                    result = await assemble_system_prompt(
                        notebook_id="notebook:abc123"
                    )

                    # Should return global-only without crashing
                    assert "Global: Safe Fallback" in result
                    assert "MODULE-SPECIFIC" not in result

    @pytest.mark.asyncio
    async def test_assemble_handles_empty_module_prompt_string(self):
        """Test handling when module prompt system_prompt is empty string."""
        mock_global_template = "Global: Content"
        mock_module_prompt_obj = MagicMock()
        mock_module_prompt_obj.system_prompt = ""  # Empty string, not None

        with patch("open_notebook.graphs.prompt.Path.exists", return_value=True):
            with patch("builtins.open", mock_open(read_data=mock_global_template)):
                with patch("open_notebook.graphs.prompt.ModulePrompt.get_by_notebook", new_callable=AsyncMock) as mock_get:
                    mock_get.return_value = mock_module_prompt_obj

                    result = await assemble_system_prompt(
                        notebook_id="notebook:abc123"
                    )

                    # Empty string is falsy, should use global-only
                    assert "Global: Content" in result
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

    @pytest.mark.asyncio
    async def test_assemble_auto_selects_current_focus_objective(self):
        """Test current_focus_objective auto-selection (Story 4.2)."""
        mock_global_template = "Focus: {{ current_focus_objective }}"

        with patch("open_notebook.graphs.prompt.Path.exists", return_value=True):
            with patch("builtins.open", mock_open(read_data=mock_global_template)):
                with patch("open_notebook.graphs.prompt.ModulePrompt.get_by_notebook", new_callable=AsyncMock) as mock_get:
                    mock_get.return_value = None

                    objectives = [
                        {"text": "Objective 1", "status": "completed"},
                        {"text": "Objective 2", "status": "in_progress"},
                        {"text": "Objective 3", "status": "not_started"}
                    ]

                    result = await assemble_system_prompt(
                        notebook_id="notebook:abc123",
                        objectives_with_status=objectives,
                        current_focus_objective=None  # Should auto-select first incomplete
                    )

                    assert "Focus: Objective 2" in result

    @pytest.mark.asyncio
    async def test_assemble_all_objectives_completed_falls_back_to_first(self):
        """Test that when all objectives completed, focus falls back to first for review."""
        mock_global_template = "Focus: {{ current_focus_objective }}"

        with patch("open_notebook.graphs.prompt.Path.exists", return_value=True):
            with patch("builtins.open", mock_open(read_data=mock_global_template)):
                with patch("open_notebook.graphs.prompt.ModulePrompt.get_by_notebook", new_callable=AsyncMock) as mock_get:
                    mock_get.return_value = None

                    objectives = [
                        {"text": "Review Objective 1", "status": "completed"},
                        {"text": "Review Objective 2", "status": "completed"}
                    ]

                    result = await assemble_system_prompt(
                        notebook_id="notebook:abc123",
                        objectives_with_status=objectives,
                        current_focus_objective=None
                    )

                    assert "Focus: Review Objective 1" in result


    @pytest.mark.asyncio
    async def test_assemble_respects_token_budget(self):
        """Test assembled prompt stays under 2000 token limit (Story 4.2)."""
        import tiktoken
        enc = tiktoken.get_encoding("cl100k_base")

        mock_global_template = """
        You are a teacher. Profile: {{ learner_profile.role }}
        {% for obj in objectives %}
        Objective {{ loop.index }}: {{ obj.text }}
        {% endfor %}
        """

        with patch("open_notebook.graphs.prompt.Path.exists", return_value=True):
            with patch("builtins.open", mock_open(read_data=mock_global_template)):
                with patch("open_notebook.graphs.prompt.ModulePrompt.get_by_notebook", new_callable=AsyncMock) as mock_get:
                    mock_get.return_value = None

                    # Create moderate-sized input (10 objectives)
                    objectives = [
                        {"text": f"Understand concept {i} and its applications", "status": "not_started"}
                        for i in range(10)
                    ]

                    result = await assemble_system_prompt(
                        notebook_id="notebook:test",
                        learner_profile={"role": "Engineer", "ai_familiarity": "intermediate"},
                        objectives_with_status=objectives
                    )

                    token_count = len(enc.encode(result))
                    assert token_count < 2000, f"Prompt exceeded token budget: {token_count} tokens (limit: 2000)"


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
