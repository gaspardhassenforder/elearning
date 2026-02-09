"""Unit tests for company cascade deletion functionality."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from open_notebook.domain.company_deletion import (
    CompanyDeletionReport,
    CompanyDeletionSummary,
    delete_company_cascade,
    get_company_deletion_summary,
)
from open_notebook.domain.user_deletion import UserDeletionReport


class TestCompanyDeletionSummary:
    """Test CompanyDeletionSummary model validation."""

    def test_company_deletion_summary_validates(self):
        """CompanyDeletionSummary accepts valid data."""
        summary = CompanyDeletionSummary(
            company_id="company:acme",
            company_name="ACME Corp",
            user_count=5,
            assignment_count=3,
            affected_notebooks=["notebook:1", "notebook:2"],
        )
        assert summary.company_id == "company:acme"
        assert summary.user_count == 5
        assert len(summary.affected_notebooks) == 2


class TestCompanyDeletionReport:
    """Test CompanyDeletionReport model validation."""

    def test_company_deletion_report_validates(self):
        """CompanyDeletionReport accepts valid data."""
        report = CompanyDeletionReport(
            company_id="company:acme",
            deleted_users=3,
            deleted_user_data_records=45,
            deleted_assignments=2,
            total_deleted=48,
        )
        assert report.company_id == "company:acme"
        assert report.deleted_users == 3
        assert report.total_deleted == 48

    def test_company_deletion_report_defaults_to_zero(self):
        """CompanyDeletionReport has zero defaults for all counters."""
        report = CompanyDeletionReport(company_id="company:test")
        assert report.deleted_users == 0
        assert report.deleted_user_data_records == 0
        assert report.total_deleted == 0


@pytest.mark.asyncio
class TestGetCompanyDeletionSummary:
    """Test get_company_deletion_summary function."""

    async def test_get_company_deletion_summary_returns_accurate_counts(self):
        """get_company_deletion_summary returns summary with correct counts."""
        # Arrange: Mock company
        mock_company = MagicMock()
        mock_company.id = "company:acme"
        mock_company.name = "ACME Corp"
        mock_company.get_member_count = AsyncMock(return_value=3)

        # Mock repo_query to return assignments
        with patch(
            "open_notebook.domain.company_deletion.Company.get",
            return_value=mock_company,
        ):
            with patch("open_notebook.domain.company_deletion.repo_query") as mock_query:
                mock_query.return_value = [
                    {"notebook_id": "notebook:1"},
                    {"notebook_id": "notebook:2"},
                ]

                # Act
                summary = await get_company_deletion_summary("company:acme")

                # Assert
                assert isinstance(summary, CompanyDeletionSummary)
                assert summary.company_id == "company:acme"
                assert summary.company_name == "ACME Corp"
                assert summary.user_count == 3
                assert summary.assignment_count == 2
                assert summary.affected_notebooks == ["notebook:1", "notebook:2"]

    async def test_get_company_deletion_summary_raises_for_missing_company(self):
        """get_company_deletion_summary raises ValueError for non-existent company."""
        with patch(
            "open_notebook.domain.company_deletion.Company.get", return_value=None
        ):
            with pytest.raises(
                ValueError, match="Company company:missing not found"
            ):
                await get_company_deletion_summary("company:missing")

    async def test_get_company_deletion_summary_handles_no_assignments(self):
        """get_company_deletion_summary returns empty list when no assignments."""
        # Arrange
        mock_company = MagicMock()
        mock_company.id = "company:empty"
        mock_company.name = "Empty Co"
        mock_company.get_member_count = AsyncMock(return_value=0)

        with patch(
            "open_notebook.domain.company_deletion.Company.get",
            return_value=mock_company,
        ):
            with patch("open_notebook.domain.company_deletion.repo_query") as mock_query:
                mock_query.return_value = None  # No assignments

                # Act
                summary = await get_company_deletion_summary("company:empty")

                # Assert
                assert summary.assignment_count == 0
                assert summary.affected_notebooks == []


@pytest.mark.asyncio
class TestDeleteCompanyCascade:
    """Test delete_company_cascade function."""

    async def test_delete_company_cascade_removes_all_users(self):
        """delete_company_cascade cascades to all member users."""
        # Arrange: Mock company
        mock_company = MagicMock()
        mock_company.id = "company:test"
        mock_company.delete = AsyncMock()

        # Mock user deletion to return reports
        mock_user_report_1 = UserDeletionReport(user_id="user:alice", total_deleted=5)
        mock_user_report_2 = UserDeletionReport(user_id="user:bob", total_deleted=3)

        with patch(
            "open_notebook.domain.company_deletion.Company.get",
            return_value=mock_company,
        ):
            with patch("open_notebook.domain.company_deletion.repo_query") as mock_query:
                with patch(
                    "open_notebook.domain.company_deletion.delete_user_cascade"
                ) as mock_delete_user:
                    # Configure mocks
                    mock_query.side_effect = [
                        [{"id": "user:alice"}, {"id": "user:bob"}],  # User list
                        [{"id": "assignment:1"}],  # Assignments
                    ]
                    mock_delete_user.side_effect = [
                        mock_user_report_1,
                        mock_user_report_2,
                    ]

                    # Act
                    report = await delete_company_cascade("company:test")

                    # Assert
                    assert isinstance(report, CompanyDeletionReport)
                    assert report.company_id == "company:test"
                    assert report.deleted_users == 2
                    assert report.deleted_user_data_records == 8  # 5 + 3
                    assert report.deleted_assignments == 1
                    assert report.total_deleted == 10  # 8 + 1 + 1 (company)
                    assert len(report.user_deletion_reports) == 2
                    mock_company.delete.assert_called_once()

    async def test_delete_company_cascade_handles_user_failure(self):
        """delete_company_cascade continues deleting other users if one fails."""
        # Arrange
        mock_company = MagicMock()
        mock_company.id = "company:test"
        mock_company.delete = AsyncMock()

        mock_user_report = UserDeletionReport(user_id="user:bob", total_deleted=3)

        with patch(
            "open_notebook.domain.company_deletion.Company.get",
            return_value=mock_company,
        ):
            with patch("open_notebook.domain.company_deletion.repo_query") as mock_query:
                with patch(
                    "open_notebook.domain.company_deletion.delete_user_cascade"
                ) as mock_delete_user:
                    mock_query.side_effect = [
                        [{"id": "user:alice"}, {"id": "user:bob"}],  # User list
                        [],  # Assignments
                    ]
                    # First user fails, second succeeds
                    mock_delete_user.side_effect = [
                        Exception("User deletion failed"),
                        mock_user_report,
                    ]

                    # Act: Should not raise exception
                    report = await delete_company_cascade("company:test")

                    # Assert: One user deleted, one failed
                    assert report.deleted_users == 1
                    assert report.deleted_user_data_records == 3
                    assert len(report.user_deletion_reports) == 1
                    mock_company.delete.assert_called_once()

    async def test_delete_company_cascade_raises_for_missing_company(self):
        """delete_company_cascade raises ValueError for non-existent company."""
        with patch(
            "open_notebook.domain.company_deletion.Company.get", return_value=None
        ):
            with pytest.raises(
                ValueError, match="Company company:missing not found"
            ):
                await delete_company_cascade("company:missing")

    async def test_delete_company_cascade_handles_empty_company(self):
        """delete_company_cascade handles company with no users or assignments."""
        # Arrange
        mock_company = MagicMock()
        mock_company.id = "company:empty"
        mock_company.delete = AsyncMock()

        with patch(
            "open_notebook.domain.company_deletion.Company.get",
            return_value=mock_company,
        ):
            with patch("open_notebook.domain.company_deletion.repo_query") as mock_query:
                mock_query.side_effect = [
                    None,  # No users
                    None,  # No assignments
                ]

                # Act
                report = await delete_company_cascade("company:empty")

                # Assert
                assert report.deleted_users == 0
                assert report.deleted_user_data_records == 0
                assert report.deleted_assignments == 0
                assert report.total_deleted == 1  # Just the company record
                mock_company.delete.assert_called_once()
