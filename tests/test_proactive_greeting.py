"""
Story 4.2: Tests for Proactive Greeting Functionality

Tests LLM-based greeting generation, personalization, and fallback behavior.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from api.learner_chat_service import generate_proactive_greeting


@pytest.mark.asyncio
async def test_greeting_calls_llm_with_learner_context():
    """Test that greeting sends learner profile and objectives to LLM."""
    notebook_id = "notebook:test-123"
    learner_profile = {
        "role": "Data Analyst",
        "ai_familiarity": "beginner",
        "job_description": "Analyzing sales data",
    }
    mock_notebook = MagicMock()
    mock_notebook.name = "Introduction to Machine Learning"

    mock_obj = MagicMock()
    mock_obj.text = "Understand supervised learning"

    with patch(
        "api.learner_chat_service.LearningObjective.get_for_notebook",
        new_callable=AsyncMock,
        return_value=[mock_obj],
    ):
        with patch("api.learner_chat_service.provision_langchain_model") as mock_provision:
            mock_llm = AsyncMock()
            mock_llm.ainvoke = AsyncMock(
                return_value=MagicMock(
                    content="Welcome Data Analyst! Let's explore Introduction to Machine Learning together."
                )
            )
            mock_provision.return_value = mock_llm

            greeting = await generate_proactive_greeting(
                notebook_id=notebook_id,
                learner_profile=learner_profile,
                notebook=mock_notebook,
            )

    # Assert LLM was called
    mock_llm.ainvoke.assert_called_once()
    prompt_sent = mock_llm.ainvoke.call_args[0][0]

    # Assert prompt includes learner context
    assert "Data Analyst" in prompt_sent
    assert "beginner" in prompt_sent
    assert "Analyzing sales data" in prompt_sent
    assert "Introduction to Machine Learning" in prompt_sent
    assert "Understand supervised learning" in prompt_sent

    # Assert greeting is the LLM response
    assert "Welcome Data Analyst" in greeting


@pytest.mark.asyncio
async def test_greeting_includes_language_instruction_for_french():
    """Test that non-English language adds instruction to prompt."""
    learner_profile = {
        "role": "Analyste",
        "ai_familiarity": "intermediate",
        "job_description": "Analyse de données",
    }
    mock_notebook = MagicMock()
    mock_notebook.name = "Module IA"

    with patch(
        "api.learner_chat_service.LearningObjective.get_for_notebook",
        new_callable=AsyncMock,
        return_value=[],
    ):
        with patch("api.learner_chat_service.provision_langchain_model") as mock_provision:
            mock_llm = AsyncMock()
            mock_llm.ainvoke = AsyncMock(
                return_value=MagicMock(content="Bonjour ! Bienvenue dans Module IA.")
            )
            mock_provision.return_value = mock_llm

            greeting = await generate_proactive_greeting(
                notebook_id="notebook:test",
                learner_profile=learner_profile,
                notebook=mock_notebook,
                language="fr-FR",
            )

    # Assert language instruction was in the prompt
    prompt_sent = mock_llm.ainvoke.call_args[0][0]
    assert "French" in prompt_sent
    assert "MUST write the entire greeting" in prompt_sent

    assert len(greeting) > 0


@pytest.mark.asyncio
async def test_greeting_no_language_instruction_for_english():
    """Test that English (default) does not add language instruction."""
    learner_profile = {"role": "Student", "ai_familiarity": "beginner", "job_description": ""}
    mock_notebook = MagicMock()
    mock_notebook.name = "Test Module"

    with patch(
        "api.learner_chat_service.LearningObjective.get_for_notebook",
        new_callable=AsyncMock,
        return_value=[],
    ):
        with patch("api.learner_chat_service.provision_langchain_model") as mock_provision:
            mock_llm = AsyncMock()
            mock_llm.ainvoke = AsyncMock(
                return_value=MagicMock(content="Hello! Welcome to Test Module.")
            )
            mock_provision.return_value = mock_llm

            await generate_proactive_greeting(
                notebook_id="notebook:test",
                learner_profile=learner_profile,
                notebook=mock_notebook,
                language="en-US",
            )

    prompt_sent = mock_llm.ainvoke.call_args[0][0]
    assert "MUST write the entire greeting" not in prompt_sent


@pytest.mark.asyncio
async def test_greeting_handles_no_objectives():
    """Test greeting generation when no learning objectives exist."""
    learner_profile = {"role": "Student", "ai_familiarity": "beginner", "job_description": ""}
    mock_notebook = MagicMock()
    mock_notebook.name = "Test Module"

    with patch(
        "api.learner_chat_service.LearningObjective.get_for_notebook",
        new_callable=AsyncMock,
        return_value=[],
    ):
        with patch("api.learner_chat_service.provision_langchain_model") as mock_provision:
            mock_llm = AsyncMock()
            mock_llm.ainvoke = AsyncMock(
                return_value=MagicMock(content="Welcome! Let's explore this module.")
            )
            mock_provision.return_value = mock_llm

            greeting = await generate_proactive_greeting(
                notebook_id="notebook:test",
                learner_profile=learner_profile,
                notebook=mock_notebook,
            )

    # Prompt should contain fallback text for no objectives
    prompt_sent = mock_llm.ainvoke.call_args[0][0]
    assert "No specific objectives defined yet" in prompt_sent
    assert len(greeting) > 0


@pytest.mark.asyncio
async def test_greeting_fallback_on_llm_failure():
    """Test that greeting generation falls back gracefully if LLM fails."""
    learner_profile = {"role": "Engineer", "ai_familiarity": "intermediate", "job_description": ""}
    mock_notebook = MagicMock()
    mock_notebook.name = "Test Module"

    with patch(
        "api.learner_chat_service.LearningObjective.get_for_notebook",
        new_callable=AsyncMock,
        return_value=[MagicMock(text="Test Objective")],
    ):
        with patch("api.learner_chat_service.provision_langchain_model") as mock_provision:
            mock_provision.side_effect = Exception("LLM unavailable")

            greeting = await generate_proactive_greeting(
                notebook_id="notebook:test",
                learner_profile=learner_profile,
                notebook=mock_notebook,
            )

    # Should return fallback greeting
    assert "Test Module" in greeting
    assert len(greeting) > 0


@pytest.mark.asyncio
async def test_greeting_fallback_on_llm_failure_french():
    """Test French fallback when LLM fails."""
    learner_profile = {"role": "Ingénieur", "ai_familiarity": "intermediate", "job_description": ""}
    mock_notebook = MagicMock()
    mock_notebook.name = "Module Test"

    with patch(
        "api.learner_chat_service.LearningObjective.get_for_notebook",
        new_callable=AsyncMock,
        return_value=[],
    ):
        with patch("api.learner_chat_service.provision_langchain_model") as mock_provision:
            mock_provision.side_effect = Exception("LLM unavailable")

            greeting = await generate_proactive_greeting(
                notebook_id="notebook:test",
                learner_profile=learner_profile,
                notebook=mock_notebook,
                language="fr-FR",
            )

    # Should return French fallback
    assert "Bonjour" in greeting
    assert "Module Test" in greeting


@pytest.mark.asyncio
async def test_greeting_handles_missing_profile_fields():
    """Test greeting generation with minimal learner profile."""
    learner_profile = {
        "role": "Student",
        "ai_familiarity": "beginner",
        # job_description intentionally missing
    }
    mock_notebook = MagicMock()
    mock_notebook.name = "Intro Course"

    with patch(
        "api.learner_chat_service.LearningObjective.get_for_notebook",
        new_callable=AsyncMock,
        return_value=[MagicMock(text="Learn basics")],
    ):
        with patch("api.learner_chat_service.provision_langchain_model") as mock_provision:
            mock_llm = AsyncMock()
            mock_llm.ainvoke = AsyncMock(
                return_value=MagicMock(content="Hello Student! Welcome to Intro Course.")
            )
            mock_provision.return_value = mock_llm

            greeting = await generate_proactive_greeting(
                notebook_id="notebook:test",
                learner_profile=learner_profile,
                notebook=mock_notebook,
            )

    # Should not crash, should use N/A for missing job_description
    prompt_sent = mock_llm.ainvoke.call_args[0][0]
    assert "N/A" in prompt_sent
    assert len(greeting) > 0
