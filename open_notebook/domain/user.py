from typing import Any, ClassVar, Dict, Optional

from loguru import logger

from open_notebook.database.repository import ensure_record_id, repo_query
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

    def _prepare_save_data(self) -> Dict[str, Any]:
        data = super()._prepare_save_data()
        # SurrealDB schema defines company_id as option<record<company>>.
        # connection.insert() requires a RecordID object, not a string.
        if data.get("company_id") and isinstance(data["company_id"], str):
            data["company_id"] = ensure_record_id(data["company_id"])
        return data

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
