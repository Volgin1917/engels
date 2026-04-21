"""Роутеры для пользователей."""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from src.api.schemas import UserCreate, UserUpdate, UserResponse, PaginatedResponse
from src.api.deps import get_user_service, get_current_active_user
from src.services.user_service import UserService
from src.models.user import User

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user: UserCreate,
    service: UserService = Depends(get_user_service),
    current_user: User = Depends(get_current_active_user)
):
    """Создать нового пользователя."""
    # Проверка на существование
    existing = await service.get_by_username(user.username)
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already exists")
    
    return await service.create(user.model_dump())


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    service: UserService = Depends(get_user_service),
    current_user: User = Depends(get_current_active_user)
):
    """Получить пользователя по ID."""
    user = await service.get(user_id)
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
    updated_user = await service.update(user_id, user_update.model_dump(exclude_unset=True))
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
    success = await service.delete(user_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")


@router.get("/", response_model=PaginatedResponse)
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    is_active: bool = None,
    service: UserService = Depends(get_user_service),
    current_user: User = Depends(get_current_active_user)
):
    """Список пользователей с пагинацией."""
    users, total = await service.list(skip=skip, limit=limit, is_active=is_active)
    return PaginatedResponse(
        items=users,
        total=total,
        page=(skip // limit) + 1,
        page_size=limit,
        pages=(total + limit - 1) // limit
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """Получить информацию о текущем пользователе."""
    return current_user
