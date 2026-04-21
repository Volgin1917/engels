"""Главный модуль приложения."""

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import structlog

from src.api import (
    router_entities,
    router_relations,
    router_sources,
    router_audit
)
from src.core.config import settings
from src.core.logging import setup_logging

logger = structlog.get_logger(__name__)


def create_app() -> FastAPI:
    """Фабрика приложения FastAPI."""
    
    # Настройка логирования
    setup_logging()
    
    # Создание приложения
    app = FastAPI(
        title=settings.PROJECT_NAME,
        description="Система извлечения знаний с графом сущностей",
        version="0.1.0",
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
    )
    
    # Настройка CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Регистрация роутеров
    app.include_router(router_entities, prefix="/api/v1")
    app.include_router(router_relations, prefix="/api/v1")
    app.include_router(router_sources, prefix="/api/v1")
    app.include_router(router_audit, prefix="/api/v1")
    
    # Health check
    @app.get("/health", tags=["Health"])
    async def health_check():
        return {"status": "healthy", "version": "0.1.0"}
    
    # Обработчики ошибок
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        logger.warning("Validation error", errors=exc.errors())
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"detail": exc.errors(), "code": "VALIDATION_ERROR"},
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        logger.error("Unhandled exception", error=str(exc), exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Internal server error", "code": "INTERNAL_ERROR"},
        )
    
    # Startup events
    @app.on_event("startup")
    async def startup_event():
        logger.info("Application startup", version="0.1.0")
        # Здесь будет инициализация БД, кэша и других сервисов
    
    # Shutdown events
    @app.on_event("shutdown")
    async def shutdown_event():
        logger.info("Application shutdown")
        # Здесь будет закрытие соединений
    
    return app


# Создание экземпляра приложения
app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
    )
