"""Quiz domain models for the learning platform."""

import json
from typing import ClassVar, List, Literal, Optional, Union

from pydantic import BaseModel, Field, field_validator

from open_notebook.database.repository import ensure_record_id
from open_notebook.domain.base import ObjectModel


class QuizQuestion(BaseModel):
    """Individual quiz question (embedded in Quiz)."""

    question: str
    options: List[str] = Field(default_factory=list)  # For MCQ
    correct_answer: int = 0  # Index of correct option (0-based)
    explanation: Optional[str] = None
    source_reference: Optional[str] = None  # Reference to source document


class Quiz(ObjectModel):
    """Quiz artifact generated from notebook sources."""

    table_name: ClassVar[str] = "quiz"

    notebook_id: str
    title: str
    description: Optional[str] = None
    questions: List[QuizQuestion] = Field(default_factory=list)
    created_by: Literal["admin", "user"] = "user"
    source_ids: Optional[List[str]] = None  # Which sources the quiz covers
    # Store questions as JSON string in DB to work around SurrealDB nested object issues
    questions_json: Optional[str] = None
    # Persistence: store user's last attempt
    user_answers: Optional[List[int]] = None  # User's selected answers (indices)
    last_score: Optional[int] = None  # Last score achieved
    completed: bool = False  # Whether quiz has been completed at least once

    @field_validator('questions', mode='before')
    @classmethod
    def validate_questions(cls, v):
        """Ensure questions are QuizQuestion objects."""
        if not v:
            return []
        # If it's a string, it might be JSON from DB
        if isinstance(v, str):
            try:
                v = json.loads(v)
            except json.JSONDecodeError:
                return []
        result = []
        for q in v:
            if isinstance(q, QuizQuestion):
                result.append(q)
            elif isinstance(q, dict):
                result.append(QuizQuestion(**q))
            else:
                # Try to convert to dict first
                result.append(QuizQuestion(**dict(q)))
        return result
    
    def __init__(self, **data):
        """Initialize Quiz, restoring questions from questions_json if present."""
        # If questions_json is provided and questions is empty, restore from JSON
        questions_json = data.get('questions_json')
        questions = data.get('questions', [])
        
        if questions_json and not questions:
            try:
                parsed = json.loads(questions_json)
                if isinstance(parsed, list):
                    data['questions'] = parsed
            except (json.JSONDecodeError, TypeError):
                pass
        
        super().__init__(**data)
    
    def _prepare_save_data(self) -> dict:
        """Override to serialize questions as JSON string for reliable storage."""
        from loguru import logger
        
        data = super()._prepare_save_data()
        
        # Convert notebook_id string to RecordID format for database
        if "notebook_id" in data and data["notebook_id"] is not None:
            data["notebook_id"] = ensure_record_id(data["notebook_id"])
        
        # Serialize questions to JSON string for reliable storage in SurrealDB
        if "questions" in data and data["questions"]:
            questions_data = data["questions"]
            serialized_questions = []
            for q in questions_data:
                if isinstance(q, dict):
                    serialized_questions.append(q)
                elif hasattr(q, 'model_dump'):
                    serialized_questions.append(q.model_dump())
                else:
                    serialized_questions.append(dict(q))
            
            # Store as JSON string
            data["questions_json"] = json.dumps(serialized_questions)
            logger.info(f"Serialized {len(serialized_questions)} questions to JSON string")
        
        # Keep questions as empty array in DB (SurrealDB can't handle nested objects)
        data["questions"] = []
        
        return data

    async def get_notebook(self):
        """Get the parent notebook."""
        from open_notebook.domain.notebook import Notebook

        return await Notebook.get(self.notebook_id)

    def add_question(self, question: QuizQuestion) -> None:
        """Add a question to the quiz."""
        self.questions.append(question)

    def get_score(self, answers: List[int]) -> dict:
        """
        Calculate score from user answers.
        
        Args:
            answers: List of answer indices (0-based) matching question order
            
        Returns:
            dict with score, total, percentage, and per-question results
        """
        if len(answers) != len(self.questions):
            raise ValueError(
                f"Expected {len(self.questions)} answers, got {len(answers)}"
            )

        results = []
        correct = 0

        for i, (question, answer) in enumerate(zip(self.questions, answers)):
            is_correct = answer == question.correct_answer
            if is_correct:
                correct += 1
            results.append({
                "question_index": i,
                "user_answer": answer,
                "correct_answer": question.correct_answer,
                "is_correct": is_correct,
                "explanation": question.explanation,
            })

        return {
            "score": correct,
            "total": len(self.questions),
            "percentage": round(correct / len(self.questions) * 100, 1) if self.questions else 0,
            "results": results,
        }
