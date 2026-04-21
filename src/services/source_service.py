from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from src.services.base import BaseService
from src.models import Source

logger = structlog.get_logger()

class SourceService(BaseService[Source]):
    def __init__(self, db: AsyncSession):
        super().__init__(db)
        self.model = Source

    async def create_source(self, data: Dict[str, Any], user_id: int) -> Source:
        data["created_by"] = user_id
        data["updated_by"] = user_id
        logger.info("Creating source", name=data.get("name"), type=data.get("type"))
        return await self.create(data)

    async def update_source(self, source_id: int, data: Dict[str, Any], user_id: int) -> Optional[Source]:
        data["updated_by"] = user_id
        logger.info("Updating source", source_id=source_id)
        return await self.update(source_id, data)

    async def delete_source(self, source_id: int, user_id: int) -> bool:
        logger.info("Deleting source", source_id=source_id)
        return await self.delete(source_id)

    async def get_source(self, source_id: int) -> Optional[Source]:
        return await self.get(source_id)

    async def list_sources(self, skip: int = 0, limit: int = 100, is_active: Optional[bool] = None) -> List[Source]:
        """List sources with pagination and optional filtering"""
        from sqlalchemy import select
        
        query = select(Source).offset(skip).limit(limit)
        
        if is_active is not None:
            query = query.where(Source.is_active == is_active)
            
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def sync_source(self, source_id: int, user_id: int) -> None:
        """Запускает синхронизацию источника данных"""
        logger.info("Syncing source", source_id=source_id)
        # Здесь будет логика синхронизации
        pass
