"""
Tests for user service functions (Story 1.3).
Tests admin user management: create_user_admin, list_users, update_user, delete_user.
"""

import os
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

# Set JWT secret for tests before importing modules
os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-testing-only"

from api.user_service import (
    create_user_admin,
    list_users,
    update_user,
    delete_user,
    get_user_by_id,
    get_user_with_company_name,
)


class TestCreateUserAdmin:
    """Test admin user creation."""

    @pytest.mark.asyncio
    async def test_create_user_admin_success(self):
        """Admin should be able to create a new user with role and company."""
        mock_company = MagicMock()
        mock_company.id = "company:test123"

        mock_user = MagicMock()
        mock_user.id = "user:new123"
        mock_user.username = "testuser"
        mock_user.email = "test@example.com"
        mock_user.role = "learner"
        mock_user.company_id = "company:test123"

        with patch("api.user_service.User") as MockUser:
            MockUser.get_by_username = AsyncMock(return_value=None)
            MockUser.get_by_email = AsyncMock(return_value=None)
            MockUser.return_value = mock_user
            mock_user.save = AsyncMock()

            with patch("open_notebook.domain.company.Company") as MockCompany:
                MockCompany.get = AsyncMock(return_value=mock_company)

                user = await create_user_admin(
                    username="testuser",
                    email="test@example.com",
                    password="password123",
                    role="learner",
                    company_id="company:test123",
                )

                assert user.username == "testuser"
                assert user.role == "learner"
                assert user.company_id == "company:test123"
                mock_user.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_user_admin_company_not_found(self):
        """Admin user creation should fail if company doesn't exist."""
        with patch("api.user_service.User") as MockUser:
            MockUser.get_by_username = AsyncMock(return_value=None)
            MockUser.get_by_email = AsyncMock(return_value=None)

            with patch("open_notebook.domain.company.Company") as MockCompany:
                MockCompany.get = AsyncMock(return_value=None)

                with pytest.raises(ValueError) as exc_info:
                    await create_user_admin(
                        username="testuser",
                        email="test@example.com",
                        password="password123",
                        role="learner",
                        company_id="company:nonexistent",
                    )
                assert "Company not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_user_admin_duplicate_username(self):
        """Admin user creation should fail for duplicate username."""
        mock_existing_user = MagicMock()
        mock_existing_user.username = "existinguser"

        with patch("api.user_service.User") as MockUser:
            MockUser.get_by_username = AsyncMock(return_value=mock_existing_user)

            with pytest.raises(ValueError) as exc_info:
                await create_user_admin(
                    username="existinguser",
                    email="new@example.com",
                    password="password123",
                    role="learner",
                )
            assert "Username already taken" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_user_admin_duplicate_email(self):
        """Admin user creation should fail for duplicate email."""
        mock_existing_user = MagicMock()
        mock_existing_user.email = "existing@example.com"

        with patch("api.user_service.User") as MockUser:
            MockUser.get_by_username = AsyncMock(return_value=None)
            MockUser.get_by_email = AsyncMock(return_value=mock_existing_user)

            with pytest.raises(ValueError) as exc_info:
                await create_user_admin(
                    username="newuser",
                    email="existing@example.com",
                    password="password123",
                    role="learner",
                )
            assert "Email already registered" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_user_admin_invalid_role(self):
        """Admin user creation should fail for invalid role."""
        with patch("api.user_service.User") as MockUser:
            MockUser.get_by_username = AsyncMock(return_value=None)
            MockUser.get_by_email = AsyncMock(return_value=None)

            with pytest.raises(ValueError) as exc_info:
                await create_user_admin(
                    username="testuser",
                    email="test@example.com",
                    password="password123",
                    role="invalid_role",
                )
            assert "Role must be 'admin' or 'learner'" in str(exc_info.value)


class TestListUsers:
    """Test listing users."""

    @pytest.mark.asyncio
    async def test_list_users_success(self):
        """List users should return all users."""
        mock_user1 = MagicMock()
        mock_user1.id = "user:1"
        mock_user1.username = "user1"

        mock_user2 = MagicMock()
        mock_user2.id = "user:2"
        mock_user2.username = "user2"

        with patch("api.user_service.User") as MockUser:
            MockUser.get_all = AsyncMock(return_value=[mock_user1, mock_user2])

            users = await list_users()

            assert len(users) == 2
            assert users[0].username == "user1"
            assert users[1].username == "user2"


