"""Tests for Story 4.5: Adaptive Teaching & Fast-Track for Advanced Learners

Tests the prompt assembly with learner AI familiarity levels and adaptive teaching instructions.
"""

import pytest
from pathlib import Path

from open_notebook.graphs.prompt import assemble_system_prompt


class TestAdaptivePromptAssembly:
    """Test prompt assembly includes adaptive teaching context based on learner familiarity."""

    @pytest.mark.asyncio
    async def test_prompt_includes_ai_familiarity_high(self):
        """Test prompt context includes learner.profile.ai_familiarity for high familiarity."""
        learner_profile = {
            "role": "Data Scientist",
            "ai_familiarity": "high",
            "job": "ML Engineer at TechCorp"
        }

        objectives_with_status = [
            {"text": "Understand supervised learning", "status": "incomplete"},
            {"text": "Explain regularization", "status": "incomplete"}
        ]

        prompt = await assemble_system_prompt(
            notebook_id="notebook:test123",
            learner_profile=learner_profile,
            objectives_with_status=objectives_with_status
        )

        # Verify prompt includes AI familiarity level
        assert ("AI Familiarity" in prompt and "high" in prompt) or "ai_familiarity" in prompt.lower()
        # Verify adaptive strategy section exists
        assert "Adaptive Teaching Strategy" in prompt or "ADAPTIVE TEACHING" in prompt

    @pytest.mark.asyncio
    async def test_high_familiarity_prompt_instructions(self):
        """Test high/expert familiarity triggers fast-track instructions."""
        learner_profile = {
            "role": "Senior ML Engineer",
            "ai_familiarity": "expert",
            "job": "AI Researcher"
        }

        objectives_with_status = [
            {"text": "Understand neural networks", "status": "incomplete"}
        ]

        prompt = await assemble_system_prompt(
            notebook_id="notebook:test456",
            learner_profile=learner_profile,
            objectives_with_status=objectives_with_status
        )

        # Verify fast-track instructions present
        assert "expert" in prompt.lower() or "high" in prompt.lower()
        # Verify multiple objective check-off guidance
        assert "multiple objectives" in prompt.lower() or "multiple objective" in prompt.lower()
        # Verify rapid assessment mentioned
        assert "rapid" in prompt.lower() or "quick" in prompt.lower() or "fast" in prompt.lower()

    @pytest.mark.asyncio
    async def test_low_familiarity_prompt_instructions(self):
        """Test low/beginner familiarity triggers patient teaching instructions."""
        learner_profile = {
            "role": "Product Manager",
            "ai_familiarity": "beginner",
            "job": "PM at StartupCo"
        }

        objectives_with_status = [
            {"text": "Understand AI basics", "status": "incomplete"}
        ]

        prompt = await assemble_system_prompt(
            notebook_id="notebook:test789",
            learner_profile=learner_profile,
            objectives_with_status=objectives_with_status
        )

        # Verify patient teaching instructions present
        assert "beginner" in prompt.lower() or "patient" in prompt.lower()
        # Verify detailed explanations guidance
        assert "detailed" in prompt.lower() or "step by step" in prompt.lower()
        # Verify single objective focus
        assert "one objective" in prompt.lower() or "single objective" in prompt.lower()

    @pytest.mark.asyncio
    async def test_adaptive_strategy_section_rendered(self):
        """Test Adaptive Teaching Strategy section appears in final prompt."""
        learner_profile = {
            "role": "Developer",
            "ai_familiarity": "intermediate",
            "job": "Full Stack Developer"
        }

        objectives_with_status = [
            {"text": "Learn Python basics", "status": "incomplete"}
        ]

        prompt = await assemble_system_prompt(
            notebook_id="notebook:test_adaptive",
            learner_profile=learner_profile,
            objectives_with_status=objectives_with_status
        )

        # Verify adaptive teaching strategy section exists
        assert "Adaptive Teaching Strategy" in prompt or "adaptive" in prompt.lower()
        # Verify intermediate/balanced approach mentioned
        assert "intermediate" in prompt.lower() or "balanced" in prompt.lower()

    @pytest.mark.asyncio
    async def test_knowledge_gap_detection_instructions(self):
        """Test prompt includes knowledge gap detection guidance for ALL learners."""
        learner_profile = {
            "role": "Analyst",
            "ai_familiarity": "high",
            "job": "Business Analyst"
        }

        objectives_with_status = [
            {"text": "Understand data analysis", "status": "incomplete"}
        ]

        prompt = await assemble_system_prompt(
            notebook_id="notebook:test_gaps",
            learner_profile=learner_profile,
            objectives_with_status=objectives_with_status
        )

        # Verify knowledge gap detection instructions present
        assert "knowledge gap" in prompt.lower() or "gap detected" in prompt.lower()
        # Verify guidance on responding to gaps
        assert "deeper" in prompt.lower() or "slow down" in prompt.lower()


