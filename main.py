"""Точка входа приложения."""
import uvicorn
from src.config import settings


def main():
    """Запустить сервер."""
    uvicorn.run(
        "src.api.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info" if not settings.DEBUG else "debug"
    )


if __name__ == "__main__":
    main()
