"""Quiz generation workflow using LangGraph."""

import asyncio
import json
import re
from typing import List, Literal, Optional, TypedDict

from ai_prompter import Prompter
from loguru import logger

from open_notebook.ai.provision import provision_langchain_model
from open_notebook.domain.artifact import Artifact
from open_notebook.domain.notebook import Notebook
from open_notebook.domain.quiz import Quiz, QuizQuestion


class QuizGenerationState(TypedDict):
    """State for quiz generation workflow."""

    notebook_id: str
    topic: Optional[str]
    num_questions: int
    source_ids: Optional[List[str]]
    sources_content: str
    generated_questions: List[dict]
    quiz_id: Optional[str]
    error: Optional[str]
    status: Literal["pending", "gathering", "generating", "saving", "completed", "failed"]


async def gather_sources(state: QuizGenerationState) -> dict:
    """Gather relevant source content from the notebook."""
    logger.info(f"Gathering sources for notebook {state['notebook_id']}")

    try:
        notebook = await Notebook.get(state["notebook_id"])
        sources = await notebook.get_sources()

        if not sources:
            return {
                "error": "No sources found in notebook",
                "status": "failed",
            }

        # Filter by source_ids if specified
        if state.get("source_ids"):
            sources = [s for s in sources if s.id in state["source_ids"]]
            if not sources:
                return {
                    "error": "Specified sources not found",
                    "status": "failed",
                }

        # Combine source content with source titles for context
        content_parts = []
        for source in sources:
            if source.full_text:
                # Limit each source to prevent context overflow
                text = source.full_text[:8000] if len(source.full_text) > 8000 else source.full_text
                content_parts.append(f"## Source: {source.title or 'Untitled'}\n\n{text}")

        if not content_parts:
            return {
                "error": "No text content found in sources",
                "status": "failed",
            }

        combined_content = "\n\n---\n\n".join(content_parts)
        
        # Limit total content to prevent context overflow
        max_content_length = 30000
        if len(combined_content) > max_content_length:
            combined_content = combined_content[:max_content_length] + "\n\n[Content truncated...]"

        logger.info(f"Gathered {len(sources)} sources with {len(combined_content)} characters")

        return {
            "sources_content": combined_content,
            "status": "generating",
        }

    except Exception as e:
        logger.error(f"Error gathering sources: {e}")
        return {
            "error": f"Failed to gather sources: {str(e)}",
            "status": "failed",
        }


async def generate_questions(state: QuizGenerationState) -> dict:
    """Use LLM to generate quiz questions from source content."""
    if state.get("error"):
        return {}

    logger.info(f"Generating {state['num_questions']} quiz questions")

    try:
        # Prepare prompt data
        prompt_data = {
            "sources_content": state["sources_content"],
            "topic": state.get("topic"),
            "num_questions": state["num_questions"],
        }

        # Render prompt using Prompter
        prompter = Prompter(prompt_template="quiz/generate")
        prompt = prompter.render(data=prompt_data)

        # Get model for quiz generation
        model = await provision_langchain_model(
            content=prompt,
            model_id=None,
            default_type="default",
            max_tokens=4096,
        )

        # Generate questions
        response = await model.ainvoke(prompt)
        response_text = response.content if hasattr(response, "content") else str(response)

        # Parse JSON response
        questions = _parse_quiz_response(response_text)

        if not questions:
            return {
                "error": "Failed to parse quiz questions from LLM response",
                "status": "failed",
            }

        logger.info(f"Successfully generated {len(questions)} questions")

        return {
            "generated_questions": questions,
            "status": "saving",
        }

    except Exception as e:
        logger.error(f"Error generating questions: {e}")
        logger.exception(e)
        return {
            "error": f"Failed to generate questions: {str(e)}",
            "status": "failed",
        }


def _parse_quiz_response(response_text: str) -> List[dict]:
    """Parse LLM response to extract quiz questions."""
    # Try to find JSON in the response
    try:
        # First, try direct JSON parse
        return json.loads(response_text)
    except json.JSONDecodeError:
        pass

    # Try to extract JSON from markdown code blocks
    json_patterns = [
        r"```json\s*([\s\S]*?)\s*```",
        r"```\s*([\s\S]*?)\s*```",
        r"\[\s*\{[\s\S]*\}\s*\]",
    ]

    for pattern in json_patterns:
        match = re.search(pattern, response_text)
        if match:
            try:
                json_str = match.group(1) if "```" in pattern else match.group(0)
                return json.loads(json_str)
            except (json.JSONDecodeError, IndexError):
                continue

    logger.warning(f"Could not parse quiz response: {response_text[:500]}")
    return []


async def save_quiz(state: QuizGenerationState) -> dict:
    """Save generated quiz to database and create artifact tracker."""
    if state.get("error"):
        return {}

    logger.info(f"Saving quiz with {len(state['generated_questions'])} questions")

    try:
        # Convert dicts to QuizQuestion objects
        questions = []
        for q in state["generated_questions"]:
            question = QuizQuestion(
                question=q.get("question", ""),
                options=q.get("options", []),
                correct_answer=q.get("correct_answer", 0),
                explanation=q.get("explanation"),
                source_reference=q.get("source_reference"),
            )
            questions.append(question)

        # Create quiz title
        topic_suffix = f": {state['topic']}" if state.get("topic") else ""
        title = f"Quiz{topic_suffix}"

        # Create and save quiz
        quiz = Quiz(
            notebook_id=state["notebook_id"],
            title=title,
            questions=questions,
            source_ids=state.get("source_ids"),
            created_by="user",
        )
        await quiz.save()

        # Create artifact tracker
        await Artifact.create_for_artifact(
            notebook_id=state["notebook_id"],
            artifact_type="quiz",
            artifact_id=quiz.id,
            title=quiz.title,
        )

        logger.info(f"Quiz saved with ID: {quiz.id}")

        return {
            "quiz_id": quiz.id,
            "status": "completed",
        }

    except Exception as e:
        logger.error(f"Error saving quiz: {e}")
        logger.exception(e)
        return {
            "error": f"Failed to save quiz: {str(e)}",
            "status": "failed",
        }


async def generate_quiz(
    notebook_id: str,
    topic: Optional[str] = None,
    num_questions: int = 5,
    source_ids: Optional[List[str]] = None,
) -> dict:
    """
    Main entry point for quiz generation.
    
    Args:
        notebook_id: ID of the notebook to generate quiz for
        topic: Optional topic to focus questions on
        num_questions: Number of questions to generate (default: 5)
        source_ids: Optional list of specific source IDs to use
        
    Returns:
        dict with quiz_id if successful, or error message if failed
    """
    logger.info(f"Starting quiz generation for notebook {notebook_id}")

    # Initialize state
    state: QuizGenerationState = {
        "notebook_id": notebook_id,
        "topic": topic,
        "num_questions": min(num_questions, 20),  # Cap at 20 questions
        "source_ids": source_ids,
        "sources_content": "",
        "generated_questions": [],
        "quiz_id": None,
        "error": None,
        "status": "pending",
    }

    # Run workflow steps sequentially
    # Step 1: Gather sources
    state.update(await gather_sources(state))
    if state.get("error"):
        return {"error": state["error"], "status": state["status"]}

    # Step 2: Generate questions
    state.update(await generate_questions(state))
    if state.get("error"):
        return {"error": state["error"], "status": state["status"]}

    # Step 3: Save quiz
    state.update(await save_quiz(state))
    if state.get("error"):
        return {"error": state["error"], "status": state["status"]}

    return {
        "quiz_id": state["quiz_id"],
        "status": state["status"],
        "num_questions": len(state["generated_questions"]),
    }
