from typing import TypeVar, Generic, Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from pydantic import BaseModel

T = TypeVar('T')

class BaseService(Generic[T]):
    def __init__(self, db: AsyncSession):
        self.db = db
        self.model = None  # Должен быть установлен в наследниках

    async def get(self, id: int) -> Optional[T]:
        if not self.model:
            raise NotImplementedError("Model not defined")
        result = await self.db.execute(select(self.model).where(self.model.id == id))
        return result.scalar_one_or_none()

    async def list(self, skip: int = 0, limit: int = 100) -> List[T]:
        if not self.model:
            raise NotImplementedError("Model not defined")
        result = await self.db.execute(select(self.model).offset(skip).limit(limit))
        return list(result.scalars().all())

    async def create(self, data: Dict[str, Any]) -> T:
        if not self.model:
            raise NotImplementedError("Model not defined")
        instance = self.model(**data)
        self.db.add(instance)
        await self.db.commit()
        await self.db.refresh(instance)
        return instance

    async def update(self, id: int, data: Dict[str, Any]) -> Optional[T]:
        if not self.model:
            raise NotImplementedError("Model not defined")
        stmt = update(self.model).where(self.model.id == id).values(**data).returning(self.model)
        result = await self.db.execute(stmt)
        await self.db.commit()
        return result.scalar_one_or_none()

    async def delete(self, id: int) -> bool:
        if not self.model:
            raise NotImplementedError("Model not defined")
        stmt = delete(self.model).where(self.model.id == id)
        result = await self.db.execute(stmt)
        await self.db.commit()
        return result.rowcount > 0
