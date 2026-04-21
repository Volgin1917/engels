"""Модуль API."""

from src.api.routers import router_entities, router_relations, router_sources, router_audit
from src.api.dependencies import get_db, get_current_user, get_services, ServiceDependencies
from src.api.schemas import (
    EntityCreate, EntityUpdate, EntityResponse,
    RelationCreate, RelationUpdate, RelationResponse,
    SourceCreate, SourceResponse,
    AuditLogResponse, PaginatedResponse, ErrorResponse,
    EntityType, RelationType, SourceType, AuditAction
)

__all__ = [
    # Routers
    "router_entities",
    "router_relations",
    "router_sources",
    "router_audit",
    # Dependencies
    "get_db",
    "get_current_user",
    "get_services",
    "ServiceDependencies",
    # Schemas
    "EntityCreate",
    "EntityUpdate",
    "EntityResponse",
    "RelationCreate",
    "RelationUpdate",
    "RelationResponse",
    "SourceCreate",
    "SourceResponse",
    "AuditLogResponse",
    "PaginatedResponse",
    "ErrorResponse",
    "EntityType",
    "RelationType",
    "SourceType",
    "AuditAction",
]
