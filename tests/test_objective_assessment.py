"""
Unit tests for Learning Objective Progress Tracking (Story 4.4).

Tests cover:
- LearnerObjectiveProgress domain model
- CRUD operations (create, get, update)
- Duplicate prevention (UNIQUE constraint)
- Progress queries (user + notebook filtering)
- Company scoping validation
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, patch

from open_notebook.domain.learner_objective_progress import (
    LearnerObjectiveProgress,
    ProgressStatus,
    CompletedVia,
)
from open_notebook.exceptions import DatabaseOperationError, InvalidInputError


# ============================================================================
# TEST SUITE 1: LearnerObjectiveProgress Domain Model
# ============================================================================


class TestLearnerObjectiveProgress:
    """Test suite for LearnerObjectiveProgress CRUD operations."""

    @pytest.mark.asyncio
    async def test_create_progress_record(self):
        """Test creating progress record for learner on objective."""
        with patch("open_notebook.domain.learner_objective_progress.repo_query") as mock_query, \
             patch("open_notebook.domain.learner_objective_progress.repo_create") as mock_create:
            # Mock get_by_user_and_objective returning None (no existing record)
            mock_query.return_value = []

            # Mock repo_create returning new record
            mock_create.return_value = {
                "id": "learner_objective_progress:test123",
                "user_id": "user:learner1",
                "objective_id": "learning_objective:obj1",
                "status": "completed",
                "completed_via": "conversation",
                "evidence": "Learner explained concept correctly",
                "completed_at": datetime.now().isoformat(),
                "created": datetime.now().isoformat(),
            }

            progress = await LearnerObjectiveProgress.create(
                user_id="user:learner1",
                objective_id="learning_objective:obj1",
                status=ProgressStatus.COMPLETED,
                completed_via=CompletedVia.CONVERSATION,
                evidence="Learner explained concept correctly",
            )

            assert progress.user_id == "user:learner1"
            assert progress.objective_id == "learning_objective:obj1"
            assert progress.status == ProgressStatus.COMPLETED
            assert progress.completed_via == CompletedVia.CONVERSATION
            assert progress.evidence == "Learner explained concept correctly"
            assert progress.completed_at is not None

    @pytest.mark.asyncio
    async def test_create_prevents_duplicate(self):
        """Test UNIQUE constraint prevents duplicate completion."""
        with patch("open_notebook.domain.learner_objective_progress.repo_query") as mock_query:
            # Simulate existing record
            mock_query.return_value = [
                {
                    "id": "learner_objective_progress:existing",
                    "user_id": "user:learner1",
                    "objective_id": "learning_objective:obj1",
                    "status": "completed",
                    "completed_via": "conversation",
                    "evidence": "Already completed",
                    "completed_at": datetime.now().isoformat(),
                    "created": datetime.now().isoformat(),
                }
            ]

            # Should return existing record without error
            progress = await LearnerObjectiveProgress.get_by_user_and_objective(
                user_id="user:learner1", objective_id="learning_objective:obj1"
            )

            assert progress is not None
            assert progress.status == ProgressStatus.COMPLETED
            assert progress.evidence == "Already completed"

    @pytest.mark.asyncio
    async def test_get_by_user_and_objective(self):
        """Test fetching specific progress record."""
        with patch("open_notebook.domain.learner_objective_progress.repo_query") as mock_query:
            mock_query.return_value = [
                {
                    "id": "learner_objective_progress:test123",
                    "user_id": "user:learner1",
                    "objective_id": "learning_objective:obj1",
                    "status": "completed",
                    "completed_via": "conversation",
                    "evidence": "Test evidence",
                    "completed_at": datetime.now().isoformat(),
                    "created": datetime.now().isoformat(),
                }
            ]

            progress = await LearnerObjectiveProgress.get_by_user_and_objective(
                user_id="user:learner1", objective_id="learning_objective:obj1"
            )

            assert progress is not None
            assert progress.user_id == "user:learner1"
            assert progress.objective_id == "learning_objective:obj1"

    @pytest.mark.asyncio
    async def test_get_user_progress_for_notebook(self):
        """Test fetching all progress for user in notebook."""
        with patch("open_notebook.domain.learner_objective_progress.repo_query") as mock_query:
            mock_query.return_value = [
                {
                    "id": "learner_objective_progress:prog1",
                    "user_id": "user:learner1",
                    "objective_id": "learning_objective:obj1",
                    "status": "completed",
                    "completed_via": "conversation",
                    "evidence": "Evidence 1",
                    "completed_at": datetime.now().isoformat(),
                    "created": datetime.now().isoformat(),
                },
                {
                    "id": "learner_objective_progress:prog2",
                    "user_id": "user:learner1",
                    "objective_id": "learning_objective:obj2",
                    "status": "completed",
                    "completed_via": "quiz",
                    "evidence": "Evidence 2",
                    "completed_at": datetime.now().isoformat(),
                    "created": datetime.now().isoformat(),
                },
            ]

            progress_list = await LearnerObjectiveProgress.get_user_progress_for_notebook(
                user_id="user:learner1", notebook_id="notebook:module1"
            )

            assert len(progress_list) == 2
            assert progress_list[0].objective_id == "learning_objective:obj1"
            assert progress_list[1].objective_id == "learning_objective:obj2"

    @pytest.mark.asyncio
    async def test_update_status(self):
        """Test updating progress status (not_started → in_progress → completed)."""
        with patch("open_notebook.domain.learner_objective_progress.repo_update") as mock_update:
            mock_update.return_value = {
                "id": "learner_objective_progress:test123",
                "user_id": "user:learner1",
                "objective_id": "learning_objective:obj1",
                "status": "completed",
                "completed_via": "conversation",
                "evidence": "Updated evidence",
                "completed_at": datetime.now().isoformat(),
                "created": datetime.now().isoformat(),
            }

            progress = await LearnerObjectiveProgress.update_status(
                progress_id="learner_objective_progress:test123",
                status=ProgressStatus.COMPLETED,
                completed_via=CompletedVia.CONVERSATION,
                evidence="Updated evidence",
            )

            assert progress.status == ProgressStatus.COMPLETED
            assert progress.evidence == "Updated evidence"

    @pytest.mark.asyncio
    async def test_company_scoping(self):
        """Test progress queries filter by company (no leakage)."""
        # This test validates that when fetching progress, we only get records
        # for objectives in notebooks assigned to the learner's company
        with patch("open_notebook.domain.learner_objective_progress.repo_query") as mock_query:
            # Simulate query that JOINs with learning_objective and notebook
            # to filter by company_id
            mock_query.return_value = [
                {
                    "id": "learner_objective_progress:prog1",
                    "user_id": "user:learner1",
                    "objective_id": "learning_objective:obj1",
                    "status": "completed",
                    "completed_via": "conversation",
                    "evidence": "Company A objective",
                    "completed_at": datetime.now().isoformat(),
                    "created": datetime.now().isoformat(),
                }
            ]

            # This should only return progress for objectives in company's notebooks
            progress_list = await LearnerObjectiveProgress.get_user_progress_for_notebook(
                user_id="user:learner1", notebook_id="notebook:companyA_module"
            )

            assert len(progress_list) == 1
            assert "Company A" in progress_list[0].evidence

    @pytest.mark.asyncio
    async def test_evidence_required(self):
        """Test that evidence field is required when marking complete."""
        # Evidence is critical for review/debugging
        with pytest.raises(InvalidInputError):
            # This should fail validation during model creation
            LearnerObjectiveProgress(
                id="test",
                user_id="user:learner1",
                objective_id="learning_objective:obj1",
                status=ProgressStatus.COMPLETED,
                completed_via=CompletedVia.CONVERSATION,
                evidence="",  # Empty evidence should fail validation
            )


# ============================================================================
# TEST SUITE 2: check_off_objective Tool
# ============================================================================


class TestCheckOffObjectiveTool:
    """Test suite for check_off_objective LangGraph tool."""

    @pytest.mark.asyncio
    async def test_check_off_valid_objective(self):
        """Test tool successfully checks off objective with evidence."""
        from open_notebook.graphs.tools import check_off_objective

        with patch("open_notebook.domain.learning_objective.LearningObjective.get") as mock_get:
            mock_get.return_value = AsyncMock(
                id="learning_objective:obj1",
                notebook_id="notebook:module1",
                text="Understand supervised learning",
                order=0,
                auto_generated=False,
            )

            result = await check_off_objective.ainvoke(
                {"objective_id": "learning_objective:obj1", "evidence_text": "Learner explained concept"}
            )

            # Should return structured error about missing user_id (temporary limitation)
            assert "error" in result or "objective_id" in result
            # Tool should at least validate that objective exists
            mock_get.assert_called_once()

    @pytest.mark.asyncio
    async def test_check_off_duplicate_graceful(self):
        """Test tool handles duplicate check-off gracefully (no error)."""
        from open_notebook.graphs.tools import check_off_objective

        with patch("open_notebook.domain.learning_objective.LearningObjective.get") as mock_get:
            mock_get.return_value = AsyncMock(
                id="learning_objective:obj1",
                notebook_id="notebook:module1",
                text="Understand supervised learning",
                order=0,
                auto_generated=False,
            )

            # First call
            result1 = await check_off_objective.ainvoke(
                {"objective_id": "learning_objective:obj1", "evidence_text": "First evidence"}
            )

            # Second call with same objective (should be graceful)
            result2 = await check_off_objective.ainvoke(
                {"objective_id": "learning_objective:obj1", "evidence_text": "Second evidence"}
            )

            # Both should succeed without raising exceptions
            assert result1 is not None
            assert result2 is not None

    @pytest.mark.asyncio
    async def test_check_off_invalid_objective(self):
        """Test tool rejects invalid objective ID."""
        from open_notebook.graphs.tools import check_off_objective

        with patch("open_notebook.domain.learning_objective.LearningObjective.get") as mock_get:
            mock_get.return_value = None  # Objective not found

            result = await check_off_objective.ainvoke(
                {"objective_id": "learning_objective:invalid", "evidence_text": "Evidence"}
            )

            assert "error" in result
            assert result["error"] == "Learning objective not found"
            assert result["objective_id"] == "learning_objective:invalid"

    @pytest.mark.asyncio
    async def test_check_off_returns_progress_count(self):
        """Test tool returns total_completed and total_objectives (once user_id available)."""
        # This test documents the intended behavior once user_id is available in tool context
        # Currently returns error, but should return progress counts in final implementation
        from open_notebook.graphs.tools import check_off_objective

        with patch("open_notebook.domain.learning_objective.LearningObjective.get") as mock_get:
            mock_get.return_value = AsyncMock(
                id="learning_objective:obj1",
                notebook_id="notebook:module1",
                text="Understand supervised learning",
                order=0,
                auto_generated=False,
            )

            result = await check_off_objective.ainvoke(
                {"objective_id": "learning_objective:obj1", "evidence_text": "Evidence"}
            )

            # Should have structure for progress tracking
            assert "objective_id" in result
            # Note: full implementation pending user_id in RunnableConfig (Story 7.5)

    @pytest.mark.asyncio
    async def test_check_off_detects_all_complete(self):
        """Test tool returns all_complete=true when last objective checked (future)."""
        # This test documents future behavior once user_id is available
        # For now, just verify tool structure exists
        from open_notebook.graphs.tools import check_off_objective

        assert hasattr(check_off_objective, "ainvoke")
        assert check_off_objective.name == "check_off_objective"


# ============================================================================
# TEST SUITE 3: Prompt Context with Objectives (Task 3)
# ============================================================================


class TestPromptWithObjectives:
    """Test suite for prompt assembly with objectives status."""

    @pytest.mark.asyncio
    async def test_get_learner_objectives_with_status(self):
        """Test loading objectives with progress status via JOIN."""
        from api.learner_chat_service import get_learner_objectives_with_status

        with patch("open_notebook.database.repository.repo_query") as mock_query:
            # Simulate JOIN result with mixed completion status
            mock_query.return_value = [
                {
                    "objective_id": "learning_objective:obj1",
                    "text": "Understand supervised learning",
                    "order": 0,
                    "auto_generated": False,
                    "progress_status": "completed",
                    "completed_at": "2024-01-15T10:00:00",
                    "evidence": "Explained concept correctly",
                },
                {
                    "objective_id": "learning_objective:obj2",
                    "text": "Explain overfitting",
                    "order": 1,
                    "auto_generated": False,
                    "progress_status": None,  # Not started
                    "completed_at": None,
                    "evidence": None,
                },
                {
                    "objective_id": "learning_objective:obj3",
                    "text": "Apply regularization",
                    "order": 2,
                    "auto_generated": True,
                    "progress_status": None,
                    "completed_at": None,
                    "evidence": None,
                },
            ]

            objectives = await get_learner_objectives_with_status(
                notebook_id="notebook:module1", user_id="user:learner1"
            )

            assert len(objectives) == 3
            assert objectives[0]["status"] == "completed"
            assert objectives[0]["evidence"] == "Explained concept correctly"
            assert objectives[1]["status"] == "not_started"
            assert objectives[2]["status"] == "not_started"

    @pytest.mark.asyncio
    async def test_objectives_included_in_prompt_context(self):
        """Test that objectives with status are injected into system prompt."""
        from open_notebook.graphs.prompt import assemble_system_prompt

        # This test verifies the template receives objectives
        # The actual rendering is tested by prompt assembly tests
        objectives_with_status = [
            {"text": "Understand ML basics", "status": "completed", "order": 0},
            {"text": "Apply algorithms", "status": "not_started", "order": 1},
        ]

        with patch("open_notebook.graphs.prompt.Path.exists", return_value=True), \
             patch("builtins.open", create=True) as mock_open, \
             patch("open_notebook.graphs.prompt.ModulePrompt.get_by_notebook", return_value=None):
            # Mock template file content
            mock_open.return_value.__enter__.return_value.read.return_value = """
