"""Роутеры для источников."""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from src.api.schemas import SourceCreate, SourceResponse, PaginatedResponse
from src.api.deps import get_source_service, get_current_active_user
from src.services.source_service import SourceService
from src.models.user import User

router = APIRouter(prefix="/sources", tags=["sources"])


@router.post("/", response_model=SourceResponse, status_code=status.HTTP_201_CREATED)
async def create_source(
    source: SourceCreate,
    service: SourceService = Depends(get_source_service),
    current_user: User = Depends(get_current_active_user)
):
    """Создать новый источник."""
    return await service.create(source.model_dump(), current_user.id)


@router.get("/{source_id}", response_model=SourceResponse)
async def get_source(
    source_id: int,
    service: SourceService = Depends(get_source_service),
    current_user: User = Depends(get_current_active_user)
):
    """Получить источник по ID."""
    source = await service.get(source_id)
    if not source:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source not found")
    return source


@router.delete("/{source_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_source(
    source_id: int,
    service: SourceService = Depends(get_source_service),
    current_user: User = Depends(get_current_active_user)
):
    """Удалить источник."""
    success = await service.delete(source_id, current_user.id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source not found")


@router.get("/", response_model=PaginatedResponse)
async def list_sources(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    source_type: str = None,
    is_active: bool = None,
    service: SourceService = Depends(get_source_service),
    current_user: User = Depends(get_current_active_user)
):
    """Список источников с пагинацией."""
    sources, total = await service.list(skip=skip, limit=limit, source_type=source_type, is_active=is_active)
    return PaginatedResponse(
        items=sources,
        total=total,
        page=(skip // limit) + 1,
        page_size=limit,
        pages=(total + limit - 1) // limit
    )


@router.post("/{source_id}/sync", status_code=status.HTTP_200_OK)
async def sync_source(
    source_id: int,
    service: SourceService = Depends(get_source_service),
    current_user: User = Depends(get_current_active_user)
):
    """Запустить синхронизацию источника."""
    source = await service.get(source_id)
    if not source:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source not found")
    
    await service.sync(source_id, current_user.id)
    return {"message": f"Sync initiated for source {source_id}"}
