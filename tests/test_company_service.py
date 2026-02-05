"""
Tests for company service functions.
"""

import os
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

# Set JWT secret for tests before importing modules
os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-testing-only"

from api.company_service import (
    create_company,
    get_company_by_id,
    get_company_by_slug,
    list_companies,
    list_companies_with_counts,
    update_company,
    delete_company,
    get_company_user_count,
    get_company_assignment_count,
)


class TestCreateCompany:
    """Test company creation."""

    @pytest.mark.asyncio
    async def test_create_company_success(self):
        """Company creation should succeed with valid data."""
        mock_company = MagicMock()
        mock_company.id = "company:test123"
        mock_company.name = "Test Company"
        mock_company.slug = "test-company"
        mock_company.description = "A test company"

        with patch("api.company_service.Company") as MockCompany:
            MockCompany.get_by_slug = AsyncMock(return_value=None)
            MockCompany.return_value = mock_company
            mock_company.save = AsyncMock()

            company = await create_company(
                name="Test Company",
                slug="test-company",
                description="A test company",
            )

            assert company.name == "Test Company"
            assert company.slug == "test-company"
            mock_company.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_company_duplicate_slug(self):
        """Company creation should fail for duplicate slug."""
        mock_existing = MagicMock()
        mock_existing.slug = "existing-slug"

        with patch("api.company_service.Company") as MockCompany:
            MockCompany.get_by_slug = AsyncMock(return_value=mock_existing)

            with pytest.raises(ValueError) as exc_info:
                await create_company(
                    name="New Company",
                    slug="existing-slug",
                )
            assert "already exists" in str(exc_info.value)


class TestListCompanies:
    """Test listing companies."""

    @pytest.mark.asyncio
    async def test_list_companies_success(self):
        """List companies should return all companies."""
        mock_company1 = MagicMock()
        mock_company1.id = "company:1"
        mock_company1.name = "Company 1"

        mock_company2 = MagicMock()
        mock_company2.id = "company:2"
        mock_company2.name = "Company 2"

        with patch("api.company_service.Company") as MockCompany:
            MockCompany.get_all = AsyncMock(return_value=[mock_company1, mock_company2])

            companies = await list_companies()

            assert len(companies) == 2
            assert companies[0].name == "Company 1"
            assert companies[1].name == "Company 2"

    @pytest.mark.asyncio
    async def test_list_companies_with_counts_success(self):
        """list_companies_with_counts should return companies with batch-loaded counts."""
        mock_company1 = MagicMock()
        mock_company1.id = "company:1"
        mock_company1.name = "Company 1"

        mock_company2 = MagicMock()
        mock_company2.id = "company:2"
        mock_company2.name = "Company 2"

        mock_company3 = MagicMock()
        mock_company3.id = "company:3"
        mock_company3.name = "Company 3"

        with patch("api.company_service.Company") as MockCompany:
            MockCompany.get_all = AsyncMock(
                return_value=[mock_company1, mock_company2, mock_company3]
            )
            MockCompany.get_all_user_counts = AsyncMock(
                return_value={"company:1": 5, "company:2": 10}
            )
            MockCompany.get_all_assignment_counts = AsyncMock(
                return_value={"company:1": 2, "company:3": 7}
            )

            results = await list_companies_with_counts()

            assert len(results) == 3
            # Company 1: 5 users, 2 assignments
            assert results[0][0].name == "Company 1"
            assert results[0][1] == 5
            assert results[0][2] == 2
            # Company 2: 10 users, 0 assignments
            assert results[1][0].name == "Company 2"
            assert results[1][1] == 10
            assert results[1][2] == 0
            # Company 3: 0 users, 7 assignments
            assert results[2][0].name == "Company 3"
            assert results[2][1] == 0
            assert results[2][2] == 7

    @pytest.mark.asyncio
    async def test_list_companies_with_counts_empty(self):
        """list_companies_with_counts should handle empty company list."""
        with patch("api.company_service.Company") as MockCompany:
            MockCompany.get_all = AsyncMock(return_value=[])
            MockCompany.get_all_user_counts = AsyncMock(return_value={})
            MockCompany.get_all_assignment_counts = AsyncMock(return_value={})

            results = await list_companies_with_counts()

            assert len(results) == 0


