from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from src.services.base import BaseService
from src.models.audit_log import AuditLog

logger = structlog.get_logger()

class AuditService(BaseService[AuditLog]):
    def __init__(self, db: AsyncSession):
        super().__init__(db)
        self.model = AuditLog

    async def log_action(self, action: str, entity_type: str, entity_id: int, 
                         old_values: Optional[Dict], new_values: Optional[Dict], 
                         user_id: int) -> AuditLog:
        data = {
            "action": action,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "old_values": old_values or {},
            "new_values": new_values or {},
            "user_id": user_id
        }
        logger.info("Logging audit action", action=action, entity_type=entity_type, entity_id=entity_id)
        return await self.create(data)

    async def get_entity_audit_log(self, entity_type: str, entity_id: int, 
                                   skip: int = 0, limit: int = 100) -> List[AuditLog]:
        # Кастомный метод для получения истории по сущности
        from sqlalchemy import select
        stmt = select(self.model).where(
            self.model.entity_type == entity_type,
            self.model.entity_id == entity_id
        ).offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_audit_logs(self, skip: int = 0, limit: int = 100) -> List[AuditLog]:
        return await self.list(skip=skip, limit=limit)
