"""
Unit tests for quiz generation workflow.
"""

import os
import pytest
from unittest.mock import patch, AsyncMock, MagicMock

from open_notebook.graphs.quiz_generation import (
    generate_quiz,
    gather_sources,
    generate_questions,
    save_quiz,
    QuizGenerationState,
)


@pytest.fixture(autouse=True)
def setup_test_env():
    """Set up test environment variables."""
    os.environ.setdefault("SURREAL_URL", "ws://localhost:8000/rpc")
    os.environ.setdefault("SURREAL_USER", "root")
    os.environ.setdefault("SURREAL_PASSWORD", "root")
    os.environ.setdefault("SURREAL_NAMESPACE", "test")
    os.environ.setdefault("SURREAL_DATABASE", "test")


class TestGatherSources:
    """Test suite for source gathering step."""

    @pytest.mark.asyncio
    async def test_gather_sources_notebook_not_found(self):
        """Test that non-existent notebook returns error."""
        state: QuizGenerationState = {
            "notebook_id": "notebook:notfound",
            "topic": None,
            "num_questions": 5,
            "source_ids": None,
            "sources_content": "",
            "generated_questions": [],
            "quiz_id": None,
            "error": None,
            "status": "pending",
        }

        with patch("open_notebook.graphs.quiz_generation.Notebook.get") as mock_get, \
             patch("open_notebook.database.repository.repo_query") as mock_query:
            mock_get.return_value = None
            mock_query.return_value = []

            result = await gather_sources(state)
            assert result["status"] == "failed"
            assert "not found" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_gather_sources_no_sources(self):
        """Test that notebook with no sources returns error."""
        state: QuizGenerationState = {
            "notebook_id": "notebook:test123",
            "topic": None,
            "num_questions": 5,
            "source_ids": None,
            "sources_content": "",
            "generated_questions": [],
            "quiz_id": None,
            "error": None,
            "status": "pending",
        }

        mock_notebook = MagicMock()
        mock_notebook.id = "notebook:test123"

        with patch("open_notebook.graphs.quiz_generation.Notebook.get") as mock_get, \
             patch("open_notebook.database.repository.repo_query") as mock_query:
            mock_get.return_value = mock_notebook
            mock_query.return_value = []

            result = await gather_sources(state)
            assert result["status"] == "failed"
            assert "No sources found" in result["error"]

    @pytest.mark.asyncio
    async def test_gather_sources_success(self):
        """Test successful source gathering with full_text."""
        state: QuizGenerationState = {
            "notebook_id": "notebook:test123",
            "topic": None,
            "num_questions": 5,
            "source_ids": None,
            "sources_content": "",
            "generated_questions": [],
            "quiz_id": None,
            "error": None,
            "status": "pending",
        }

        mock_notebook = MagicMock()
        mock_notebook.id = "notebook:test123"

        mock_source_data = {
            "source": {
                "id": "source:1",
                "title": "Test Source",
                "full_text": "This is the full text content for testing.",
            }
        }

        with patch("open_notebook.graphs.quiz_generation.Notebook.get") as mock_get, \
             patch("open_notebook.database.repository.repo_query") as mock_query:
            mock_get.return_value = mock_notebook
            mock_query.return_value = [mock_source_data]

            result = await gather_sources(state)
            assert result["status"] == "generating"
            assert "sources_content" in result
            assert "Test Source" in result["sources_content"]
            assert "full text content" in result["sources_content"]


class TestGenerateQuestions:
    """Test suite for question generation step."""

    @pytest.mark.asyncio
    async def test_generate_questions_with_error_state(self):
        """Test that existing error state bypasses generation."""
        state: QuizGenerationState = {
            "notebook_id": "notebook:test123",
            "topic": None,
            "num_questions": 5,
            "source_ids": None,
            "sources_content": "Test content",
            "generated_questions": [],
            "quiz_id": None,
            "error": "Previous error",
            "status": "failed",
        }

        result = await generate_questions(state)
        assert result == {}

    @pytest.mark.asyncio
    async def test_generate_questions_success(self):
        """Test successful question generation."""
        state: QuizGenerationState = {
            "notebook_id": "notebook:test123",
            "topic": None,
            "num_questions": 2,
            "source_ids": None,
            "sources_content": "Test content for quiz generation.",
            "generated_questions": [],
            "quiz_id": None,
            "error": None,
            "status": "generating",
        }

        mock_response = MagicMock()
        mock_response.content = '[{"question": "What is this?", "options": ["A", "B", "C", "D"], "correct_answer": 0, "explanation": "A is correct"}]'

        mock_model = MagicMock()
        mock_model.ainvoke = AsyncMock(return_value=mock_response)

        with patch("open_notebook.graphs.quiz_generation.provision_langchain_model") as mock_provision, \
             patch("open_notebook.graphs.quiz_generation.Prompter") as mock_prompter:
            mock_provision.return_value = mock_model
            mock_prompter_instance = MagicMock()
            mock_prompter_instance.render.return_value = "Test prompt"
            mock_prompter.return_value = mock_prompter_instance

            result = await generate_questions(state)
            assert result["status"] == "saving"
            assert len(result["generated_questions"]) == 1


class TestSaveQuiz:
    """Test suite for quiz saving step."""

    @pytest.mark.asyncio
    async def test_save_quiz_success(self):
        """Test successful quiz saving."""
        state: QuizGenerationState = {
            "notebook_id": "notebook:test123",
            "topic": "Test Topic",
            "num_questions": 1,
            "source_ids": None,
            "sources_content": "Test content",
            "generated_questions": [
                {
                    "question": "What is this?",
                    "options": ["A", "B", "C", "D"],
                    "correct_answer": 0,
                    "explanation": "A is correct",
                }
            ],
            "quiz_id": None,
            "error": None,
            "status": "saving",
        }

        mock_quiz = MagicMock()
        mock_quiz.id = "quiz:test123"
        mock_quiz.title = "Quiz: Test Topic"
        mock_quiz.save = AsyncMock()

        with patch("open_notebook.graphs.quiz_generation.Quiz") as mock_quiz_class, \
             patch("open_notebook.graphs.quiz_generation.Artifact.create_for_artifact") as mock_artifact:
            mock_quiz_class.return_value = mock_quiz
            mock_artifact.return_value = MagicMock()

            result = await save_quiz(state)
            assert result["status"] == "completed"
            assert result["quiz_id"] == "quiz:test123"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