class TestUpdateCompany:
    """Test company update."""

    @pytest.mark.asyncio
    async def test_update_company_success(self):
        """Company update should succeed with valid data."""
        mock_company = MagicMock()
        mock_company.id = "company:test123"
        mock_company.name = "Original Name"
        mock_company.slug = "original-slug"
        mock_company.description = None

        with patch("api.company_service.get_company_by_id") as mock_get:
            mock_get.return_value = mock_company
            mock_company.save = AsyncMock()

            with patch("api.company_service.Company") as MockCompany:
                MockCompany.get_by_slug = AsyncMock(return_value=None)

                company = await update_company(
                    company_id="company:test123",
                    name="Updated Name",
                )

                assert mock_company.name == "Updated Name"
                mock_company.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_company_not_found(self):
        """Company update should return None for non-existent company."""
        with patch("api.company_service.get_company_by_id") as mock_get:
            mock_get.return_value = None

            result = await update_company(
                company_id="company:nonexistent",
                name="Updated Name",
            )

            assert result is None

    @pytest.mark.asyncio
    async def test_update_company_duplicate_slug(self):
        """Company update should fail for duplicate slug."""
        mock_company = MagicMock()
        mock_company.id = "company:test123"
        mock_company.slug = "original-slug"

        mock_existing = MagicMock()
        mock_existing.id = "company:other"
        mock_existing.slug = "taken-slug"

        with patch("api.company_service.get_company_by_id") as mock_get:
            mock_get.return_value = mock_company

            with patch("api.company_service.Company") as MockCompany:
                MockCompany.get_by_slug = AsyncMock(return_value=mock_existing)

                with pytest.raises(ValueError) as exc_info:
                    await update_company(
                        company_id="company:test123",
                        slug="taken-slug",
                    )
                assert "already exists" in str(exc_info.value)


class TestDeleteCompany:
    """Test company deletion."""

    @pytest.mark.asyncio
    async def test_delete_company_success(self):
        """Company deletion should succeed when no users or assignments."""
        mock_company = MagicMock()
        mock_company.id = "company:test123"
        mock_company.name = "Test Company"
        mock_company.delete = AsyncMock()

        with patch("api.company_service.get_company_by_id") as mock_get:
            mock_get.return_value = mock_company

            with patch("api.company_service.Company") as MockCompany:
                MockCompany.get_user_count = AsyncMock(return_value=0)
                MockCompany.get_assignment_count = AsyncMock(return_value=0)

                result = await delete_company("company:test123")

                assert result is True
                mock_company.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_company_not_found(self):
        """Company deletion should return False for non-existent company."""
        with patch("api.company_service.get_company_by_id") as mock_get:
            mock_get.return_value = None

            result = await delete_company("company:nonexistent")

            assert result is False

    @pytest.mark.asyncio
    async def test_delete_company_with_users(self):
        """Company deletion should fail when company has assigned users."""
        mock_company = MagicMock()
        mock_company.id = "company:test123"
        mock_company.name = "Test Company"

        with patch("api.company_service.get_company_by_id") as mock_get:
            mock_get.return_value = mock_company

            with patch("api.company_service.Company") as MockCompany:
                MockCompany.get_user_count = AsyncMock(return_value=5)
                MockCompany.get_assignment_count = AsyncMock(return_value=0)

                with pytest.raises(ValueError) as exc_info:
                    await delete_company("company:test123")
                assert "5 assigned learners" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_delete_company_with_assignments(self):
        """Company deletion should fail when company has module assignments."""
        mock_company = MagicMock()
        mock_company.id = "company:test123"
        mock_company.name = "Test Company"

        with patch("api.company_service.get_company_by_id") as mock_get:
            mock_get.return_value = mock_company

            with patch("api.company_service.Company") as MockCompany:
                MockCompany.get_user_count = AsyncMock(return_value=0)
                MockCompany.get_assignment_count = AsyncMock(return_value=3)

                with pytest.raises(ValueError) as exc_info:
                    await delete_company("company:test123")
                assert "3 assigned modules" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_delete_company_with_users_and_assignments(self):
        """Company deletion should fail with combined error for users AND assignments."""
        mock_company = MagicMock()
        mock_company.id = "company:test123"
        mock_company.name = "Test Company"

        with patch("api.company_service.get_company_by_id") as mock_get:
            mock_get.return_value = mock_company

            with patch("api.company_service.Company") as MockCompany:
                MockCompany.get_user_count = AsyncMock(return_value=5)
                MockCompany.get_assignment_count = AsyncMock(return_value=3)

                with pytest.raises(ValueError) as exc_info:
                    await delete_company("company:test123")
                error_msg = str(exc_info.value)
                assert "5 assigned learners" in error_msg
                assert "3 assigned modules" in error_msg
                assert "Reassign or remove them first" in error_msg


class TestGetCompanyCounts:
    """Test company count functions."""

    @pytest.mark.asyncio
    async def test_get_company_user_count(self):
        """get_company_user_count should return count from domain model."""
        with patch("api.company_service.Company") as MockCompany:
            MockCompany.get_user_count = AsyncMock(return_value=10)

            count = await get_company_user_count("company:test123")

            assert count == 10
            MockCompany.get_user_count.assert_called_once_with("company:test123")

    @pytest.mark.asyncio
    async def test_get_company_assignment_count(self):
        """get_company_assignment_count should return count from domain model."""
        with patch("api.company_service.Company") as MockCompany:
            MockCompany.get_assignment_count = AsyncMock(return_value=7)

            count = await get_company_assignment_count("company:test123")

            assert count == 7
            MockCompany.get_assignment_count.assert_called_once_with("company:test123")
