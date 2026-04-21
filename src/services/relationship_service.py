from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from src.services.base import BaseService
from src.models.relationship import Relationship

logger = structlog.get_logger()

class RelationshipService(BaseService[Relationship]):
    def __init__(self, db: AsyncSession):
        super().__init__(db)
        self.model = Relationship

    async def create_relationship(self, data: Dict[str, Any], user_id: int) -> Relationship:
        data["created_by"] = user_id
        data["updated_by"] = user_id
        logger.info("Creating relationship", source=data.get("source_entity_id"), target=data.get("target_entity_id"))
        return await self.create(data)

    async def update_relationship(self, relationship_id: int, data: Dict[str, Any], user_id: int) -> Optional[Relationship]:
        data["updated_by"] = user_id
        logger.info("Updating relationship", relationship_id=relationship_id)
        return await self.update(relationship_id, data)

    async def delete_relationship(self, relationship_id: int, user_id: int) -> bool:
        logger.info("Deleting relationship", relationship_id=relationship_id)
        return await self.delete(relationship_id)

    async def get_relationship(self, relationship_id: int) -> Optional[Relationship]:
        return await self.get(relationship_id)

    async def list_relationships(self, skip: int = 0, limit: int = 100) -> List[Relationship]:
        return await self.list(skip=skip, limit=limit)
