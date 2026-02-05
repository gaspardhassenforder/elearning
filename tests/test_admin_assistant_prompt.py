"""Tests for admin assistant prompt template."""

import pytest
from ai_prompter import Prompter


class TestAdminAssistantPrompt:
    """Test admin assistant Jinja2 prompt template rendering."""

    def test_prompt_renders_with_minimal_context(self):
        """Test prompt renders with minimal module context."""
        prompter = Prompter(prompt_template="admin_assistant_prompt")

        context = {
            "module_title": "Test Module",
            "documents": [],
            "objectives": [],
            "module_prompt": None
        }

        rendered = prompter.render(data=context)

        # Assert core prompt sections exist
        assert "AI assistant helping administrators" in rendered
        assert "YOUR ROLE:" in rendered
        assert "CURRENT MODULE CONTEXT:" in rendered
        assert "Module: Test Module" in rendered
        assert "GUIDELINES FOR YOUR RESPONSES:" in rendered

    def test_prompt_includes_documents(self):
        """Test prompt includes uploaded documents."""
        prompter = Prompter(prompt_template="admin_assistant_prompt")

        context = {
            "module_title": "AI in Logistics",
            "documents": [
                {"title": "Introduction to AI"},
                {"title": "Supply Chain Overview"}
            ],
            "objectives": [],
            "module_prompt": None
        }

        rendered = prompter.render(data=context)

        assert "Uploaded Documents (2):" in rendered
        assert "Introduction to AI" in rendered
        assert "Supply Chain Overview" in rendered

    def test_prompt_includes_learning_objectives(self):
        """Test prompt includes learning objectives."""
        prompter = Prompter(prompt_template="admin_assistant_prompt")

        context = {
            "module_title": "AI Basics",
            "documents": [],
            "objectives": [
                {"text": "Understand AI fundamentals"},
                {"text": "Apply ML algorithms"}
            ],
            "module_prompt": None
        }

        rendered = prompter.render(data=context)

        assert "Learning Objectives (2):" in rendered
        assert "Understand AI fundamentals" in rendered
        assert "Apply ML algorithms" in rendered

    def test_prompt_includes_module_prompt(self):
        """Test prompt includes current AI teacher prompt."""
        prompter = Prompter(prompt_template="admin_assistant_prompt")

        context = {
            "module_title": "Logistics AI",
            "documents": [],
            "objectives": [],
            "module_prompt": "Focus on supply chain optimization and real-world applications."
        }

        rendered = prompter.render(data=context)

        assert "Current AI Teacher Prompt:" in rendered
        assert "Focus on supply chain optimization" in rendered

    def test_prompt_handles_empty_context(self):
        """Test prompt handles all empty/None values gracefully."""
        prompter = Prompter(prompt_template="admin_assistant_prompt")

        context = {
            "module_title": None,
            "documents": None,
            "objectives": None,
            "module_prompt": None
        }

        # Should not crash; conditional blocks should handle None
        rendered = prompter.render(data=context)

        assert "AI assistant helping administrators" in rendered
        assert "YOUR ROLE:" in rendered

    def test_prompt_has_distinct_personality_from_learner(self):
        """Test admin assistant has distinct personality from learner AI teacher."""
        prompter = Prompter(prompt_template="admin_assistant_prompt")

        context = {
            "module_title": "Test",
            "documents": [],
            "objectives": [],
            "module_prompt": None
        }

        rendered = prompter.render(data=context)

        # Admin-specific language
        assert "administrators" in rendered.lower()
        assert "module creation" in rendered.lower()
        assert "practical guidance" in rendered.lower()

        # Should NOT have learner-specific language
        assert "teach" not in rendered.lower() or "teaching" in rendered.lower()  # "teaching" OK in admin context
        assert "student" not in rendered.lower()
        assert "learn" not in rendered.lower() or "learning objectives" in rendered.lower()  # "learning objectives" OK
