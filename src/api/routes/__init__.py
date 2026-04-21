"""Роутеры API."""
from .entities import router as entities_router
from .relations import router as relations_router
from .sources import router as sources_router
from .audit import router as audit_router
from .users import router as users_router
from .auth import router as auth_router

__all__ = [
    "entities_router",
    "relations_router",
    "sources_router",
    "audit_router",
    "users_router",
    "auth_router"
]