class TestUpdateUser:
    """Test updating user fields."""

    @pytest.mark.asyncio
    async def test_update_user_success(self):
        """Update user should modify user fields."""
        mock_user = MagicMock()
        mock_user.id = "user:test123"
        mock_user.username = "oldusername"
        mock_user.email = "old@example.com"
        mock_user.role = "learner"
        mock_user.company_id = "company:old"

        with patch("api.user_service.get_user_by_id", new=AsyncMock(return_value=mock_user)):
            with patch("api.user_service.User") as MockUser:
                MockUser.get_by_username = AsyncMock(return_value=None)
                MockUser.get_by_email = AsyncMock(return_value=None)
                mock_user.save = AsyncMock()

                with patch("open_notebook.domain.company.Company") as MockCompany:
                    MockCompany.get = AsyncMock(return_value=MagicMock())

                    updated_user = await update_user(
                        user_id="user:test123",
                        username="newusername",
                        email="new@example.com",
                        role="admin",
                        company_id="company:new",
                    )

                    assert updated_user is not None
                    assert mock_user.username == "newusername"
                    assert mock_user.email == "new@example.com"
                    assert mock_user.role == "admin"
                    assert mock_user.company_id == "company:new"
                    mock_user.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_user_not_found(self):
        """Update user should return None if user doesn't exist."""
        with patch("api.user_service.get_user_by_id", new=AsyncMock(return_value=None)):
            updated_user = await update_user(
                user_id="user:nonexistent",
                username="newusername",
            )
            assert updated_user is None

    @pytest.mark.asyncio
    async def test_update_user_company_not_found(self):
        """Update user should fail if new company doesn't exist."""
        mock_user = MagicMock()
        mock_user.id = "user:test123"

        with patch("api.user_service.get_user_by_id", new=AsyncMock(return_value=mock_user)):
            with patch("open_notebook.domain.company.Company") as MockCompany:
                MockCompany.get = AsyncMock(return_value=None)

                with pytest.raises(ValueError) as exc_info:
                    await update_user(
                        user_id="user:test123",
                        company_id="company:nonexistent",
                    )
                assert "Company not found" in str(exc_info.value)


class TestDeleteUser:
    """Test deleting users."""

    @pytest.mark.asyncio
    async def test_delete_user_success(self):
        """Delete user should remove user."""
        mock_user = MagicMock()
        mock_user.id = "user:test123"
        mock_user.username = "testuser"
        mock_user.delete = AsyncMock()

        with patch("api.user_service.get_user_by_id", new=AsyncMock(return_value=mock_user)):
            result = await delete_user("user:test123")

            assert result is True
            mock_user.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_user_not_found(self):
        """Delete user should return False if user doesn't exist."""
        with patch("api.user_service.get_user_by_id", new=AsyncMock(return_value=None)):
            result = await delete_user("user:nonexistent")
            assert result is False


class TestGetUserWithCompanyName:
    """Test getting user with company name."""

    @pytest.mark.asyncio
    async def test_get_user_with_company_name_success(self):
        """Should return user data with company name."""
        mock_user = MagicMock()
        mock_user.id = "user:test123"
        mock_user.username = "testuser"
        mock_user.email = "test@example.com"
        mock_user.role = "learner"
        mock_user.company_id = "company:abc"
        mock_user.onboarding_completed = False
        mock_user.created = "2024-01-01"
        mock_user.updated = "2024-01-02"

        mock_company = MagicMock()
        mock_company.name = "Test Company"

        with patch("open_notebook.domain.company.Company") as MockCompany:
            MockCompany.get = AsyncMock(return_value=mock_company)

            result = await get_user_with_company_name(mock_user)

            assert result["id"] == "user:test123"
            assert result["username"] == "testuser"
            assert result["company_name"] == "Test Company"

    @pytest.mark.asyncio
    async def test_get_user_with_company_name_no_company(self):
        """Should return user data with None company name if no company."""
        mock_user = MagicMock()
        mock_user.id = "user:test123"
        mock_user.username = "testuser"
        mock_user.email = "test@example.com"
        mock_user.role = "admin"
        mock_user.company_id = None
        mock_user.onboarding_completed = True
        mock_user.created = "2024-01-01"
        mock_user.updated = "2024-01-02"

        result = await get_user_with_company_name(mock_user)

        assert result["id"] == "user:test123"
        assert result["username"] == "testuser"
        assert result["company_name"] is None
