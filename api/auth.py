import os
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
from fastapi import Depends, HTTPException, Request
from jose import JWTError, jwt
from loguru import logger

from open_notebook.domain.user import User

# JWT Configuration
JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "")
JWT_ALGORITHM = "HS256"
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.environ.get("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30")
)
JWT_REFRESH_TOKEN_EXPIRE_DAYS = int(
    os.environ.get("JWT_REFRESH_TOKEN_EXPIRE_DAYS", "7")
)


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    password_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password_bytes, salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a bcrypt hash."""
    password_bytes = plain_password.encode("utf-8")
    hashed_bytes = hashed_password.encode("utf-8")
    return bcrypt.checkpw(password_bytes, hashed_bytes)


def create_access_token(user_id: str, role: str, company_id: Optional[str] = None) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": user_id,
        "role": role,
        "company_id": company_id,
        "exp": expire,
        "type": "access",
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def create_refresh_token(user_id: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(days=JWT_REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {
        "sub": user_id,
        "exp": expire,
        "type": "refresh",
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def verify_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except JWTError as e:
        logger.error(f"Token verification failed: {e}")
        raise HTTPException(status_code=401, detail="Invalid token")


async def get_current_user(request: Request) -> User:
    token = request.cookies.get("access_token")
    if not token:
        logger.error("No access_token cookie found in request")
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        if payload.get("type") != "access":
            logger.error("Token type is not 'access'")
            raise HTTPException(status_code=401, detail="Invalid token type")
        user_id = payload.get("sub")
        if not user_id:
            logger.error("Token has no 'sub' claim")
            raise HTTPException(status_code=401, detail="Invalid token")
        try:
            user = await User.get(user_id)
            return user
        except Exception as e:
            logger.error(f"User not found for id {user_id}: {e}")
            raise HTTPException(status_code=401, detail="User not found")
    except JWTError as e:
        logger.error(f"JWT decode failed: {e}")
        raise HTTPException(status_code=401, detail="Invalid token")


# Backward compatibility: keep PasswordAuthMiddleware available for fallback
# If JWT_SECRET_KEY is not set but OPEN_NOTEBOOK_PASSWORD is set, use old auth
def is_jwt_enabled() -> bool:
    return bool(JWT_SECRET_KEY)


async def require_admin(user: User = Depends(get_current_user)) -> User:
    """Dependency that requires an authenticated admin user."""
    if user.role != "admin":
        logger.error(f"Admin access denied for user {user.id} with role {user.role}")
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


async def require_learner(user: User = Depends(get_current_user)) -> User:
    """Dependency that requires an authenticated learner user."""
    if user.role != "learner":
        logger.error(f"Learner access denied for user {user.id} with role {user.role}")
        raise HTTPException(status_code=403, detail="Learner access required")
    return user


@dataclass
class LearnerContext:
    """Context for learner requests with user and company information."""
    user: User
    company_id: str


async def get_current_learner(user: User = Depends(require_learner)) -> LearnerContext:
    """Dependency that requires a learner with a company assignment.

    This is the single enforcement point for per-company data isolation.
    All learner-scoped endpoints should use this dependency.
    """
    if not user.company_id:
        logger.error(f"Learner {user.id} has no company assignment")
        raise HTTPException(
            status_code=403, detail="Learner must be assigned to a company"
        )
    return LearnerContext(user=user, company_id=user.company_id)
