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
    instructions: Optional[str] = None,
    user_id: Optional[str] = None,  # Story 7.7: Token tracking context
    company_id: Optional[str] = None,  # Story 7.7: Token tracking context
) -> dict:
    """
    Generate a quiz for a notebook.

    Args:
        notebook_id: ID of the notebook
        topic: Optional topic to focus on
        num_questions: Number of questions to generate
        source_ids: Optional specific source IDs to use
        instructions: Optional specific instructions for quiz generation
        user_id: Optional user ID for token tracking (Story 7.7)
        company_id: Optional company ID for token tracking (Story 7.7)

    Returns:
        dict with quiz_id if successful, or error if failed
    """
    logger.info(f"Quiz service: generating quiz for notebook {notebook_id}")

    result = await generate_quiz_workflow(
        notebook_id=notebook_id,
        topic=topic,
        num_questions=num_questions,
        source_ids=source_ids,
        instructions=instructions,
        user_id=user_id,  # Story 7.7: Pass token tracking context
        company_id=company_id,  # Story 7.7: Pass token tracking context
    )

    return result


async def get_quiz(quiz_id: str) -> Optional[Quiz]:
    """Get a quiz by ID."""
    from open_notebook.database.repository import repo_query, ensure_record_id
    
    try:
        # First, check raw database data
        raw_result = await repo_query("SELECT * FROM $id", {"id": ensure_record_id(quiz_id)})
        if raw_result:
            raw_data = raw_result[0]
            logger.info(f"Raw DB data for {quiz_id}: keys = {list(raw_data.keys())}")
            logger.info(f"Raw DB: questions = {raw_data.get('questions')}")
            logger.info(f"Raw DB: questions_json = {raw_data.get('questions_json', 'NOT FOUND')[:200] if raw_data.get('questions_json') else 'None/Empty'}")
        
        quiz = await Quiz.get(quiz_id)
        logger.info(f"Loaded quiz {quiz_id}: title={quiz.title}, questions_count={len(quiz.questions)}, questions_json={bool(quiz.questions_json)}")
        if quiz.questions:
            logger.info(f"First question: {quiz.questions[0].question[:50]}...")
        return quiz
    except Exception as e:
        logger.error("Error getting quiz {}: {}", quiz_id, str(e))
        logger.exception(e)
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
        logger.error("Error getting quizzes for notebook {}: {}", notebook_id, str(e))
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
        logger.error("Error deleting quiz {}: {}", quiz_id, str(e))
        return False


async def check_quiz_answers(quiz_id: str, answers: List[int]) -> dict:
    """
    Check user answers against a quiz and persist the results.
    
    Args:
        quiz_id: ID of the quiz
        answers: List of answer indices (0-based) matching question order
        
    Returns:
        dict with score, total, percentage, and per-question results
    """
    quiz = await Quiz.get(quiz_id)
    if not quiz:
        raise ValueError(f"Quiz {quiz_id} not found")
    
    result = quiz.get_score(answers)
    
    # Persist the user's answers and score
    quiz.user_answers = answers
    quiz.last_score = result["score"]
    quiz.completed = True
    await quiz.save()
    
    logger.info(f"Quiz {quiz_id} completed with score {result['score']}/{result['total']}")
    
    return result


async def reset_quiz(quiz_id: str) -> bool:
    """
    Reset a quiz to allow retaking it.
    
    Args:
        quiz_id: ID of the quiz to reset
        
    Returns:
        True if successful
    """
    quiz = await Quiz.get(quiz_id)
    if not quiz:
        raise ValueError(f"Quiz {quiz_id} not found")
    
    quiz.user_answers = None
    quiz.last_score = None
    quiz.completed = False
    await quiz.save()
    
    logger.info(f"Quiz {quiz_id} reset for retake")
    return True
