"""Роутеры для пользователей."""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query

from src.api.schemas import UserCreate, UserUpdate, UserResponse
from src.api.deps import get_user_service, get_current_active_user
from src.services.user_service import UserService
from src.models import User

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user: UserCreate,
    service: UserService = Depends(get_user_service),
    current_user: User = Depends(get_current_active_user)
):
    """Создать нового пользователя."""
    # Проверка на существование
    existing = await service.get_user_by_username(user.username)
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already exists")
    
    return await service.create_user(user.model_dump())


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    service: UserService = Depends(get_user_service),
    current_user: User = Depends(get_current_active_user)
):
    """Получить пользователя по ID."""
    user = await service.get_user(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_update: UserUpdate,
    service: UserService = Depends(get_user_service),
    current_user: User = Depends(get_current_active_user)
):
    """Обновить пользователя."""
    updated_user = await service.update_user(user_id, user_update.model_dump(exclude_unset=True))
    if not updated_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return updated_user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    service: UserService = Depends(get_user_service),
    current_user: User = Depends(get_current_active_user)
):
    """Удалить пользователя."""
    success = await service.delete_user(user_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")


@router.get("/", response_model=List[UserResponse])
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    is_active: Optional[bool] = None,
    service: UserService = Depends(get_user_service),
    current_user: User = Depends(get_current_active_user)
):
    """Список пользователей с пагинацией."""
    return await service.list_users(skip=skip, limit=limit, is_active=is_active)


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """Получить информацию о текущем пользователе."""
    return current_user
