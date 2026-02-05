from typing import List

from fastapi import APIRouter, Depends, HTTPException
from loguru import logger

from api.auth import require_admin
from api.models import AdminUserCreate, UserListResponse, UserUpdate
from api import user_service
from open_notebook.domain.user import User

router = APIRouter(dependencies=[Depends(require_admin)])


@router.get("/users", response_model=List[UserListResponse])
async def list_users():
    """Get all users with company names."""
    try:
        users = await user_service.list_users()
        result = []
        for user in users:
            user_data = await user_service.get_user_with_company_name(user)
            result.append(UserListResponse(**user_data))
        return result
    except Exception as e:
        logger.error(f"Error listing users: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error listing users: {str(e)}")


@router.post("/users", response_model=UserListResponse)
async def create_user(user_data: AdminUserCreate, admin: User = Depends(require_admin)):
    """Create a new user (admin only)."""
    try:
        user = await user_service.create_user_admin(
            username=user_data.username,
            email=user_data.email,
            password=user_data.password,
            role=user_data.role,
            company_id=user_data.company_id,
        )
        result = await user_service.get_user_with_company_name(user)
        return UserListResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating user: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating user: {str(e)}")


@router.get("/users/{user_id}", response_model=UserListResponse)
async def get_user(user_id: str):
    """Get a specific user by ID."""
    try:
        user = await user_service.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        result = await user_service.get_user_with_company_name(user)
        return UserListResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching user: {str(e)}")


@router.put("/users/{user_id}", response_model=UserListResponse)
async def update_user(user_id: str, user_update: UserUpdate, admin: User = Depends(require_admin)):
    """Update a user (admin only)."""
    try:
        user = await user_service.update_user(
            user_id=user_id,
            username=user_update.username,
            email=user_update.email,
            password=user_update.password,
            role=user_update.role,
            company_id=user_update.company_id,
            onboarding_completed=user_update.onboarding_completed,
        )
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        result = await user_service.get_user_with_company_name(user)
        return UserListResponse(**result)
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error updating user: {str(e)}")


@router.delete("/users/{user_id}")
async def delete_user(user_id: str, admin: User = Depends(require_admin)):
    """Delete a user (admin only)."""
    try:
        deleted = await user_service.delete_user(user_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="User not found")
        return {"message": "User deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error deleting user: {str(e)}")
