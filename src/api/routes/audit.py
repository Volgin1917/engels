"""Роутеры для аудита."""
from typing import List, Optional
from fastapi import APIRouter, Depends, Query

from src.api.schemas import AuditLogResponse
from src.api.deps import get_audit_service, get_current_active_user
from src.services.audit_service import AuditService
from src.models import User

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("/", response_model=List[AuditLogResponse])
async def get_audit_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    entity_type: Optional[str] = None,
    action: Optional[str] = None,
    service: AuditService = Depends(get_audit_service),
    current_user: User = Depends(get_current_active_user)
):
    """Получить логи аудита с фильтрацией и пагинацией."""
    return await service.get_audit_logs(skip=skip, limit=limit, entity_type=entity_type, action=action)


@router.get("/{entity_type}/{entity_id}", response_model=List[AuditLogResponse])
async def get_entity_audit_log(
    entity_type: str,
    entity_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    service: AuditService = Depends(get_audit_service),
    current_user: User = Depends(get_current_active_user)
):
    """Получить логи аудита для конкретной сущности."""
    return await service.get_entity_audit_log(entity_type, entity_id, skip=skip, limit=limit)
