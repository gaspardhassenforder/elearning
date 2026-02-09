"""Integration tests for user deletion API endpoint."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from api.routers.users import delete_user_endpoint
from open_notebook.domain.user_deletion import UserDeletionReport


@pytest.mark.asyncio
class TestDeleteUserEndpoint:
    """Test DELETE /admin/users/{user_id} endpoint."""

    async def test_delete_user_endpoint_returns_deletion_report(self):
        """DELETE /admin/users/{user_id} returns UserDeletionReport."""
        # Arrange: Mock admin user
        mock_admin = MagicMock()
        mock_admin.id = "user:admin"

        # Mock deletion report
        mock_report = UserDeletionReport(
            user_id="user:alice",
            deleted_progress_records=2,
            deleted_checkpoints=1,
            deleted_quiz_records=1,
            deleted_note_records=1,
            total_deleted=6,
        )

        with patch(
            "api.routers.users.delete_user_cascade", return_value=mock_report
        ):
            # Act
            result = await delete_user_endpoint("user:alice", mock_admin)

            # Assert
            assert isinstance(result, UserDeletionReport)
            assert result.user_id == "user:alice"
            assert result.total_deleted == 6

    async def test_delete_user_endpoint_returns_404_for_missing_user(self):
        """DELETE /admin/users/{user_id} returns 404 for non-existent user."""
        # Arrange: Mock admin user
        mock_admin = MagicMock()
        mock_admin.id = "user:admin"

        with patch(
            "api.routers.users.delete_user_cascade",
            side_effect=ValueError("User user:missing not found"),
        ):
            # Act & Assert
            with pytest.raises(HTTPException) as exc_info:
                await delete_user_endpoint("user:missing", mock_admin)

            assert exc_info.value.status_code == 404
            assert "User user:missing not found" in str(exc_info.value.detail)

    async def test_delete_user_endpoint_logs_deletion(self):
        """DELETE /admin/users/{user_id} logs deletion with admin ID."""
        # Arrange
        mock_admin = MagicMock()
        mock_admin.id = "user:admin"

        mock_report = UserDeletionReport(user_id="user:bob", total_deleted=5)

        with patch(
            "api.routers.users.delete_user_cascade", return_value=mock_report
        ):
            with patch("api.routers.users.logger") as mock_logger:
                # Act
                await delete_user_endpoint("user:bob", mock_admin)

                # Assert: Verify logging was called with admin ID
                mock_logger.info.assert_called_once()
                call_args = mock_logger.info.call_args
                assert "User deleted by admin" in call_args[0][0]
                assert call_args[1]["extra"]["admin_id"] == "user:admin"
                assert call_args[1]["extra"]["user_id"] == "user:bob"

    async def test_delete_user_endpoint_handles_unexpected_errors(self):
        """DELETE /admin/users/{user_id} returns 500 on unexpected errors."""
        # Arrange
        mock_admin = MagicMock()
        mock_admin.id = "user:admin"

        with patch(
            "api.routers.users.delete_user_cascade",
            side_effect=Exception("Database connection failed"),
        ):
            # Act & Assert
            with pytest.raises(HTTPException) as exc_info:
                await delete_user_endpoint("user:error", mock_admin)

            assert exc_info.value.status_code == 500
            assert "Internal server error" in str(exc_info.value.detail)
