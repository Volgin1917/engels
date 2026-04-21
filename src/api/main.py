"""Главный файл приложения FastAPI."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes import (
    entities_router,
    relations_router,
    sources_router,
    audit_router,
    users_router,
    auth_router
)
from src.config import settings


def create_app() -> FastAPI:
    """Создать и настроить приложение FastAPI."""
    app = FastAPI(
        title="Knowledge Graph API",
        description="API для управления графом знаний",
        version="0.1.0"
    )

    # Добавляем CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS.split(","),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Подключаем роутеры
    app.include_router(auth_router)
    app.include_router(entities_router)
    app.include_router(relations_router)
    app.include_router(sources_router)
    app.include_router(audit_router)
    app.include_router(users_router)

    @app.get("/")
    async def root():
        return {"message": "Knowledge Graph API", "version": "0.1.0"}

    @app.get("/health")
    async def health_check():
        return {"status": "healthy"}

    return app


app = create_app()
