"""
Authentication router for Open Notebook API.
Provides JWT-based registration, login, token refresh, logout, and user info endpoints.
"""

import os

from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.requests import Request
from loguru import logger

from api.auth import (
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES,
    JWT_REFRESH_TOKEN_EXPIRE_DAYS,
    create_access_token,
    create_refresh_token,
    get_current_user,
    is_jwt_enabled,
    verify_token,
)
from api.models import OnboardingSubmit, OnboardingResponse, UserCreate, UserLogin, UserResponse
from api.user_service import authenticate_user, register_user

# In local dev (HTTP), cookies with secure=True are silently dropped by browsers.
# Only set secure=True when explicitly configured for production (HTTPS).
COOKIE_SECURE = os.environ.get("COOKIE_SECURE", "false").lower() == "true"
from open_notebook.domain.user import User

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse)
async def register(user_data: UserCreate):
    """Register a new user account."""
    try:
        user = await register_user(
            username=user_data.username,
            email=user_data.email,
            password=user_data.password,
        )
        return UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            role=user.role,
            company_id=user.company_id,
            onboarding_completed=user.onboarding_completed,
        )
    except ValueError as e:
        logger.error("Registration failed: {}", str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Registration error: {}", str(e))
        raise HTTPException(status_code=500, detail="Registration failed")


@router.post("/login")
async def login(user_data: UserLogin, response: Response):
    """Authenticate user and set JWT cookies."""
    try:
        user = await authenticate_user(
            username=user_data.username,
            password=user_data.password,
        )
        if not user:
            logger.error(f"Login failed for user: {user_data.username}")
            raise HTTPException(status_code=401, detail="Invalid credentials")

        access_token = create_access_token(
            user_id=user.id,
            role=user.role,
            company_id=user.company_id,
        )
        refresh_token = create_refresh_token(user_id=user.id)

        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            secure=COOKIE_SECURE,
            samesite="lax",
            max_age=JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            path="/",
        )
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=COOKIE_SECURE,
            samesite="lax",
            max_age=JWT_REFRESH_TOKEN_EXPIRE_DAYS * 86400,
            path="/api/auth/refresh",
        )

        return {
            "id": user.id,
            "username": user.username,
            "role": user.role,
            "company_id": user.company_id,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Login error: {}", str(e))
        raise HTTPException(status_code=500, detail="Login failed")


@router.post("/refresh")
async def refresh(request: Request, response: Response):
    """Refresh access token using refresh token cookie."""
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        logger.error("No refresh_token cookie found")
        raise HTTPException(status_code=401, detail="No refresh token")

    try:
        payload = verify_token(refresh_token)
        if payload.get("type") != "refresh":
            logger.error("Token type is not 'refresh'")
            raise HTTPException(status_code=401, detail="Invalid token type")

        user_id = payload.get("sub")
        user = await User.get(user_id)
        if not user:
            logger.error(f"User not found during refresh: {user_id}")
            raise HTTPException(status_code=401, detail="User not found")

        access_token = create_access_token(
            user_id=user.id,
            role=user.role,
            company_id=user.company_id,
        )

        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            secure=COOKIE_SECURE,
            samesite="lax",
            max_age=JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            path="/",
        )

        return {"message": "Token refreshed"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Token refresh error: {}", str(e))
        raise HTTPException(status_code=401, detail="Invalid refresh token")


@router.post("/logout")
async def logout(response: Response):
    """Clear authentication cookies."""
    response.delete_cookie(key="access_token", path="/")
    response.delete_cookie(key="refresh_token", path="/api/auth/refresh")
    return {"message": "Logged out"}


@router.get("/me", response_model=UserResponse)
async def get_me(current_user=Depends(get_current_user)):
    """Return current authenticated user info."""
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        role=current_user.role,
        company_id=current_user.company_id,
        onboarding_completed=current_user.onboarding_completed,
    )


@router.get("/status")
async def get_auth_status():
    """Check if authentication is enabled (backward compatibility)."""
    return {
        "auth_enabled": True,
        "jwt_enabled": is_jwt_enabled(),
    }


@router.put("/me/onboarding", response_model=OnboardingResponse)
async def submit_onboarding(
    onboarding_data: OnboardingSubmit, current_user=Depends(get_current_user)
):
    """
    Submit onboarding questionnaire (learners only).
    Stores questionnaire responses in user profile and marks onboarding as complete.
    """
    if current_user.role != "learner":
        raise HTTPException(
            status_code=403, detail="Only learners can complete onboarding"
        )

    if current_user.onboarding_completed:
        raise HTTPException(status_code=400, detail="Onboarding already completed")

    try:
        # Build profile from questionnaire responses
        profile = {
            "ai_familiarity": onboarding_data.ai_familiarity,
            "job_type": onboarding_data.job_type,
            "job_description": onboarding_data.job_description,
        }

        # Update user profile and mark onboarding complete
        current_user.profile = profile
        current_user.onboarding_completed = True
        await current_user.save()

        logger.info(f"Onboarding completed for user: {current_user.username}")

        return OnboardingResponse(
            success=True,
            message="Onboarding completed successfully",
            profile=profile,
        )
    except Exception as e:
        logger.error("Onboarding submission failed for {}: {}", current_user.username, str(e))
        raise HTTPException(status_code=500, detail="Failed to save onboarding data")
