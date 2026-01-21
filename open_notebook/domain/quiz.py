"""Quiz domain models for the learning platform."""

from typing import ClassVar, List, Literal, Optional

from pydantic import BaseModel, Field

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
