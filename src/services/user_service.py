from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from src.services.base import BaseService
from src.models.user import User
from src.core.security import get_password_hash

logger = structlog.get_logger()

class UserService(BaseService[User]):
    def __init__(self, db: AsyncSession):
        super().__init__(db)
        self.model = User

    async def create_user(self, data: Dict[str, Any]) -> User:
        # Хешируем пароль перед сохранением
        if "password" in data:
            data["password"] = get_password_hash(data["password"])
        logger.info("Creating user", username=data.get("username"), email=data.get("email"))
        return await self.create(data)

    async def update_user(self, user_id: int, data: Dict[str, Any]) -> Optional[User]:
        # Если обновляется пароль, хешируем его
        if "password" in data:
            data["password"] = get_password_hash(data["password"])
        logger.info("Updating user", user_id=user_id)
        return await self.update(user_id, data)

    async def delete_user(self, user_id: int) -> bool:
        logger.info("Deleting user", user_id=user_id)
        return await self.delete(user_id)

    async def get_user(self, user_id: int) -> Optional[User]:
        return await self.get(user_id)

    async def get_user_by_username(self, username: str) -> Optional[User]:
        from sqlalchemy import select
        stmt = select(self.model).where(self.model.username == username)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        return await self.list(skip=skip, limit=limit)
