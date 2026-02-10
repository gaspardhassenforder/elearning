"""
Tests for learner onboarding questionnaire (Story 1.4).

Tests the PUT /auth/me/onboarding endpoint: happy path, validation,
authentication, role restrictions, and idempotency.
"""

import os
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

# Set JWT secret for tests before importing auth modules
os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-testing-only"

from api.auth import (
    create_access_token,
    get_current_user,
    hash_password,
)
from api.models import OnboardingSubmit, OnboardingResponse


class TestOnboardingModels:
    """Test Pydantic models for onboarding."""

    def test_onboarding_submit_valid(self):
        """Valid onboarding data should be accepted."""
        data = OnboardingSubmit(
            ai_familiarity="used_occasionally",
            job_type="Project Manager",
            job_description="I coordinate teams and track deliverables across projects",
        )
        assert data.ai_familiarity == "used_occasionally"
        assert data.job_type == "Project Manager"

    def test_onboarding_submit_all_familiarity_levels(self):
        """All AI familiarity levels should be accepted."""
        for level in ["never_used", "used_occasionally", "use_regularly", "power_user"]:
            data = OnboardingSubmit(
                ai_familiarity=level,
                job_type="Tester",
                job_description="Testing all familiarity levels works",
            )
            assert data.ai_familiarity == level

    def test_onboarding_submit_invalid_familiarity(self):
        """Invalid AI familiarity value should be rejected."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            OnboardingSubmit(
                ai_familiarity="expert",  # Not a valid option
                job_type="Tester",
                job_description="This should fail validation",
            )

    def test_onboarding_submit_empty_job_type(self):
        """Empty job_type should be rejected."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            OnboardingSubmit(
                ai_familiarity="never_used",
                job_type="",
                job_description="Valid description here for testing",
            )

    def test_onboarding_submit_short_job_description(self):
        """Job description shorter than 10 chars should be rejected."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            OnboardingSubmit(
                ai_familiarity="never_used",
                job_type="Manager",
                job_description="Short",  # Less than 10 chars
            )

    def test_onboarding_response_model(self):
        """OnboardingResponse should contain all required fields."""
        response = OnboardingResponse(
            success=True,
            message="Onboarding completed",
            profile={"ai_familiarity": "power_user", "job_type": "Engineer"},
        )
        assert response.success is True
        assert response.profile["ai_familiarity"] == "power_user"


class TestOnboardingEndpoint:
    """Test the onboarding endpoint logic."""

    @pytest.mark.asyncio
    async def test_submit_onboarding_happy_path(self):
        """Learner should be able to complete onboarding successfully."""
        from api.routers.auth import submit_onboarding

        mock_user = MagicMock()
        mock_user.id = "user:learner123"
        mock_user.username = "testlearner"
        mock_user.role = "learner"
        mock_user.onboarding_completed = False
        mock_user.profile = None
        mock_user.save = AsyncMock()

        data = OnboardingSubmit(
            ai_familiarity="used_occasionally",
            job_type="Data Analyst",
            job_description="I analyze business data and create reports for stakeholders",
        )

        result = await submit_onboarding(data, mock_user)

        assert result.success is True
        assert result.message == "Onboarding completed successfully"
        assert result.profile["ai_familiarity"] == "used_occasionally"
        assert result.profile["job_type"] == "Data Analyst"
        assert mock_user.onboarding_completed is True
        assert mock_user.profile is not None
        mock_user.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_submit_onboarding_admin_rejected(self):
        """Admin users should be rejected from onboarding."""
        from fastapi import HTTPException
        from api.routers.auth import submit_onboarding

        mock_user = MagicMock()
        mock_user.id = "user:admin123"
        mock_user.role = "admin"
        mock_user.onboarding_completed = False

        data = OnboardingSubmit(
            ai_familiarity="power_user",
            job_type="Admin",
            job_description="I manage the platform and its content",
        )

        with pytest.raises(HTTPException) as exc_info:
            await submit_onboarding(data, mock_user)
        assert exc_info.value.status_code == 403
        assert "Only learners" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_submit_onboarding_already_completed(self):
        """Onboarding should not be allowed twice."""
        from fastapi import HTTPException
        from api.routers.auth import submit_onboarding

        mock_user = MagicMock()
        mock_user.id = "user:learner456"
        mock_user.role = "learner"
        mock_user.onboarding_completed = True  # Already done

        data = OnboardingSubmit(
            ai_familiarity="never_used",
            job_type="Manager",
            job_description="I manage teams of ten or more people",
        )

        with pytest.raises(HTTPException) as exc_info:
            await submit_onboarding(data, mock_user)
        assert exc_info.value.status_code == 400
        assert "already completed" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_submit_onboarding_stores_profile(self):
        """Profile should be stored with all questionnaire fields."""
        from api.routers.auth import submit_onboarding

        mock_user = MagicMock()
        mock_user.id = "user:learner789"
        mock_user.username = "profiletest"
        mock_user.role = "learner"
        mock_user.onboarding_completed = False
        mock_user.profile = None
        mock_user.save = AsyncMock()

        data = OnboardingSubmit(
            ai_familiarity="use_regularly",
            job_type="Software Engineer",
            job_description="I build web applications and APIs for our clients",
        )

        result = await submit_onboarding(data, mock_user)

        # Verify all profile fields stored
        assert mock_user.profile["ai_familiarity"] == "use_regularly"
        assert mock_user.profile["job_type"] == "Software Engineer"
        assert mock_user.profile["job_description"] == "I build web applications and APIs for our clients"

    @pytest.mark.asyncio
    async def test_submit_onboarding_save_failure(self):
        """Save failure should return 500."""
        from fastapi import HTTPException
        from api.routers.auth import submit_onboarding

        mock_user = MagicMock()
        mock_user.id = "user:learner_fail"
        mock_user.username = "failuser"
        mock_user.role = "learner"
        mock_user.onboarding_completed = False
        mock_user.profile = None
        mock_user.save = AsyncMock(side_effect=RuntimeError("DB connection failed"))

        data = OnboardingSubmit(
            ai_familiarity="never_used",
            job_type="Tester",
            job_description="I test things that should fail gracefully",
        )

        with pytest.raises(HTTPException) as exc_info:
            await submit_onboarding(data, mock_user)
        assert exc_info.value.status_code == 500


class TestOnboardingAuth:
    """Test authentication requirements for onboarding."""

    @pytest.mark.asyncio
    async def test_unauthenticated_request_rejected(self):
        """Unauthenticated user should get 401."""
        from fastapi import HTTPException

        mock_request = MagicMock()
        mock_request.cookies.get.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(mock_request)
        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_authenticated_learner_accepted(self):
        """Authenticated learner should pass auth check."""
        mock_user = MagicMock()
        mock_user.id = "user:learner_auth"
        mock_user.role = "learner"
        mock_user.onboarding_completed = False

        token = create_access_token(
            user_id="user:learner_auth",
            role="learner",
        )

        mock_request = MagicMock()
        mock_request.cookies.get.return_value = token

        with patch("api.auth.User") as MockUser:
            MockUser.get = AsyncMock(return_value=mock_user)
            user = await get_current_user(mock_request)
            assert user.id == "user:learner_auth"
            assert user.onboarding_completed is False
