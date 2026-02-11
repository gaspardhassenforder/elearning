"""Learner objective progress domain model for tracking comprehension (Story 4.4).

Tracks individual learner progress on learning objectives through:
- Conversation-based assessment (AI checks off objectives)
- Quiz-based assessment (future: Story 4.5+)
"""

from datetime import datetime
from enum import Enum
from typing import ClassVar, Optional

from loguru import logger
from pydantic import field_validator

from open_notebook.database.repository import repo_create, repo_query, repo_update, ensure_record_id
from open_notebook.domain.base import ObjectModel
from open_notebook.exceptions import DatabaseOperationError, InvalidInputError


class ProgressStatus(str, Enum):
    """Status of learner progress on an objective."""

    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class CompletedVia(str, Enum):
    """Method by which objective was completed."""

    CONVERSATION = "conversation"  # AI assessed via chat
    QUIZ = "quiz"  # Assessed via quiz


class LearnerObjectiveProgress(ObjectModel):
    """Tracks learner progress on individual learning objectives.

    Links a user to a learning objective with completion status and evidence.
    Used by AI teacher to track comprehension and guide conversation.

    Attributes:
        user_id: Reference to user (learner)
        objective_id: Reference to learning objective
        status: Progress status (not_started, in_progress, completed)
        completed_via: Method of completion (conversation, quiz)
        evidence: AI reasoning or quiz result justifying completion
        completed_at: Timestamp when marked complete
    """

    table_name: ClassVar[str] = "learner_objective_progress"

    user_id: str
    objective_id: str
    status: ProgressStatus
    completed_via: Optional[CompletedVia] = None
    evidence: Optional[str] = None
    completed_at: Optional[datetime] = None

    @field_validator("user_id")
    @classmethod
    def ensure_user_id_format(cls, v: str) -> str:
        """Ensure user_id is in RecordID format (user:id)."""
        if not v.startswith("user:"):
            return f"user:{v}"
        return v

    @field_validator("objective_id")
    @classmethod
    def ensure_objective_id_format(cls, v: str) -> str:
        """Ensure objective_id is in RecordID format (learning_objective:id)."""
        if not v.startswith("learning_objective:"):
            return f"learning_objective:{v}"
        return v

    @field_validator("evidence")
    @classmethod
    def validate_evidence(cls, v: Optional[str], info) -> Optional[str]:
        """Ensure evidence is provided when status is completed."""
        status = info.data.get("status")
        if status == ProgressStatus.COMPLETED and (not v or not v.strip()):
            raise InvalidInputError("Evidence is required when marking objective complete")
        return v.strip() if v else None

    def needs_embedding(self) -> bool:
        """Progress records are not searchable."""
        return False

    @classmethod
    async def create(
        cls,
        user_id: str,
        objective_id: str,
        status: ProgressStatus,
        completed_via: CompletedVia,
        evidence: str,
    ) -> "LearnerObjectiveProgress":
        """Create progress record for learner on objective.

        Handles UNIQUE constraint: if record exists, returns existing instead of error.

        Args:
            user_id: User record ID (with or without 'user:' prefix)
            objective_id: Objective record ID (with or without 'learning_objective:' prefix)
            status: Progress status (typically COMPLETED)
            completed_via: Method of completion (conversation or quiz)
            evidence: AI reasoning or quiz result

        Returns:
            LearnerObjectiveProgress instance (newly created or existing)

        Raises:
            DatabaseOperationError: If database operation fails
        """
        # Ensure IDs have correct format (validators apply on instance creation)
        if not user_id.startswith("user:"):
            user_id = f"user:{user_id}"
        if not objective_id.startswith("learning_objective:"):
            objective_id = f"learning_objective:{objective_id}"

        try:
            # Check if already exists (graceful duplicate handling)
            existing = await cls.get_by_user_and_objective(user_id, objective_id)
            if existing:
                logger.info(
                    f"Progress already exists for {user_id} on {objective_id}, returning existing"
                )
                return existing

            # Create new record
            data = {
                "user_id": ensure_record_id(user_id),
                "objective_id": ensure_record_id(objective_id),
                "status": status.value,
                "completed_via": completed_via.value,
                "evidence": evidence,
                "completed_at": datetime.now().isoformat() if status == ProgressStatus.COMPLETED else None,
            }

            result = await repo_create(cls.table_name, data)
            logger.info(f"Created progress record {result['id']} for {user_id} on {objective_id}")

            return cls(**result)

        except Exception as e:
            logger.error(f"Error creating progress record: {str(e)}")
            raise DatabaseOperationError(e)

    @classmethod
    async def get_by_user_and_objective(
        cls, user_id: str, objective_id: str
    ) -> Optional["LearnerObjectiveProgress"]:
        """Get progress for specific user on specific objective.

        Args:
            user_id: User record ID
            objective_id: Objective record ID

        Returns:
            LearnerObjectiveProgress instance or None if not found
        """
        # Ensure IDs have correct format
        if not user_id.startswith("user:"):
            user_id = f"user:{user_id}"
        if not objective_id.startswith("learning_objective:"):
            objective_id = f"learning_objective:{objective_id}"

        try:
            query = """
                SELECT * FROM learner_objective_progress
                WHERE user_id = $user_id AND objective_id = $objective_id
            """
            result = await repo_query(query, {"user_id": ensure_record_id(user_id), "objective_id": ensure_record_id(objective_id)})

            if result:
                return cls(**result[0])
            return None

        except Exception as e:
            logger.error(f"Error fetching progress for {user_id} on {objective_id}: {str(e)}")
            raise DatabaseOperationError(e)

    @classmethod
    async def get_user_progress_for_notebook(
        cls, user_id: str, notebook_id: str
    ) -> list["LearnerObjectiveProgress"]:
        """Get all progress records for user in a notebook.

        Joins with learning_objective to filter by notebook_id.

        Args:
            user_id: User record ID
            notebook_id: Notebook record ID

        Returns:
            List of LearnerObjectiveProgress instances
        """
        # Ensure IDs have correct format
        if not user_id.startswith("user:"):
            user_id = f"user:{user_id}"
        if not notebook_id.startswith("notebook:"):
            notebook_id = f"notebook:{notebook_id}"

        try:
            query = """
                SELECT * FROM learner_objective_progress
                WHERE user_id = $user_id
                  AND objective_id IN (
                    SELECT VALUE id FROM learning_objective WHERE notebook_id = $notebook_id
                  )
            """
            result = await repo_query(query, {"user_id": ensure_record_id(user_id), "notebook_id": ensure_record_id(notebook_id)})

            return [cls(**item) for item in result]

        except Exception as e:
            logger.error(f"Error fetching progress for {user_id} in {notebook_id}: {str(e)}")
            raise DatabaseOperationError(e)

    @classmethod
    async def update_status(
        cls,
        progress_id: str,
        status: ProgressStatus,
        completed_via: Optional[CompletedVia] = None,
        evidence: Optional[str] = None,
    ) -> "LearnerObjectiveProgress":
        """Update progress status (e.g., not_started → in_progress → completed).

        Args:
            progress_id: Progress record ID
            status: New status
            completed_via: Method of completion (required if status=completed)
            evidence: Evidence text (required if status=completed)

        Returns:
            Updated LearnerObjectiveProgress instance

        Raises:
            InvalidInputError: If completed without evidence
            DatabaseOperationError: If update fails
        """
        try:
            # Validate evidence when completing
            if status == ProgressStatus.COMPLETED and (not evidence or not evidence.strip()):
                raise InvalidInputError("Evidence is required when marking objective complete")

            data = {
                "status": status.value,
                "completed_at": datetime.now().isoformat() if status == ProgressStatus.COMPLETED else None,
            }

            if completed_via:
                data["completed_via"] = completed_via.value
            if evidence:
                data["evidence"] = evidence

            result = await repo_update(cls.table_name, progress_id, data)
            logger.info(f"Updated progress {progress_id} to status {status.value}")

            return cls(**result)

        except Exception as e:
            logger.error(f"Error updating progress {progress_id}: {str(e)}")
            raise DatabaseOperationError(e)

    @classmethod
    async def count_completed_for_notebook(cls, user_id: str, notebook_id: str) -> int:
        """Count completed objectives for user in notebook.

        Args:
            user_id: User record ID
            notebook_id: Notebook record ID

        Returns:
            Count of completed objectives
        """
        # Ensure IDs have correct format
        if not user_id.startswith("user:"):
            user_id = f"user:{user_id}"
        if not notebook_id.startswith("notebook:"):
            notebook_id = f"notebook:{notebook_id}"

        try:
            query = """
                SELECT count() AS count
                FROM learner_objective_progress
                WHERE user_id = $user_id
                  AND objective_id IN (
                    SELECT VALUE id FROM learning_objective WHERE notebook_id = $notebook_id
                  )
                  AND status = 'completed'
                GROUP ALL
            """
            result = await repo_query(query, {"user_id": ensure_record_id(user_id), "notebook_id": ensure_record_id(notebook_id)})

            return result[0]["count"] if result else 0

        except Exception as e:
            logger.error(f"Error counting completed objectives for {user_id} in {notebook_id}: {str(e)}")
            raise DatabaseOperationError(e)
