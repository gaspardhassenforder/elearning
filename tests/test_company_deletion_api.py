"""Integration tests for company deletion API endpoints."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from api.routers.companies import delete_company_endpoint, preview_company_deletion
from open_notebook.domain.company_deletion import (
    CompanyDeletionReport,
    CompanyDeletionSummary,
)


@pytest.mark.asyncio
class TestPreviewCompanyDeletion:
    """Test GET /admin/companies/{company_id}/deletion-summary endpoint."""

    async def test_preview_company_deletion_returns_summary(self):
        """GET /admin/companies/{id}/deletion-summary returns CompanyDeletionSummary."""
        # Arrange: Mock admin user
        mock_admin = MagicMock()
        mock_admin.id = "user:admin"

        # Mock summary
        mock_summary = CompanyDeletionSummary(
            company_id="company:acme",
            company_name="ACME Corp",
            user_count=5,
            assignment_count=3,
            affected_notebooks=["notebook:1", "notebook:2"],
        )

        with patch(
            "api.routers.companies.get_company_deletion_summary",
            return_value=mock_summary,
        ):
            # Act
            result = await preview_company_deletion("company:acme", mock_admin)

            # Assert
            assert isinstance(result, CompanyDeletionSummary)
            assert result.company_id == "company:acme"
            assert result.user_count == 5
            assert result.assignment_count == 3

    async def test_preview_company_deletion_returns_404_for_missing_company(self):
        """GET /admin/companies/{id}/deletion-summary returns 404 for non-existent company."""
        # Arrange
        mock_admin = MagicMock()
        mock_admin.id = "user:admin"

        with patch(
            "api.routers.companies.get_company_deletion_summary",
            side_effect=ValueError("Company company:missing not found"),
        ):
            # Act & Assert
            with pytest.raises(HTTPException) as exc_info:
                await preview_company_deletion("company:missing", mock_admin)

            assert exc_info.value.status_code == 404
            assert "Company company:missing not found" in str(
                exc_info.value.detail
            )


@pytest.mark.asyncio
class TestDeleteCompanyEndpoint:
    """Test DELETE /admin/companies/{company_id} endpoint."""

    async def test_delete_company_requires_confirmation(self):
        """DELETE /admin/companies/{id} returns 400 without ?confirm=true."""
        # Arrange: Mock admin user
        mock_admin = MagicMock()
        mock_admin.id = "user:admin"

        # Act & Assert: Call without confirm=True
        with pytest.raises(HTTPException) as exc_info:
            await delete_company_endpoint("company:acme", confirm=False, admin=mock_admin)

        assert exc_info.value.status_code == 400
        assert "Must confirm deletion" in str(exc_info.value.detail)

    async def test_delete_company_cascades_to_all_users(self):
        """DELETE /admin/companies/{id}?confirm=true returns CompanyDeletionReport."""
        # Arrange
        mock_admin = MagicMock()
        mock_admin.id = "user:admin"

        mock_report = CompanyDeletionReport(
            company_id="company:test",
            deleted_users=3,
            deleted_user_data_records=45,
            deleted_assignments=2,
            total_deleted=48,
        )

        with patch(
            "api.routers.companies.delete_company_cascade",
            return_value=mock_report,
        ):
            # Act
            result = await delete_company_endpoint(
                "company:test", confirm=True, admin=mock_admin
            )

            # Assert
            assert isinstance(result, CompanyDeletionReport)
            assert result.company_id == "company:test"
            assert result.deleted_users == 3
            assert result.total_deleted == 48

    async def test_delete_company_logs_with_warning_severity(self):
        """DELETE /admin/companies/{id} logs deletion with WARNING severity."""
        # Arrange
        mock_admin = MagicMock()
        mock_admin.id = "user:admin"

        mock_report = CompanyDeletionReport(
            company_id="company:test", deleted_users=2, total_deleted=10
        )

        with patch(
            "api.routers.companies.delete_company_cascade",
            return_value=mock_report,
        ):
            with patch("api.routers.companies.logger") as mock_logger:
                # Act
                await delete_company_endpoint(
                    "company:test", confirm=True, admin=mock_admin
                )

                # Assert: Verify WARNING level logging
                mock_logger.warning.assert_called_once()
                call_args = mock_logger.warning.call_args
                assert "Company deleted by admin" in call_args[0][0]
                assert call_args[1]["extra"]["company_id"] == "company:test"
                assert call_args[1]["extra"]["admin_id"] == "user:admin"

    async def test_delete_company_returns_404_for_missing_company(self):
        """DELETE /admin/companies/{id} returns 404 for non-existent company."""
        # Arrange
        mock_admin = MagicMock()
        mock_admin.id = "user:admin"

        with patch(
            "api.routers.companies.delete_company_cascade",
            side_effect=ValueError("Company company:missing not found"),
        ):
            # Act & Assert
            with pytest.raises(HTTPException) as exc_info:
                await delete_company_endpoint(
                    "company:missing", confirm=True, admin=mock_admin
                )

            assert exc_info.value.status_code == 404
            assert "Company company:missing not found" in str(
                exc_info.value.detail
            )

    async def test_delete_company_handles_unexpected_errors(self):
        """DELETE /admin/companies/{id} returns 500 on unexpected errors."""
        # Arrange
        mock_admin = MagicMock()
        mock_admin.id = "user:admin"

        with patch(
            "api.routers.companies.delete_company_cascade",
            side_effect=Exception("Database connection failed"),
        ):
            # Act & Assert
            with pytest.raises(HTTPException) as exc_info:
                await delete_company_endpoint(
                    "company:error", confirm=True, admin=mock_admin
                )

            assert exc_info.value.status_code == 500
            assert "Internal server error" in str(exc_info.value.detail)
