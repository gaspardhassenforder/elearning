"""
Tests for JWT authentication system.
"""

import os
import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

# Set JWT secret for tests before importing auth modules
os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-testing-only"

from api.auth import (
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
    verify_token,
    get_current_user,
    require_admin,
    require_learner,
    get_current_learner,
    is_jwt_enabled,
    LearnerContext,
)
from api.user_service import register_user, authenticate_user, get_user_by_id
from api.models import UserCreate, UserLogin, UserResponse


class TestPasswordHashing:
    """Test password hashing functions."""

    def test_hash_password_returns_hash(self):
        """Hash should not equal plain password."""
        password = "testpassword123"
        hashed = hash_password(password)
        assert hashed != password
        assert len(hashed) > 0

    def test_verify_password_correct(self):
        """Verify should return True for correct password."""
        password = "testpassword123"
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """Verify should return False for wrong password."""
        password = "testpassword123"
        hashed = hash_password(password)
        assert verify_password("wrongpassword", hashed) is False


class TestJWTTokens:
    """Test JWT token creation and verification."""

    def test_create_access_token(self):
        """Access token should be created with correct claims."""
        token = create_access_token(
            user_id="user:123",
            role="learner",
            company_id="company:abc",
        )
        assert token is not None
        payload = verify_token(token)
        assert payload["sub"] == "user:123"
        assert payload["role"] == "learner"
        assert payload["company_id"] == "company:abc"
        assert payload["type"] == "access"

    def test_create_access_token_without_company(self):
        """Access token should work without company_id."""
        token = create_access_token(
            user_id="user:456",
            role="admin",
        )
        payload = verify_token(token)
        assert payload["sub"] == "user:456"
        assert payload["role"] == "admin"
        assert payload["company_id"] is None

    def test_create_refresh_token(self):
        """Refresh token should be created with correct claims."""
        token = create_refresh_token(user_id="user:789")
        payload = verify_token(token)
        assert payload["sub"] == "user:789"
        assert payload["type"] == "refresh"

    def test_verify_token_invalid(self):
        """Verify should raise HTTPException for invalid token."""
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            verify_token("invalid-token")
        assert exc_info.value.status_code == 401

    def test_is_jwt_enabled(self):
        """JWT should be enabled when secret is set."""
        assert is_jwt_enabled() is True


class TestUserService:
    """Test user service functions."""

    @pytest.mark.asyncio
    async def test_register_user_success(self):
        """User registration should create user with hashed password."""
        mock_user = MagicMock()
        mock_user.id = "user:new123"
        mock_user.username = "newuser"
        mock_user.email = "new@test.com"
        mock_user.role = "learner"

        with patch("api.user_service.User") as MockUser:
            MockUser.get_by_username = AsyncMock(return_value=None)
            MockUser.get_by_email = AsyncMock(return_value=None)
            MockUser.return_value = mock_user
            mock_user.save = AsyncMock()

            user = await register_user(
                username="newuser",
                email="new@test.com",
                password="password123",
            )

            assert user.username == "newuser"
            mock_user.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_register_user_duplicate_username(self):
        """Registration should fail for duplicate username."""
        mock_existing = MagicMock()
        mock_existing.username = "existing"

        with patch("api.user_service.User") as MockUser:
            MockUser.get_by_username = AsyncMock(return_value=mock_existing)

            with pytest.raises(ValueError) as exc_info:
                await register_user(
                    username="existing",
                    email="new@test.com",
                    password="password123",
                )
            assert "already taken" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_register_user_duplicate_email(self):
        """Registration should fail for duplicate email."""
        mock_existing = MagicMock()
        mock_existing.email = "existing@test.com"

        with patch("api.user_service.User") as MockUser:
            MockUser.get_by_username = AsyncMock(return_value=None)
            MockUser.get_by_email = AsyncMock(return_value=mock_existing)

            with pytest.raises(ValueError) as exc_info:
                await register_user(
                    username="newuser",
                    email="existing@test.com",
                    password="password123",
                )
            assert "already registered" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_register_user_short_password(self):
        """Registration should fail for short password."""
        with pytest.raises(ValueError) as exc_info:
            await register_user(
                username="newuser",
                email="new@test.com",
                password="short",
            )
        assert "at least 8 characters" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_register_user_short_username(self):
        """Registration should fail for short username."""
        with pytest.raises(ValueError) as exc_info:
            await register_user(
                username="ab",
                email="new@test.com",
                password="password123",
            )
        assert "at least 3 characters" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_authenticate_user_success(self):
        """Authentication should succeed with correct credentials."""
        password = "testpassword123"
        mock_user = MagicMock()
        mock_user.password_hash = hash_password(password)

        with patch("api.user_service.User") as MockUser:
            MockUser.get_by_username = AsyncMock(return_value=mock_user)

            user = await authenticate_user("testuser", password)
            assert user is not None

    @pytest.mark.asyncio
    async def test_authenticate_user_wrong_password(self):
        """Authentication should fail with wrong password."""
        mock_user = MagicMock()
        mock_user.password_hash = hash_password("correctpassword")

        with patch("api.user_service.User") as MockUser:
            MockUser.get_by_username = AsyncMock(return_value=mock_user)

            user = await authenticate_user("testuser", "wrongpassword")
            assert user is None

    @pytest.mark.asyncio
    async def test_authenticate_user_not_found(self):
        """Authentication should fail for nonexistent user."""
        with patch("api.user_service.User") as MockUser:
            MockUser.get_by_username = AsyncMock(return_value=None)

            user = await authenticate_user("nonexistent", "password123")
            assert user is None


