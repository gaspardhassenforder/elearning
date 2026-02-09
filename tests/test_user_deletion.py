"""Unit tests for user cascade deletion functionality."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from open_notebook.domain.user_deletion import (
    UserDeletionReport,
    delete_user_cascade,
)


class TestUserDeletionReport:
    """Test UserDeletionReport model validation."""

    def test_user_deletion_report_validates(self):
        """UserDeletionReport accepts valid data."""
        report = UserDeletionReport(
            user_id="user:alice",
            deleted_progress_records=5,
            deleted_checkpoints=3,
            deleted_quiz_records=2,
            deleted_note_records=1,
            deleted_assignment_records=0,
            total_deleted=12,
        )
        assert report.user_id == "user:alice"
        assert report.total_deleted == 12

    def test_user_deletion_report_defaults_to_zero(self):
        """UserDeletionReport has zero defaults for all counters."""
        report = UserDeletionReport(user_id="user:test")
        assert report.deleted_progress_records == 0
        assert report.deleted_checkpoints == 0
        assert report.total_deleted == 0


@pytest.mark.asyncio
class TestDeleteUserCascade:
    """Test delete_user_cascade function."""

    async def test_delete_user_cascade_raises_for_missing_user(self):
        """delete_user_cascade raises ValueError for non-existent user."""
        with patch("open_notebook.domain.user_deletion.User.get", return_value=None):
            with pytest.raises(ValueError, match="User user:missing not found"):
                await delete_user_cascade("user:missing")

    async def test_delete_user_cascade_returns_deletion_report(self):
        """delete_user_cascade returns UserDeletionReport with counts."""
        # Arrange: Mock user and associated data
        mock_user = MagicMock()
        mock_user.id = "user:alice"
        mock_user.delete = AsyncMock()

        # Mock repo_query to return data for cascade deletion
        with patch("open_notebook.domain.user_deletion.User.get", return_value=mock_user):
            with patch("open_notebook.domain.user_deletion.repo_query") as mock_query:
                with patch(
                    "open_notebook.domain.user_deletion.delete_user_checkpoints",
                    return_value=1,
                ):
                    # Configure mock_query to return different data for each call
                    mock_query.side_effect = [
                        [{"id": "progress:1"}, {"id": "progress:2"}],  # 2 progress records
                        [{"id": "quiz:1"}],  # 1 quiz
                        [{"id": "note:1"}],  # 1 note
                        [],  # 0 assignments
                    ]

                    # Act
                    report = await delete_user_cascade("user:alice")

                    # Assert
                    assert isinstance(report, UserDeletionReport)
                    assert report.user_id == "user:alice"
                    assert report.deleted_progress_records == 2
                    assert report.deleted_checkpoints == 1
                    assert report.deleted_quiz_records == 1
                    assert report.deleted_note_records == 1
                    assert report.deleted_assignment_records == 0
                    assert report.total_deleted == 6  # 2 + 1 + 1 + 1 + 0 + 1 (user)
                    mock_user.delete.assert_called_once()

    async def test_delete_user_cascade_continues_on_checkpoint_failure(self):
        """delete_user_cascade continues even if checkpoint deletion fails."""
        # Arrange: Mock user
        mock_user = MagicMock()
        mock_user.id = "user:bob"
        mock_user.delete = AsyncMock()

        # Mock checkpoint deletion to raise exception
        with patch("open_notebook.domain.user_deletion.User.get", return_value=mock_user):
            with patch("open_notebook.domain.user_deletion.repo_query") as mock_query:
                with patch(
                    "open_notebook.domain.user_deletion.delete_user_checkpoints",
                    side_effect=Exception("SQLite connection failed"),
                ):
                    mock_query.side_effect = [
                        [],  # 0 progress
                        [],  # 0 quizzes
                        [],  # 0 notes
                        [],  # 0 assignments
                    ]

                    # Act: Should not raise exception
                    report = await delete_user_cascade("user:bob")

                    # Assert: User still deleted, checkpoints = 0
                    assert report.user_id == "user:bob"
                    assert report.deleted_checkpoints == 0
                    assert report.total_deleted == 1  # Just the user record
                    mock_user.delete.assert_called_once()

    async def test_delete_user_cascade_calls_all_deletion_queries(self):
        """delete_user_cascade executes all cascade deletion queries."""
        # Arrange
        mock_user = MagicMock()
        mock_user.id = "user:charlie"
        mock_user.delete = AsyncMock()

        with patch("open_notebook.domain.user_deletion.User.get", return_value=mock_user):
            with patch("open_notebook.domain.user_deletion.repo_query") as mock_query:
                with patch(
                    "open_notebook.domain.user_deletion.delete_user_checkpoints",
                    return_value=0,
                ):
                    mock_query.side_effect = [[], [], [], []]

                    # Act
                    await delete_user_cascade("user:charlie")

                    # Assert: Verify all deletion queries were called
                    assert mock_query.call_count == 4
                    # Check query patterns
                    call_args_list = [call[0][0] for call in mock_query.call_args_list]
                    assert any("learner_objective_progress" in q for q in call_args_list)
                    assert any("quiz" in q for q in call_args_list)
                    assert any("note" in q for q in call_args_list)
                    assert any("module_assignment" in q for q in call_args_list)
