"""User cascade deletion service for GDPR-compliant data removal."""

from typing import Optional

from loguru import logger
from pydantic import BaseModel

from open_notebook.database.repository import repo_query
from open_notebook.domain.user import User
from open_notebook.observability.checkpoint_cleanup import delete_user_checkpoints


class UserDeletionReport(BaseModel):
    """Report of deleted records during user cascade deletion."""

    user_id: str
    deleted_progress_records: int = 0
    deleted_checkpoints: int = 0
    deleted_quiz_records: int = 0
    deleted_note_records: int = 0
    deleted_assignment_records: int = 0
    total_deleted: int = 0


async def delete_user_cascade(user_id: str) -> UserDeletionReport:
    """
    Delete user and all associated data (GDPR-compliant cascade).

    Cascades to:
    - learner_objective_progress (learning progress)
    - LangGraph checkpoints (conversation history)
    - module_assignment (if user is assigned_by admin)
    - quiz (user-created quizzes)
    - note (user-created notes)

    Args:
        user_id: User record ID (e.g., "user:alice")

    Returns:
        UserDeletionReport with counts of deleted records

    Raises:
        ValueError: If user not found
    """
    # Validate user exists
    user = await User.get(user_id)
    if not user:
        raise ValueError(f"User {user_id} not found")

    report = UserDeletionReport(user_id=user_id)

    # Delete learner progress records
    progress_result = await repo_query(
        "DELETE learner_objective_progress WHERE user_id = $uid RETURN BEFORE",
        {"uid": user_id},
    )
    report.deleted_progress_records = len(progress_result) if progress_result else 0

    # Delete LangGraph checkpoints (SQLite)
    try:
        report.deleted_checkpoints = delete_user_checkpoints(user_id)
    except Exception as e:
        logger.warning("Failed to delete checkpoints for {}: {}", user_id, str(e))
        # Continue deletion even if checkpoints fail

    # Delete user-created quizzes
    quiz_result = await repo_query(
        "DELETE quiz WHERE created_by = $uid RETURN BEFORE",
        {"uid": user_id},
    )
    report.deleted_quiz_records = len(quiz_result) if quiz_result else 0

    # Delete user-created notes
    note_result = await repo_query(
        "DELETE note WHERE user_id = $uid RETURN BEFORE", {"uid": user_id}
    )
    report.deleted_note_records = len(note_result) if note_result else 0

    # Delete module assignments where user is the assigner
    assignment_result = await repo_query(
        "DELETE module_assignment WHERE assigned_by = $uid RETURN BEFORE",
        {"uid": user_id},
    )
    report.deleted_assignment_records = (
        len(assignment_result) if assignment_result else 0
    )

    # Delete user record
    await user.delete()

    # Calculate total
    report.total_deleted = (
        report.deleted_progress_records
        + report.deleted_checkpoints
        + report.deleted_quiz_records
        + report.deleted_note_records
        + report.deleted_assignment_records
        + 1  # User record itself
    )

    logger.warning(
        f"User deletion cascade completed",
        extra={"user_id": user_id, "report": report.model_dump()},
    )

    return report
