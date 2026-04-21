from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from src.services.base import BaseService
from src.models.entity import Entity

logger = structlog.get_logger()

class EntityService(BaseService[Entity]):
    def __init__(self, db: AsyncSession):
        super().__init__(db)
        self.model = Entity

    async def create_entity(self, data: Dict[str, Any], user_id: int) -> Entity:
        data["created_by"] = user_id
        data["updated_by"] = user_id
        logger.info("Creating entity", name=data.get("name"), type=data.get("type"))
        return await self.create(data)

    async def update_entity(self, entity_id: int, data: Dict[str, Any], user_id: int) -> Optional[Entity]:
        data["updated_by"] = user_id
        logger.info("Updating entity", entity_id=entity_id)
        return await self.update(entity_id, data)

    async def delete_entity(self, entity_id: int, user_id: int) -> bool:
        logger.info("Deleting entity", entity_id=entity_id)
        return await self.delete(entity_id)

    async def get_entity(self, entity_id: int) -> Optional[Entity]:
        return await self.get(entity_id)

    async def list_entities(self, skip: int = 0, limit: int = 100) -> List[Entity]:
        return await self.list(skip=skip, limit=limit)
