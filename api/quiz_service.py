"""Quiz service for API layer."""

from typing import List, Optional

from loguru import logger

from open_notebook.domain.quiz import Quiz
from open_notebook.graphs.quiz_generation import generate_quiz as generate_quiz_workflow


async def generate_quiz(
    notebook_id: str,
    topic: Optional[str] = None,
    num_questions: int = 5,
    source_ids: Optional[List[str]] = None,
) -> dict:
    """
    Generate a quiz for a notebook.
    
    Args:
        notebook_id: ID of the notebook
        topic: Optional topic to focus on
        num_questions: Number of questions to generate
        source_ids: Optional specific source IDs to use
        
    Returns:
        dict with quiz_id if successful, or error if failed
    """
    logger.info(f"Quiz service: generating quiz for notebook {notebook_id}")
    
    result = await generate_quiz_workflow(
        notebook_id=notebook_id,
        topic=topic,
        num_questions=num_questions,
        source_ids=source_ids,
    )
    
    return result


async def get_quiz(quiz_id: str) -> Optional[Quiz]:
    """Get a quiz by ID."""
    try:
        return await Quiz.get(quiz_id)
    except Exception as e:
        logger.error(f"Error getting quiz {quiz_id}: {e}")
        return None


async def get_notebook_quizzes(notebook_id: str) -> List[Quiz]:
    """Get all quizzes for a notebook."""
    from open_notebook.database.repository import repo_query, ensure_record_id
    
    try:
        result = await repo_query(
            """
            SELECT * FROM quiz 
            WHERE notebook_id = $notebook_id 
            ORDER BY created DESC
            """,
            {"notebook_id": ensure_record_id(notebook_id)},
        )
        return [Quiz(**r) for r in result] if result else []
    except Exception as e:
        logger.error(f"Error getting quizzes for notebook {notebook_id}: {e}")
        return []


async def delete_quiz(quiz_id: str) -> bool:
    """Delete a quiz and its artifact tracker."""
    from open_notebook.database.repository import repo_query
    
    try:
        quiz = await Quiz.get(quiz_id)
        if not quiz:
            return False
        
        # Delete artifact tracker first
        await repo_query(
            "DELETE FROM artifact WHERE artifact_id = $artifact_id",
            {"artifact_id": quiz_id},
        )
        
        # Delete the quiz
        await quiz.delete()
        logger.info(f"Deleted quiz {quiz_id}")
        return True
    except Exception as e:
        logger.error(f"Error deleting quiz {quiz_id}: {e}")
        return False


async def check_quiz_answers(quiz_id: str, answers: List[int]) -> dict:
    """
    Check user answers against a quiz.
    
    Args:
        quiz_id: ID of the quiz
        answers: List of answer indices (0-based) matching question order
        
    Returns:
        dict with score, total, percentage, and per-question results
    """
    quiz = await Quiz.get(quiz_id)
    if not quiz:
        raise ValueError(f"Quiz {quiz_id} not found")
    
    return quiz.get_score(answers)
