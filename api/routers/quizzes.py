"""Quiz API router."""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from api.auth import get_current_user, require_admin, LearnerContext, get_current_learner
from open_notebook.domain.user import User
from api import quiz_service

router = APIRouter(dependencies=[Depends(get_current_user)])


class QuizGenerateRequest(BaseModel):
    """Request body for quiz generation."""

    topic: Optional[str] = Field(None, description="Optional topic to focus questions on")
    num_questions: int = Field(5, ge=1, le=20, description="Number of questions to generate")
    source_ids: Optional[List[str]] = Field(None, description="Optional specific source IDs to use")
    instructions: Optional[str] = Field(None, description="Optional specific instructions for quiz generation")


class QuizAnswersRequest(BaseModel):
    """Request body for checking quiz answers."""

    answers: List[int] = Field(..., description="List of answer indices (0-based)")


@router.post("/notebooks/{notebook_id}/quizzes/generate")
async def generate_quiz(notebook_id: str, request: QuizGenerateRequest, admin: User = Depends(require_admin)):
    """
    Generate a new quiz for the notebook.
    
    The quiz will be generated from the notebook's sources using AI.
    """
    try:
        result = await quiz_service.generate_quiz(
            notebook_id=notebook_id,
            topic=request.topic,
            num_questions=request.num_questions,
            source_ids=request.source_ids,
            instructions=request.instructions,
        )

        if result.get("error"):
            raise HTTPException(status_code=400, detail=result["error"])

        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/notebooks/{notebook_id}/quizzes")
async def get_notebook_quizzes(notebook_id: str):
    """Get all quizzes for a notebook."""
    quizzes = await quiz_service.get_notebook_quizzes(notebook_id)
    return [
        {
            "id": q.id,
            "title": q.title,
            "description": q.description,
            "num_questions": len(q.questions),
            "created": q.created,
            "created_by": q.created_by,
        }
        for q in quizzes
    ]


@router.get("/quizzes/{quiz_id}")
async def get_quiz(quiz_id: str, user: User = Depends(get_current_user)):
    """
    Get a specific quiz with all questions.

    Story 4.6: Company scoping for learners - validates notebook assignment.
    Story 7.5: Uses get_current_learner() for consistent company isolation.
    Admins can access any quiz; learners can only access quizzes from assigned modules.
    """
    from loguru import logger
    from open_notebook.database.repository import repo_query

    quiz = await quiz_service.get_quiz(quiz_id)
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")

    # Story 7.5: Company scoping - admin vs learner pattern
    if user.role == "learner":
        # Validate quiz's notebook is assigned to learner's company
        if not user.company_id:
            raise HTTPException(status_code=403, detail="Access denied")

        # Check module_assignment for company access
        result = await repo_query(
            """
            SELECT VALUE true
            FROM module_assignment
            WHERE notebook_id = $notebook_id
              AND company_id = $company_id
            LIMIT 1
            """,
            {"notebook_id": quiz.notebook_id, "company_id": user.company_id},
        )

        if not result:
            logger.warning(
                f"Learner {user.id} attempted to access quiz {quiz_id} from unassigned notebook {quiz.notebook_id}"
            )
            raise HTTPException(status_code=403, detail="Quiz not accessible")

    logger.info(f"Quiz {quiz_id} accessed by {user.role} user {user.id}: {len(quiz.questions)} questions")

    response = {
        "id": quiz.id,
        "title": quiz.title,
        "description": quiz.description,
        "questions": [
            {
                "question": q.question,
                "options": q.options,
                # Include correct_answer only if quiz is completed (for showing results)
                **({"correct_answer": q.correct_answer, "explanation": q.explanation} if quiz.completed else {}),
            }
            for q in quiz.questions
        ],
        "num_questions": len(quiz.questions),
        "created": quiz.created,
        "created_by": quiz.created_by,
        # Include completion state
        "completed": quiz.completed,
        "user_answers": quiz.user_answers,
        "last_score": quiz.last_score,
    }

    return response


@router.post("/quizzes/{quiz_id}/check")
async def check_quiz_answers(quiz_id: str, request: QuizAnswersRequest, user: User = Depends(get_current_user)):
    """
    Check user answers against a quiz.

    Story 4.6: Company scoping for learners - validates notebook assignment.
    Story 7.5: Uses get_current_learner() for consistent company isolation.
    Returns score, percentage, and per-question results with explanations.
    """
    from loguru import logger
    from open_notebook.database.repository import repo_query

    try:
        # Fetch quiz first to validate access
        quiz = await quiz_service.get_quiz(quiz_id)
        if not quiz:
            raise HTTPException(status_code=404, detail="Quiz not found")

        # Story 7.5: Company scoping - admin vs learner pattern
        if user.role == "learner":
            # Validate quiz's notebook is assigned to learner's company
            if not user.company_id:
                raise HTTPException(status_code=403, detail="Access denied")

            # Check module_assignment for company access
            result = await repo_query(
                """
                SELECT VALUE true
                FROM module_assignment
                WHERE notebook_id = $notebook_id
                  AND company_id = $company_id
                LIMIT 1
                """,
                {"notebook_id": quiz.notebook_id, "company_id": user.company_id},
            )

            if not result:
                logger.warning(
                    f"Learner {user.id} attempted to check quiz {quiz_id} from unassigned notebook {quiz.notebook_id}"
                )
                raise HTTPException(status_code=403, detail="Quiz not accessible")

        # Proceed with answer checking
        result = await quiz_service.check_quiz_answers(quiz_id, request.answers)
        return result
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/quizzes/{quiz_id}/reset")
async def reset_quiz(quiz_id: str):
    """Reset a quiz to allow retaking it."""
    try:
        await quiz_service.reset_quiz(quiz_id)
        return {"status": "reset", "quiz_id": quiz_id}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/quizzes/{quiz_id}")
async def delete_quiz(quiz_id: str, admin: User = Depends(require_admin)):
    """Delete a quiz."""
    success = await quiz_service.delete_quiz(quiz_id)
    if not success:
        raise HTTPException(status_code=404, detail="Quiz not found or could not be deleted")
    return {"status": "deleted", "quiz_id": quiz_id}
