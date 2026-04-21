"""Зависимости для внедрения в API."""

from typing import Generator, Optional
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

# Импорты сервисов и сессии БД (будут реализованы)
# from src.db.session import get_db_session
# from src.services import EntityService, RelationService, SourceService, AuditService


def get_db() -> Generator:
    """
    Зависимость для получения сессии базы данных.
    В реальном приложении импортируется из db.session.
    """
    # session = next(get_db_session())
    # try:
    #     yield session
    # finally:
    #     session.close()
    raise NotImplementedError("DB session not configured yet")


def get_current_user(
    # token: str = Depends(oauth2_scheme)
) -> Optional[dict]:
    """
    Зависимость для получения текущего пользователя.
    Здесь будет логика проверки JWT токена.
    """
    # user = await get_user_from_token(token)
    # if not user:
    #     raise HTTPException(status_code=401, detail="Invalid token")
    # return user
    return {"id": 1, "username": "admin", "role": "admin"}  # Mock для разработки


class ServiceDependencies:
    """Контейнер зависимостей сервисов."""
    
    def __init__(self, db: Session = Depends(get_db)):
        self.db = db
        # self.entity_service = EntityService(db)
        # self.relation_service = RelationService(db)
        # self.source_service = SourceService(db)
        # self.audit_service = AuditService(db)


def get_services() -> ServiceDependencies:
    """Получение всех сервисов одной зависимостью."""
    return ServiceDependencies()