class TestGetCurrentUser:
    """Test get_current_user dependency."""

    @pytest.mark.asyncio
    async def test_get_current_user_success(self):
        """Should return user for valid token."""
        mock_user = MagicMock()
        mock_user.id = "user:test123"
        mock_user.role = "learner"

        token = create_access_token(
            user_id="user:test123",
            role="learner",
        )

        mock_request = MagicMock()
        mock_request.cookies.get.return_value = token

        with patch("api.auth.User") as MockUser:
            MockUser.get = AsyncMock(return_value=mock_user)

            user = await get_current_user(mock_request)
            assert user.id == "user:test123"

    @pytest.mark.asyncio
    async def test_get_current_user_no_token(self):
        """Should raise 401 when no token provided."""
        from fastapi import HTTPException

        mock_request = MagicMock()
        mock_request.cookies.get.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(mock_request)
        assert exc_info.value.status_code == 401
        assert "Not authenticated" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token(self):
        """Should raise 401 for invalid token."""
        from fastapi import HTTPException

        mock_request = MagicMock()
        mock_request.cookies.get.return_value = "invalid-token"

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(mock_request)
        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_get_current_user_refresh_token_rejected(self):
        """Should reject refresh token as access token."""
        from fastapi import HTTPException

        refresh_token = create_refresh_token(user_id="user:test123")

        mock_request = MagicMock()
        mock_request.cookies.get.return_value = refresh_token

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(mock_request)
        assert exc_info.value.status_code == 401
        assert "Invalid token type" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_get_current_user_user_not_found(self):
        """Should raise 401 when user not found."""
        from fastapi import HTTPException
        from open_notebook.exceptions import NotFoundError

        token = create_access_token(
            user_id="user:deleted123",
            role="learner",
        )

        mock_request = MagicMock()
        mock_request.cookies.get.return_value = token

        with patch("open_notebook.domain.user.User.get", new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = NotFoundError("User not found")

            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(mock_request)
            assert exc_info.value.status_code == 401


class TestPydanticModels:
    """Test Pydantic models for auth."""

    def test_user_create_valid(self):
        """UserCreate should accept valid data."""
        user = UserCreate(
            username="testuser",
            email="test@example.com",
            password="password123",
        )
        assert user.username == "testuser"
        assert user.email == "test@example.com"

    def test_user_create_short_username(self):
        """UserCreate should reject short username."""
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            UserCreate(
                username="ab",
                email="test@example.com",
                password="password123",
            )

    def test_user_create_short_password(self):
        """UserCreate should reject short password."""
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            UserCreate(
                username="testuser",
                email="test@example.com",
                password="short",
            )

    def test_user_login_valid(self):
        """UserLogin should accept valid data."""
        login = UserLogin(
            username="testuser",
            password="password123",
        )
        assert login.username == "testuser"

    def test_user_response(self):
        """UserResponse should contain all required fields."""
        response = UserResponse(
            id="user:123",
            username="testuser",
            email="test@example.com",
            role="learner",
            company_id=None,
            onboarding_completed=False,
        )
        assert response.id == "user:123"
        assert response.role == "learner"


class TestRequireAdmin:
    """Test require_admin dependency (Task 13.2)."""

    @pytest.mark.asyncio
    async def test_require_admin_with_admin_user(self):
        """Admin user should pass require_admin check."""
        mock_user = MagicMock()
        mock_user.id = "user:admin123"
        mock_user.role = "admin"

        # require_admin just checks the role of the user passed to it
        result = await require_admin(mock_user)
        assert result.id == "user:admin123"
        assert result.role == "admin"

    @pytest.mark.asyncio
    async def test_require_admin_with_learner_user(self):
        """Learner user should get 403 from require_admin."""
        from fastapi import HTTPException

        mock_user = MagicMock()
        mock_user.id = "user:learner123"
        mock_user.role = "learner"

        with pytest.raises(HTTPException) as exc_info:
            await require_admin(mock_user)
        assert exc_info.value.status_code == 403
        assert "Admin access required" in str(exc_info.value.detail)


class TestRequireLearner:
    """Test require_learner dependency (Task 13.3)."""

    @pytest.mark.asyncio
    async def test_require_learner_with_learner_user(self):
        """Learner user should pass require_learner check."""
        mock_user = MagicMock()
        mock_user.id = "user:learner123"
        mock_user.role = "learner"

        result = await require_learner(mock_user)
        assert result.id == "user:learner123"
        assert result.role == "learner"

    @pytest.mark.asyncio
    async def test_require_learner_with_admin_user(self):
        """Admin user should get 403 from require_learner."""
        from fastapi import HTTPException

        mock_user = MagicMock()
        mock_user.id = "user:admin123"
        mock_user.role = "admin"

        with pytest.raises(HTTPException) as exc_info:
            await require_learner(mock_user)
        assert exc_info.value.status_code == 403
        assert "Learner access required" in str(exc_info.value.detail)


class TestGetCurrentLearner:
    """Test get_current_learner dependency (Task 13.4)."""

    @pytest.mark.asyncio
    async def test_get_current_learner_with_company_id(self):
        """Learner with company_id should pass get_current_learner check."""
        mock_user = MagicMock()
        mock_user.id = "user:learner123"
        mock_user.role = "learner"
        mock_user.company_id = "company:abc123"

        result = await get_current_learner(mock_user)
        assert isinstance(result, LearnerContext)
        assert result.user.id == "user:learner123"
        assert result.company_id == "company:abc123"

    @pytest.mark.asyncio
    async def test_get_current_learner_without_company_id(self):
        """Learner without company_id should get 403."""
        from fastapi import HTTPException

        mock_user = MagicMock()
        mock_user.id = "user:learner123"
        mock_user.role = "learner"
        mock_user.company_id = None

        with pytest.raises(HTTPException) as exc_info:
            await get_current_learner(mock_user)
        assert exc_info.value.status_code == 403
        assert "Learner must be assigned to a company" in str(exc_info.value.detail)


class TestExpiredToken:
    """Test expired token handling (Task 13.7)."""

    @pytest.mark.asyncio
    async def test_expired_access_token(self):
        """Expired token should return 401."""
        from fastapi import HTTPException
        from jose import jwt

        # Create an already-expired token
        expired_payload = {
            "sub": "user:test123",
            "role": "learner",
            "company_id": None,
            "type": "access",
            "exp": datetime.now(timezone.utc) - timedelta(hours=1),  # 1 hour ago
        }
        expired_token = jwt.encode(
            expired_payload,
            os.environ["JWT_SECRET_KEY"],
            algorithm="HS256",
        )

        mock_request = MagicMock()
        mock_request.cookies.get.return_value = expired_token

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(mock_request)
        assert exc_info.value.status_code == 401
