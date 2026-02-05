from typing import ClassVar, Optional

from loguru import logger

from open_notebook.database.repository import repo_query
from open_notebook.domain.base import ObjectModel
from open_notebook.exceptions import DatabaseOperationError


class User(ObjectModel):
    table_name: ClassVar[str] = "user"

    username: str
    email: str
    password_hash: str
    role: str = "learner"
    company_id: Optional[str] = None
    profile: Optional[dict] = None
    onboarding_completed: bool = False

    @classmethod
    async def get_by_username(cls, username: str) -> Optional["User"]:
        try:
            result = await repo_query(
                "SELECT * FROM user WHERE username = $username LIMIT 1",
                {"username": username},
            )
            if result:
                return cls(**result[0])
            return None
        except Exception as e:
            logger.error(f"Error fetching user by username {username}: {str(e)}")
            raise DatabaseOperationError(e)

    @classmethod
    async def get_by_email(cls, email: str) -> Optional["User"]:
        try:
            result = await repo_query(
                "SELECT * FROM user WHERE email = $email LIMIT 1",
                {"email": email},
            )
            if result:
                return cls(**result[0])
            return None
        except Exception as e:
            logger.error(f"Error fetching user by email {email}: {str(e)}")
            raise DatabaseOperationError(e)
