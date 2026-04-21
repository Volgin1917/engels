"""Роутеры для аудита."""
from fastapi import APIRouter, Depends, Query
from src.api.schemas import AuditLogResponse, PaginatedResponse
from src.api.deps import get_audit_service, get_current_active_user
from src.services.audit_service import AuditService
from src.models.user import User

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("/", response_model=PaginatedResponse)
async def get_audit_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    entity_type: str = None,
    entity_id: int = None,
    action: str = None,
    user_id: int = None,
    service: AuditService = Depends(get_audit_service),
    current_user: User = Depends(get_current_active_user)
):
    """Получить логи аудита с фильтрацией и пагинацией."""
    logs, total = await service.list(
        skip=skip, 
        limit=limit, 
        entity_type=entity_type, 
        entity_id=entity_id,
        action=action,
        user_id=user_id
    )
    return PaginatedResponse(
        items=logs,
        total=total,
        page=(skip // limit) + 1,
        page_size=limit,
        pages=(total + limit - 1) // limit
    )


@router.get("/{entity_type}/{entity_id}", response_model=PaginatedResponse)
async def get_entity_audit_log(
    entity_type: str,
    entity_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    service: AuditService = Depends(get_audit_service),
    current_user: User = Depends(get_current_active_user)
):
    """Получить логи аудита для конкретной сущности."""
    logs, total = await service.get_entity_audit_log(entity_type, entity_id, skip=skip, limit=limit)
    return PaginatedResponse(
        items=logs,
        total=total,
        page=(skip // limit) + 1,
        page_size=limit,
        pages=(total + limit - 1) // limit
    )
