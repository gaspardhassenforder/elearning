"""Quiz API router."""

from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from api import quiz_service

router = APIRouter()


class QuizGenerateRequest(BaseModel):
    """Request body for quiz generation."""

    topic: Optional[str] = Field(None, description="Optional topic to focus questions on")
    num_questions: int = Field(5, ge=1, le=20, description="Number of questions to generate")
    source_ids: Optional[List[str]] = Field(None, description="Optional specific source IDs to use")


class QuizAnswersRequest(BaseModel):
    """Request body for checking quiz answers."""

    answers: List[int] = Field(..., description="List of answer indices (0-based)")


@router.post("/notebooks/{notebook_id}/quizzes/generate")
async def generate_quiz(notebook_id: str, request: QuizGenerateRequest):
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
async def get_quiz(quiz_id: str):
    """Get a specific quiz with all questions."""
    quiz = await quiz_service.get_quiz(quiz_id)
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    
    return {
        "id": quiz.id,
        "title": quiz.title,
        "description": quiz.description,
        "questions": [
            {
                "question": q.question,
                "options": q.options,
                # Note: correct_answer is intentionally NOT included
                # so users can't cheat by inspecting the response
            }
            for q in quiz.questions
        ],
        "num_questions": len(quiz.questions),
        "created": quiz.created,
        "created_by": quiz.created_by,
    }


@router.post("/quizzes/{quiz_id}/check")
async def check_quiz_answers(quiz_id: str, request: QuizAnswersRequest):
    """
    Check user answers against a quiz.
    
    Returns score, percentage, and per-question results with explanations.
    """
    try:
        result = await quiz_service.check_quiz_answers(quiz_id, request.answers)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/quizzes/{quiz_id}")
async def delete_quiz(quiz_id: str):
    """Delete a quiz."""
    success = await quiz_service.delete_quiz(quiz_id)
    if not success:
        raise HTTPException(status_code=404, detail="Quiz not found or could not be deleted")
    return {"status": "deleted", "quiz_id": quiz_id}
