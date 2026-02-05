from typing import List, Optional

from loguru import logger

from api.auth import hash_password, verify_password
from open_notebook.domain.user import User
from open_notebook.database.repository import repo_query


async def register_user(username: str, email: str, password: str) -> User:
    """Register a new user with hashed password."""
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters")

    if len(username) < 3:
        raise ValueError("Username must be at least 3 characters")

    existing = await User.get_by_username(username)
    if existing:
        raise ValueError("Username already taken")

    existing_email = await User.get_by_email(email)
    if existing_email:
        raise ValueError("Email already registered")

    user = User(
        username=username,
        email=email,
        password_hash=hash_password(password),
        role="learner",
    )
    await user.save()
    logger.info(f"User registered: {username}")
    return user


async def authenticate_user(username: str, password: str) -> Optional[User]:
    """Authenticate user by username and password."""
    user = await User.get_by_username(username)
    if not user:
        logger.error(f"Authentication failed: user not found: {username}")
        return None

    if not verify_password(password, user.password_hash):
        logger.error(f"Authentication failed: invalid password for: {username}")
        return None

    return user


async def get_user_by_id(user_id: str) -> Optional[User]:
    """Fetch user by ID."""
    try:
        return await User.get(user_id)
    except Exception:
        return None


async def create_user_admin(
    username: str,
    email: str,
    password: str,
    role: str = "learner",
    company_id: Optional[str] = None,
) -> User:
    """Admin creates a new user with specified role and company."""
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters")

    if len(username) < 3:
        raise ValueError("Username must be at least 3 characters")

    if role not in ["admin", "learner"]:
        raise ValueError("Role must be 'admin' or 'learner'")

    existing = await User.get_by_username(username)
    if existing:
        raise ValueError("Username already taken")

    existing_email = await User.get_by_email(email)
    if existing_email:
        raise ValueError("Email already registered")

    if company_id:
        from open_notebook.domain.company import Company

        company = await Company.get(company_id)
        if not company:
            raise ValueError("Company not found")

    user = User(
        username=username,
        email=email,
        password_hash=hash_password(password),
        role=role,
        company_id=company_id,
    )
    await user.save()
    logger.info(f"Admin created user: {username} (role: {role})")
    return user


async def list_users() -> List["UserListResponse"]:
    """List all users with company names.

    Uses single JOIN query to avoid N+1 problem.
    Returns UserListResponse Pydantic models, not raw dicts.
    """
    from api.models import UserListResponse
    from open_notebook.database.repository import repo_query

    try:
        # Single JOIN query to get all users with company names (avoid N+1)
        result = await repo_query(
            """
            SELECT
                id,
                username,
                email,
                role,
                company_id,
                onboarding_completed,
                created,
                updated,
                (SELECT name FROM company WHERE id = $parent.company_id LIMIT 1)[0] AS company_name
            FROM user
            ORDER BY username
            """,
            {}
        )

        # Convert to Pydantic models (type-safe)
        users = []
        for row in result:
            users.append(UserListResponse(
                id=row.get("id"),
                username=row.get("username"),
                email=row.get("email"),
                role=row.get("role"),
                company_id=row.get("company_id"),
                company_name=row.get("company_name"),
                onboarding_completed=row.get("onboarding_completed", False),
                created=str(row.get("created", "")),
                updated=str(row.get("updated", ""))
            ))

        return users
    except Exception as e:
        logger.error(f"Error listing users: {e}")
        raise


async def update_user(
    user_id: str,
    username: Optional[str] = None,
    email: Optional[str] = None,
    password: Optional[str] = None,
    role: Optional[str] = None,
    company_id: Optional[str] = None,
    onboarding_completed: Optional[bool] = None,
) -> Optional[User]:
    """Update user fields."""
    user = await get_user_by_id(user_id)
    if not user:
        return None

    if username and username != user.username:
        existing = await User.get_by_username(username)
        if existing:
            raise ValueError("Username already taken")
        user.username = username

    if email and email != user.email:
        existing = await User.get_by_email(email)
        if existing:
            raise ValueError("Email already registered")
        user.email = email

    if password:
        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters")
        user.password_hash = hash_password(password)

    if role:
        if role not in ["admin", "learner"]:
            raise ValueError("Role must be 'admin' or 'learner'")
        user.role = role

    if company_id is not None:
        if company_id:
            from open_notebook.domain.company import Company

            company = await Company.get(company_id)
            if not company:
                raise ValueError("Company not found")
        user.company_id = company_id

    if onboarding_completed is not None:
        user.onboarding_completed = onboarding_completed

    await user.save()
    logger.info(f"User updated: {user.username}")
    return user


async def delete_user(user_id: str) -> bool:
    """Delete a user. Returns True if deleted."""
    user = await get_user_by_id(user_id)
    if not user:
        return False

    await user.delete()
    logger.info(f"User deleted: {user.username}")
    return True


# REMOVED: get_user_with_company_name() - caused N+1 query problem
# Now list_users() uses JOIN query and returns UserListResponse models directly
