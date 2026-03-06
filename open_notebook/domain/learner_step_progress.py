"""Learner step progress domain model for tracking lesson plan completion.

Tracks which lesson steps a learner has completed, allowing the AI teacher
to know exactly where the learner is in the structured lesson plan.
"""

from datetime import datetime
from typing import ClassVar, Optional

from loguru import logger

from open_notebook.database.repository import ensure_record_id, repo_query
from open_notebook.domain.base import ObjectModel
from open_notebook.exceptions import DatabaseOperationError


class LearnerStepProgress(ObjectModel):
    """Tracks learner completion of individual lesson steps.

    Attributes:
        user_id: Reference to user (learner)
        step_id: Reference to lesson step
        completed_at: Timestamp when step was marked complete (None = incomplete)
    """

    table_name: ClassVar[str] = "learner_step_progress"
    nullable_fields: ClassVar[set[str]] = {"completed_at"}

    user_id: str
    step_id: str
    completed_at: Optional[datetime] = None

    def needs_embedding(self) -> bool:
        """Progress records are not searchable."""
        return False

    @classmethod
    async def mark_complete(
        cls, user_id: str, step_id: str
    ) -> "LearnerStepProgress":
        """Mark a lesson step as complete for a learner (upsert).

        Creates or updates the progress record with the current timestamp.

        Args:
            user_id: User record ID (with or without 'user:' prefix)
            step_id: Lesson step record ID (with or without 'lesson_step:' prefix)

        Returns:
            LearnerStepProgress instance
        """
        if not user_id.startswith("user:"):
            user_id = f"user:{user_id}"
        if not step_id.startswith("lesson_step:"):
            step_id = f"lesson_step:{step_id}"

        try:
            # Check if already exists
            existing = await cls._get_by_user_and_step(user_id, step_id)
            if existing:
                if existing.completed_at is None:
                    # Update to mark as complete
                    result = await repo_query(
                        "UPDATE $id SET completed_at = $completed_at",
                        {
                            "id": existing.id,
                            "completed_at": datetime.now(),
                        },
                    )
                    if result:
                        return cls(**result[0])
                return existing

            # Create new progress record
            from open_notebook.database.repository import repo_create

            data = {
                "user_id": ensure_record_id(user_id),
                "step_id": ensure_record_id(step_id),
                "completed_at": datetime.now(),
            }
            result = await repo_create(cls.table_name, data)
            logger.info(
                f"Marked step {step_id} complete for user {user_id}"
            )
            return cls(**result)

        except Exception as e:
            logger.error(
                f"Error marking step {step_id} complete for user {user_id}: {str(e)}"
            )
            raise DatabaseOperationError(e)

    @classmethod
    async def _get_by_user_and_step(
        cls, user_id: str, step_id: str
    ) -> Optional["LearnerStepProgress"]:
        """Get progress record for a specific user and step."""
        try:
            result = await repo_query(
                "SELECT * FROM learner_step_progress WHERE user_id = $user_id AND step_id = $step_id LIMIT 1",
                {
                    "user_id": ensure_record_id(user_id),
                    "step_id": ensure_record_id(step_id),
                },
            )
            if result:
                return cls(**result[0])
            return None
        except Exception as e:
            logger.error(f"Error fetching progress for user {user_id} on step {step_id}: {str(e)}")
            return None

    @classmethod
    async def get_completed_step_ids(
        cls, user_id: str, notebook_id: str
    ) -> list[str]:
        """Get IDs of all completed steps for a learner in a notebook.

        Args:
            user_id: User record ID
            notebook_id: Notebook record ID

        Returns:
            List of completed step record IDs (as strings)
        """
        if not user_id.startswith("user:"):
            user_id = f"user:{user_id}"
        if not notebook_id.startswith("notebook:"):
            notebook_id = f"notebook:{notebook_id}"

        try:
            result = await repo_query(
                """
                SELECT VALUE type::string(step_id) FROM learner_step_progress
                WHERE user_id = $user_id
                  AND step_id IN (
                    SELECT VALUE id FROM lesson_step WHERE notebook_id = $notebook_id
                  )
                  AND completed_at IS NOT NULL
                """,
                {
                    "user_id": ensure_record_id(user_id),
                    "notebook_id": ensure_record_id(notebook_id),
                },
            )
            return [str(r) for r in result] if result else []
        except Exception as e:
            logger.error(
                f"Error fetching completed step IDs for user {user_id} in notebook {notebook_id}: {str(e)}"
            )
            raise DatabaseOperationError(e)

    @classmethod
    async def reset_progress(cls, user_id: str, notebook_id: str) -> int:
        """Delete all progress records for a learner in a notebook.

        Args:
            user_id: User record ID
            notebook_id: Notebook record ID

        Returns:
            Number of deleted records
        """
        if not user_id.startswith("user:"):
            user_id = f"user:{user_id}"
        if not notebook_id.startswith("notebook:"):
            notebook_id = f"notebook:{notebook_id}"

        try:
            result = await repo_query(
                """
                DELETE learner_step_progress
                WHERE user_id = $user_id
                  AND step_id IN (
                    SELECT VALUE id FROM lesson_step WHERE notebook_id = $notebook_id
                  )
                RETURN BEFORE
                """,
                {
                    "user_id": ensure_record_id(user_id),
                    "notebook_id": ensure_record_id(notebook_id),
                },
            )
            deleted = len(result) if result else 0
            logger.info(f"Reset {deleted} progress records for user {user_id} in notebook {notebook_id}")
            return deleted
        except Exception as e:
            logger.error(f"Error resetting progress for user {user_id} in notebook {notebook_id}: {str(e)}")
            raise DatabaseOperationError(e)

    @classmethod
    async def get_for_notebook(
        cls, user_id: str, notebook_id: str
    ) -> list["LearnerStepProgress"]:
        """Get all progress records for a learner in a notebook.

        Args:
            user_id: User record ID
            notebook_id: Notebook record ID

        Returns:
            List of LearnerStepProgress instances
        """
        if not user_id.startswith("user:"):
            user_id = f"user:{user_id}"
        if not notebook_id.startswith("notebook:"):
            notebook_id = f"notebook:{notebook_id}"

        try:
            result = await repo_query(
                """
                SELECT * FROM learner_step_progress
                WHERE user_id = $user_id
                  AND step_id IN (
                    SELECT VALUE id FROM lesson_step WHERE notebook_id = $notebook_id
                  )
                """,
                {
                    "user_id": ensure_record_id(user_id),
                    "notebook_id": ensure_record_id(notebook_id),
                },
            )
            return [cls(**item) for item in result] if result else []
        except Exception as e:
            logger.error(
                f"Error fetching step progress for user {user_id} in notebook {notebook_id}: {str(e)}"
            )
            raise DatabaseOperationError(e)
