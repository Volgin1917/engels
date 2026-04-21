"""Роутеры для связей."""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from src.api.schemas import RelationCreate, RelationUpdate, RelationResponse, PaginatedResponse
from src.api.deps import get_relation_service, get_current_active_user
from src.services.relation_service import RelationService
from src.models.user import User

router = APIRouter(prefix="/relations", tags=["relations"])


@router.post("/", response_model=RelationResponse, status_code=status.HTTP_201_CREATED)
async def create_relation(
    relation: RelationCreate,
    service: RelationService = Depends(get_relation_service),
    current_user: User = Depends(get_current_active_user)
):
    """Создать новую связь."""
    return await service.create(relation.model_dump(), current_user.id)


@router.get("/{relation_id}", response_model=RelationResponse)
async def get_relation(
    relation_id: int,
    service: RelationService = Depends(get_relation_service),
    current_user: User = Depends(get_current_active_user)
):
    """Получить связь по ID."""
    relation = await service.get(relation_id)
    if not relation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Relation not found")
    return relation


@router.put("/{relation_id}", response_model=RelationResponse)
async def update_relation(
    relation_id: int,
    relation_update: RelationUpdate,
    service: RelationService = Depends(get_relation_service),
    current_user: User = Depends(get_current_active_user)
):
    """Обновить связь."""
    updated_relation = await service.update(relation_id, relation_update.model_dump(exclude_unset=True), current_user.id)
    if not updated_relation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Relation not found")
    return updated_relation


@router.delete("/{relation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_relation(
    relation_id: int,
    service: RelationService = Depends(get_relation_service),
    current_user: User = Depends(get_current_active_user)
):
    """Удалить связь."""
    success = await service.delete(relation_id, current_user.id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Relation not found")


@router.get("/", response_model=PaginatedResponse)
async def list_relations(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    source_entity_id: int = None,
    target_entity_id: int = None,
    service: RelationService = Depends(get_relation_service),
    current_user: User = Depends(get_current_active_user)
):
    """Список связей с пагинацией."""
    relations, total = await service.list(
        skip=skip, 
        limit=limit, 
        source_entity_id=source_entity_id, 
        target_entity_id=target_entity_id
    )
    return PaginatedResponse(
        items=relations,
        total=total,
        page=(skip // limit) + 1,
        page_size=limit,
        pages=(total + limit - 1) // limit
    )
