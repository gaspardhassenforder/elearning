"""
Story 4.2: Tests for Proactive Greeting Functionality

Tests greeting generation, personalization, and first-visit detection.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from api.learner_chat_service import generate_proactive_greeting


@pytest.mark.asyncio
async def test_greeting_generation_with_beginner_learner():
    """Test greeting personalization for beginner AI familiarity."""
    # Arrange
    notebook_id = "notebook:test-123"
    learner_profile = {
        "role": "Data Analyst",
        "ai_familiarity": "beginner",
        "job_description": "Analyzing sales data"
    }
    mock_notebook = MagicMock()
    mock_notebook.title = "Introduction to Machine Learning"

    # Mock LearningObjective.list_by_notebook
    with patch('api.learner_chat_service.LearningObjective.list_by_notebook') as mock_objectives:
        mock_obj = MagicMock()
        mock_obj.text = "Understand supervised learning"
        mock_objectives.return_value = [mock_obj]

        # Mock LLM for opening question generation
        with patch('api.learner_chat_service.provision_langchain_model') as mock_model:
            mock_llm = AsyncMock()
            mock_llm.ainvoke = AsyncMock(return_value=MagicMock(
                content="What patterns do you notice in your sales data analysis?"
            ))
            mock_model.return_value = mock_llm

            # Act
            greeting = await generate_proactive_greeting(
                notebook_id=notebook_id,
                learner_profile=learner_profile,
                notebook=mock_notebook
            )

    # Assert
    assert "Data Analyst" in greeting
    assert "Introduction to Machine Learning" in greeting
    assert "AI is new to you" in greeting or "beginner" in greeting.lower()
    assert "Understand supervised learning" in greeting
    assert "?" in greeting  # Should ask an opening question


@pytest.mark.asyncio
async def test_greeting_generation_with_expert_learner():
    """Test greeting personalization for expert AI familiarity."""
    # Arrange
    notebook_id = "notebook:test-456"
    learner_profile = {
        "role": "Machine Learning Engineer",
        "ai_familiarity": "expert",
        "job_description": "Building ML models"
    }
    mock_notebook = MagicMock()
    mock_notebook.title = "Advanced Neural Networks"

    with patch('api.learner_chat_service.LearningObjective.list_by_notebook') as mock_objectives:
        mock_obj = MagicMock()
        mock_obj.text = "Understand transformers architecture"
        mock_objectives.return_value = [mock_obj]

        with patch('api.learner_chat_service.provision_langchain_model') as mock_model:
            mock_llm = AsyncMock()
            mock_llm.ainvoke = AsyncMock(return_value=MagicMock(
                content="How have you applied transformer architectures in your work?"
            ))
            mock_model.return_value = mock_llm

            # Act
            greeting = await generate_proactive_greeting(
                notebook_id=notebook_id,
                learner_profile=learner_profile,
                notebook=mock_notebook
            )

    # Assert
    assert "Machine Learning Engineer" in greeting
    assert "Advanced Neural Networks" in greeting
    assert "familiar with AI" in greeting or "expertise" in greeting.lower()
    assert "transformers architecture" in greeting


@pytest.mark.asyncio
async def test_greeting_generation_with_job_context():
    """Test that job context is referenced in greeting."""
    # Arrange
    learner_profile = {
        "role": "Product Manager",
        "ai_familiarity": "intermediate",
        "job_description": "Managing AI product features"
    }
    mock_notebook = MagicMock()
    mock_notebook.title = "AI for Product Managers"

    with patch('api.learner_chat_service.LearningObjective.list_by_notebook') as mock_objectives:
        mock_objectives.return_value = [MagicMock(text="Understand AI product lifecycle")]

        with patch('api.learner_chat_service.provision_langchain_model') as mock_model:
            mock_llm = AsyncMock()
            mock_llm.ainvoke = AsyncMock(return_value=MagicMock(
                content="How do you currently prioritize AI features?"
            ))
            mock_model.return_value = mock_llm

            # Act
            greeting = await generate_proactive_greeting(
                notebook_id="notebook:test",
                learner_profile=learner_profile,
                notebook=mock_notebook
            )

    # Assert
    assert "Managing AI product features" in greeting or "your work" in greeting.lower()


@pytest.mark.asyncio
async def test_greeting_generation_handles_no_objectives():
    """Test greeting generation when no learning objectives exist."""
    # Arrange
    learner_profile = {"role": "Student", "ai_familiarity": "beginner", "job_description": ""}
    mock_notebook = MagicMock()
    mock_notebook.title = "Test Module"

    with patch('api.learner_chat_service.LearningObjective.list_by_notebook') as mock_objectives:
        mock_objectives.return_value = []  # No objectives

        with patch('api.learner_chat_service.provision_langchain_model') as mock_model:
            mock_llm = AsyncMock()
            mock_llm.ainvoke = AsyncMock(return_value=MagicMock(
                content="What would you like to learn?"
            ))
            mock_model.return_value = mock_llm

            # Act
            greeting = await generate_proactive_greeting(
                notebook_id="notebook:test",
                learner_profile=learner_profile,
                notebook=mock_notebook
            )

    # Assert
    assert "Student" in greeting
    assert "Test Module" in greeting
    assert "exploring this module's content" in greeting  # Fallback objective text


@pytest.mark.asyncio
async def test_greeting_generation_fallback_on_llm_failure():
    """Test that greeting generation falls back gracefully if LLM fails."""
    # Arrange
    learner_profile = {"role": "Engineer", "ai_familiarity": "intermediate", "job_description": ""}
    mock_notebook = MagicMock()
    mock_notebook.title = "Test Module"

    with patch('api.learner_chat_service.LearningObjective.list_by_notebook') as mock_objectives:
        mock_objectives.return_value = [MagicMock(text="Test Objective")]

        with patch('api.learner_chat_service.provision_langchain_model') as mock_model:
            # Simulate LLM failure
            mock_model.side_effect = Exception("LLM unavailable")

            # Act
            greeting = await generate_proactive_greeting(
                notebook_id="notebook:test",
                learner_profile=learner_profile,
                notebook=mock_notebook
            )

    # Assert - Should still generate greeting using fallback
    assert "Engineer" in greeting
    assert "Test Module" in greeting
    assert len(greeting) > 0  # Not empty
