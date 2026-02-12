from typing import List

from fastapi import APIRouter, Depends, HTTPException
from loguru import logger

from api.auth import require_admin
from api.models import AdminUserCreate, UserListResponse, UserResponse, UserUpdate
from api.user_service import (
    create_user_admin,
    get_user_by_id,
    list_users,
    update_user,
)
from open_notebook.domain.user import User
from open_notebook.domain.user_deletion import UserDeletionReport, delete_user_cascade

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
        logger.error("User creation failed: {}", str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Unexpected error creating user: {}", str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/users", response_model=List[UserListResponse])
async def get_users(_admin: User = Depends(require_admin)):
    """List all users with company names."""
    try:
        return await list_users()
    except Exception as e:
        logger.error("Error listing users: {}", str(e))
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
        logger.error("Error fetching user {}: {}", user_id, str(e))
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
        logger.error("User update failed: {}", str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Unexpected error updating user: {}", str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/users/{user_id}", response_model=UserDeletionReport)
async def delete_user_endpoint(user_id: str, admin: User = Depends(require_admin)):
    """
    Delete user and cascade to all related data (GDPR-compliant).

    **Deleted Data:**
    - learner_objective_progress records
    - LangGraph conversation checkpoints (SQLite)
    - User-created quizzes
    - User-created notes
    - Module assignments where user is assigner
    - User record

    **Returns:**
    - 200: UserDeletionReport with counts of deleted records
    - 404: User not found
    - 403: Requires admin privileges
    """
    try:
        report = await delete_user_cascade(user_id)

        logger.info(
            f"User deleted by admin",
            extra={
                "user_id": user_id,
                "admin_id": admin.id,
                "report": report.model_dump(),
            },
        )

        return report

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error("Error deleting user {}: {}", user_id, str(e))
        raise HTTPException(status_code=500, detail="Internal server error")
