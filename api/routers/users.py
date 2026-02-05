from typing import List

from fastapi import APIRouter, Depends, HTTPException
from loguru import logger

from api.auth import require_admin
from api.models import AdminUserCreate, UserListResponse, UserResponse, UserUpdate
from api.user_service import (
    create_user_admin,
    delete_user,
    get_user_by_id,
    list_users,
    update_user,
)
from open_notebook.domain.user import User

router = APIRouter()


@router.post("/users", response_model=UserResponse, status_code=201)
async def create_user(data: AdminUserCreate, _admin: User = Depends(require_admin)):
    """Admin creates a new user (learner or admin)."""
    try:
        user = await create_user_admin(
            username=data.username,
            email=data.email,
            password=data.password,
            role=data.role,
            company_id=data.company_id,
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
        logger.error(f"User creation failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error creating user: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/users", response_model=List[UserListResponse])
async def get_users(_admin: User = Depends(require_admin)):
    """List all users with company names."""
    try:
        return await list_users()
    except Exception as e:
        logger.error(f"Error listing users: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: str, _admin: User = Depends(require_admin)):
    """Get single user details."""
    try:
        user = await get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            role=user.role,
            company_id=user.company_id,
            onboarding_completed=user.onboarding_completed,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user_endpoint(
    user_id: str, data: UserUpdate, _admin: User = Depends(require_admin)
):
    """Update user fields."""
    try:
        user = await update_user(
            user_id=user_id,
            username=data.username,
            email=data.email,
            password=data.password,
            role=data.role,
            company_id=data.company_id,
            onboarding_completed=data.onboarding_completed,
        )
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            role=user.role,
            company_id=user.company_id,
            onboarding_completed=user.onboarding_completed,
        )
    except ValueError as e:
        logger.error(f"User update failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error updating user: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/users/{user_id}", status_code=204)
async def delete_user_endpoint(user_id: str, _admin: User = Depends(require_admin)):
    """Delete a user."""
    try:
        deleted = await delete_user(user_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="User not found")
        return None
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
