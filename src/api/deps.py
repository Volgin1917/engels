"""Зависимости для API."""
from typing import AsyncGenerator
from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.db.session import get_async_session
from src.services.entity_service import EntityService
from src.services.relation_service import RelationService
from src.services.source_service import SourceService
from src.services.audit_service import AuditService
from src.services.user_service import UserService
from src.core.security import get_current_user
from src.models.user import User


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Получить сессию базы данных."""
    async for session in get_async_session():
        yield session


def get_entity_service(db: AsyncSession = Depends(get_db)) -> EntityService:
    """Получить сервис сущностей."""
    return EntityService(db)


def get_relation_service(db: AsyncSession = Depends(get_db)) -> RelationService:
    """Получить сервис связей."""
    return RelationService(db)


def get_source_service(db: AsyncSession = Depends(get_db)) -> SourceService:
    """Получить сервис источников."""
    return SourceService(db)


def get_audit_service(db: AsyncSession = Depends(get_db)) -> AuditService:
    """Получить сервис аудита."""
    return AuditService(db)


def get_user_service(db: AsyncSession = Depends(get_db)) -> UserService:
    """Получить сервис пользователей."""
    return UserService(db)


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Получить текущего активного пользователя."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user