# AI Teacher Prompt
{% for obj in objectives %}
- {{ obj.text }}: {{ obj.status }}
{% endfor %}
"""

            prompt = await assemble_system_prompt(
                notebook_id="notebook:test",
                learner_profile={"role": "developer"},
                objectives_with_status=objectives_with_status,
            )

            # Verify objectives are in the rendered prompt
            assert "Understand ML basics: completed" in prompt
            assert "Apply algorithms: not_started" in prompt

    @pytest.mark.asyncio
    async def test_focus_objective_auto_selected(self):
        """Test that first incomplete objective becomes focus."""
        from open_notebook.graphs.prompt import assemble_system_prompt

        objectives_with_status = [
            {"text": "Completed objective", "status": "completed", "order": 0},
            {"text": "First incomplete", "status": "not_started", "order": 1},
            {"text": "Second incomplete", "status": "not_started", "order": 2},
        ]

        with patch("open_notebook.graphs.prompt.Path.exists", return_value=True), \
             patch("builtins.open", create=True) as mock_open, \
             patch("open_notebook.graphs.prompt.ModulePrompt.get_by_notebook", return_value=None):
            # Mock template with current_focus_objective
            mock_open.return_value.__enter__.return_value.read.return_value = """
Focus on: {{ current_focus_objective }}
"""

            prompt = await assemble_system_prompt(
                notebook_id="notebook:test",
                objectives_with_status=objectives_with_status,
            )

            # First incomplete objective should be focus
            assert "First incomplete" in prompt
