"""Роутеры для связей."""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query

from src.api.schemas import RelationshipCreate, RelationshipUpdate, RelationshipResponse
from src.api.deps import get_relationship_service, get_current_active_user
from src.services.relationship_service import RelationshipService
from src.models import User

router = APIRouter(prefix="/relationships", tags=["relationships"])


@router.post("/", response_model=RelationshipResponse, status_code=status.HTTP_201_CREATED)
async def create_relationship(
    relationship: RelationshipCreate,
    service: RelationshipService = Depends(get_relationship_service),
    current_user: User = Depends(get_current_active_user)
):
    """Создать новую связь."""
    return await service.create_relationship(relationship.model_dump(), current_user.id)


@router.get("/{relationship_id}", response_model=RelationshipResponse)
async def get_relationship(
    relationship_id: int,
    service: RelationshipService = Depends(get_relationship_service),
    current_user: User = Depends(get_current_active_user)
):
    """Получить связь по ID."""
    relationship = await service.get_relationship(relationship_id)
    if not relationship:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Relationship not found")
    return relationship


@router.put("/{relationship_id}", response_model=RelationshipResponse)
async def update_relationship(
    relationship_id: int,
    relationship_update: RelationshipUpdate,
    service: RelationshipService = Depends(get_relationship_service),
    current_user: User = Depends(get_current_active_user)
):
    """Обновить связь."""
    updated_relationship = await service.update_relationship(relationship_id, relationship_update.model_dump(exclude_unset=True), current_user.id)
    if not updated_relationship:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Relationship not found")
    return updated_relationship


@router.delete("/{relationship_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_relationship(
    relationship_id: int,
    service: RelationshipService = Depends(get_relationship_service),
    current_user: User = Depends(get_current_active_user)
):
    """Удалить связь."""
    success = await service.delete_relationship(relationship_id, current_user.id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Relationship not found")


@router.get("/", response_model=List[RelationshipResponse])
async def list_relationships(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    source_entity_id: Optional[int] = None,
    target_entity_id: Optional[int] = None,
    service: RelationshipService = Depends(get_relationship_service),
    current_user: User = Depends(get_current_active_user)
):
    """Список связей с пагинацией."""
    return await service.list_relationships(
        skip=skip, 
        limit=limit, 
        source_entity_id=source_entity_id, 
        target_entity_id=target_entity_id
    )
