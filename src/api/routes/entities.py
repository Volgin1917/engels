"""Роутеры для сущностей."""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.schemas import EntityCreate, EntityUpdate, EntityResponse
from src.api.deps import get_entity_service, get_current_active_user
from src.services.entity_service import EntityService
from src.models import User

router = APIRouter(prefix="/entities", tags=["entities"])


@router.post("/", response_model=EntityResponse, status_code=status.HTTP_201_CREATED)
async def create_entity(
    entity: EntityCreate,
    service: EntityService = Depends(get_entity_service),
    current_user: User = Depends(get_current_active_user)
):
    """Создать новую сущность."""
    return await service.create_entity(entity.model_dump(), current_user.id)


@router.get("/{entity_id}", response_model=EntityResponse)
async def get_entity(
    entity_id: int,
    service: EntityService = Depends(get_entity_service),
    current_user: User = Depends(get_current_active_user)
):
    """Получить сущность по ID."""
    entity = await service.get_entity(entity_id)
    if not entity:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entity not found")
    return entity


@router.put("/{entity_id}", response_model=EntityResponse)
async def update_entity(
    entity_id: int,
    entity_update: EntityUpdate,
    service: EntityService = Depends(get_entity_service),
    current_user: User = Depends(get_current_active_user)
):
    """Обновить сущность."""
    updated_entity = await service.update_entity(entity_id, entity_update.model_dump(exclude_unset=True), current_user.id)
    if not updated_entity:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entity not found")
    return updated_entity


@router.delete("/{entity_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_entity(
    entity_id: int,
    service: EntityService = Depends(get_entity_service),
    current_user: User = Depends(get_current_active_user)
):
    """Удалить сущность."""
    success = await service.delete_entity(entity_id, current_user.id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entity not found")


@router.get("/", response_model=List[EntityResponse])
async def list_entities(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    entity_type: Optional[str] = None,
    service: EntityService = Depends(get_entity_service),
    current_user: User = Depends(get_current_active_user)
):
    """Список сущностей с пагинацией."""
    return await service.list_entities(skip=skip, limit=limit, entity_type=entity_type)
