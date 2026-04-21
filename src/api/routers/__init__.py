"""Роутеры для API эндпоинтов."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import List, Optional
from sqlalchemy.orm import Session

from src.api.dependencies import get_db, get_current_user, get_services, ServiceDependencies
from src.api.schemas import (
    EntityCreate, EntityUpdate, EntityResponse,
    RelationCreate, RelationUpdate, RelationResponse,
    SourceCreate, SourceResponse,
    AuditLogResponse, PaginatedResponse,
    EntityType, RelationType
)

# --- Роутер для Entity ---
router_entities = APIRouter(prefix="/entities", tags=["Entities"])


@router_entities.get("/", response_model=List[EntityResponse])
async def list_entities(
    entity_type: Optional[EntityType] = None,
    needs_review: Optional[bool] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    services: ServiceDependencies = Depends(get_services)
):
    """Получить список сущностей с фильтрацией и пагинацией."""
    # entities = await services.entity_service.list(
    #     entity_type=entity_type,
    #     needs_review=needs_review,
    #     page=page,
    #     page_size=page_size
    # )
    # return entities
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router_entities.get("/{entity_id}", response_model=EntityResponse)
async def get_entity(
    entity_id: int,
    services: ServiceDependencies = Depends(get_services)
):
    """Получить сущность по ID."""
    # entity = await services.entity_service.get_by_id(entity_id)
    # if not entity:
    #     raise HTTPException(status_code=404, detail="Entity not found")
    # return entity
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router_entities.post("/", response_model=EntityResponse, status_code=status.HTTP_201_CREATED)
async def create_entity(
    entity_data: EntityCreate,
    current_user: dict = Depends(get_current_user),
    services: ServiceDependencies = Depends(get_services)
):
    """Создать новую сущность."""
    # entity = await services.entity_service.create(entity_data, created_by=current_user["id"])
    # return entity
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router_entities.put("/{entity_id}", response_model=EntityResponse)
async def update_entity(
    entity_id: int,
    entity_data: EntityUpdate,
    current_user: dict = Depends(get_current_user),
    services: ServiceDependencies = Depends(get_services)
):
    """Обновить сущность."""
    # entity = await services.entity_service.update(entity_id, entity_data, updated_by=current_user["id"])
    # return entity
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router_entities.delete("/{entity_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_entity(
    entity_id: int,
    current_user: dict = Depends(get_current_user),
    services: ServiceDependencies = Depends(get_services)
):
    """Удалить сущность."""
    # await services.entity_service.delete(entity_id, deleted_by=current_user["id"])
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router_entities.post("/{entity_id}/review", response_model=EntityResponse)
async def review_entity(
    entity_id: int,
    approved: bool,
    comment: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    services: ServiceDependencies = Depends(get_services)
):
    """Проверить сущность экспертом (Human-in-the-loop)."""
    # entity = await services.entity_service.review(
    #     entity_id, 
    #     approved=approved, 
    #     comment=comment, 
    #     reviewed_by=current_user["id"]
    # )
    # return entity
    raise HTTPException(status_code=501, detail="Not implemented yet")


# --- Роутер для Relations ---
router_relations = APIRouter(prefix="/relations", tags=["Relations"])


@router_relations.get("/", response_model=List[RelationResponse])
async def list_relations(
    source_entity_id: Optional[int] = None,
    target_entity_id: Optional[int] = None,
    relation_type: Optional[RelationType] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    services: ServiceDependencies = Depends(get_services)
):
    """Получить список связей."""
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router_relations.post("/", response_model=RelationResponse, status_code=status.HTTP_201_CREATED)
async def create_relation(
    relation_data: RelationCreate,
    current_user: dict = Depends(get_current_user),
    services: ServiceDependencies = Depends(get_services)
):
    """Создать новую связь."""
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router_relations.delete("/{relation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_relation(
    relation_id: int,
    current_user: dict = Depends(get_current_user),
    services: ServiceDependencies = Depends(get_services)
):
    """Удалить связь."""
    raise HTTPException(status_code=501, detail="Not implemented yet")


# --- Роутер для Sources ---
router_sources = APIRouter(prefix="/sources", tags=["Sources"])


@router_sources.get("/", response_model=List[SourceResponse])
async def list_sources(
    source_type: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    services: ServiceDependencies = Depends(get_services)
):
    """Получить список источников."""
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router_sources.post("/", response_model=SourceResponse, status_code=status.HTTP_201_CREATED)
async def create_source(
    source_data: SourceCreate,
    current_user: dict = Depends(get_current_user),
    services: ServiceDependencies = Depends(get_services)
):
    """Создать новый источник."""
    raise HTTPException(status_code=501, detail="Not implemented yet")


# --- Роутер для Audit Logs ---
router_audit = APIRouter(prefix="/audit", tags=["Audit"])


@router_audit.get("/", response_model=List[AuditLogResponse])
async def list_audit_logs(
    entity_id: Optional[int] = None,
    user_id: Optional[int] = None,
    action: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    services: ServiceDependencies = Depends(get_services)
):
    """Получить лог аудита."""
    raise HTTPException(status_code=501, detail="Not implemented yet")