class TestMultipleObjectiveCheckOffGuidance:
    """Test prompt includes guidance for multiple objective check-offs."""

    @pytest.mark.asyncio
    async def test_multiple_objectives_guidance_for_advanced(self):
        """Test prompt guides AI to check off multiple objectives for advanced learners."""
        learner_profile = {
            "role": "AI Researcher",
            "ai_familiarity": "expert",
            "job": "Research Scientist"
        }

        objectives_with_status = [
            {"text": "Objective 1", "status": "incomplete"},
            {"text": "Objective 2", "status": "incomplete"},
            {"text": "Objective 3", "status": "incomplete"}
        ]

        prompt = await assemble_system_prompt(
            notebook_id="notebook:test_multi",
            learner_profile=learner_profile,
            objectives_with_status=objectives_with_status
        )

        # Verify multiple objective check-off guidance
        assert "multiple objectives" in prompt.lower() or "several objectives" in prompt.lower()
        # Verify comprehensive understanding condition
        assert "comprehensive" in prompt.lower() or "demonstrates understanding" in prompt.lower()

    @pytest.mark.asyncio
    async def test_evidence_requirement_mentioned(self):
        """Test prompt emphasizes evidence requirement for each objective."""
        learner_profile = {
            "role": "Developer",
            "ai_familiarity": "intermediate"
        }

        objectives_with_status = [
            {"text": "Test objective", "status": "incomplete"}
        ]

        prompt = await assemble_system_prompt(
            notebook_id="notebook:test_evidence",
            learner_profile=learner_profile,
            objectives_with_status=objectives_with_status
        )

        # Verify evidence requirement mentioned
        assert "evidence" in prompt.lower()


class TestModuleSuggestions:
    """Test module suggestions on completion."""

    @pytest.mark.asyncio
    async def test_suggestions_included_when_all_complete(self):
        """Test suggested_modules included when all_complete == true."""
        from open_notebook.graphs.tools import _fetch_suggested_modules
        from unittest.mock import AsyncMock, patch

        # Mock User.get to return user with company_id
        mock_user = AsyncMock()
        mock_user.company_id = "company:test123"

        # Mock repo_query to return 2 suggested modules
        mock_suggestions = [
            {"id": "notebook:module1", "title": "Advanced ML", "description": "Deep learning basics"},
            {"id": "notebook:module2", "title": "MLOps", "description": "Production ML systems"}
        ]

        with patch('open_notebook.graphs.tools.User.get', return_value=mock_user), \
             patch('open_notebook.graphs.tools.repo_query', return_value=mock_suggestions):

            result = await _fetch_suggested_modules(
                user_id="user:learner1",
                current_notebook_id="notebook:current"
            )

            # Verify returned structure
            assert len(result) == 2
            assert result[0]["id"] == "notebook:module1"
            assert result[0]["title"] == "Advanced ML"
            assert result[1]["id"] == "notebook:module2"
            assert "description" in result[0]

    @pytest.mark.asyncio
    async def test_suggestions_company_scoped(self):
        """Test suggestions filtered by learner's company."""
        from open_notebook.graphs.tools import _fetch_suggested_modules
        from unittest.mock import AsyncMock, patch

        # Mock User.get to return user with company_id
        mock_user = AsyncMock()
        mock_user.company_id = "company:acme"

        # Mock repo_query to verify company_id is passed correctly
        mock_repo_query = AsyncMock(return_value=[
            {"id": "notebook:acme_module", "title": "ACME Training", "description": "Company specific"}
        ])

        with patch('open_notebook.graphs.tools.User.get', return_value=mock_user), \
             patch('open_notebook.graphs.tools.repo_query', mock_repo_query):

            result = await _fetch_suggested_modules(
                user_id="user:alice",
                current_notebook_id="notebook:current"
            )

            # Verify repo_query was called with correct company_id
            mock_repo_query.assert_called_once()
            call_args = mock_repo_query.call_args
            assert call_args[0][1]["company_id"] == "company:acme"

            # Verify company-specific module returned
            assert len(result) == 1
            assert result[0]["id"] == "notebook:acme_module"

    @pytest.mark.asyncio
    async def test_no_suggestions_when_none_available(self):
        """Test suggested_modules = [] when no modules available."""
        from open_notebook.graphs.tools import _fetch_suggested_modules
        from unittest.mock import AsyncMock, patch

        # Mock User.get to return user with company_id
        mock_user = AsyncMock()
        mock_user.company_id = "company:startup"

        # Mock repo_query to return empty list (no modules available)
        with patch('open_notebook.graphs.tools.User.get', return_value=mock_user), \
             patch('open_notebook.graphs.tools.repo_query', return_value=[]):

            result = await _fetch_suggested_modules(
                user_id="user:bob",
                current_notebook_id="notebook:only_module"
            )

            # Verify empty list returned
            assert result == []
            assert isinstance(result, list)
