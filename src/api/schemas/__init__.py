"""Pydantic схемы для API."""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class EntityType(str, Enum):
    PERSON = "person"
    ORGANIZATION = "organization"
    EVENT = "event"
    DOCUMENT = "document"
    LOCATION = "location"


# --- Базовые схемы ---
class BaseSchema(BaseModel):
    """Базовая схема с общими полями."""
    model_config = ConfigDict(from_attributes=True)
    
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# --- Схемы для Entity ---
class EntityCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Название сущности")
    entity_type: EntityType = Field(..., description="Тип сущности")
    description: Optional[str] = Field(None, max_length=2000, description="Описание")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Дополнительные метаданные")
    source_id: Optional[int] = Field(None, description="ID источника")
    needs_review: bool = Field(False, description="Требуется ли проверка экспертом")


class EntityUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    metadata: Optional[Dict[str, Any]] = None
    needs_review: Optional[bool] = None


class EntityResponse(BaseSchema):
    name: str
    entity_type: EntityType
    description: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    source_id: Optional[int] = None
    needs_review: bool = False
    review_comment: Optional[str] = None
    reviewed_by: Optional[int] = None
    reviewed_at: Optional[datetime] = None


# --- Схемы для Relation ---
class RelationType(str, Enum):
    KNOWS = "knows"
    WORKS_FOR = "works_for"
    LOCATED_IN = "located_in"
    PART_OF = "part_of"
    RELATED_TO = "related_to"


class RelationCreate(BaseModel):
    source_entity_id: int = Field(..., description="ID исходной сущности")
    target_entity_id: int = Field(..., description="ID целевой сущности")
    relation_type: RelationType = Field(..., description="Тип связи")
    description: Optional[str] = Field(None, max_length=1000)
    confidence: float = Field(1.0, ge=0.0, le=1.0, description="Уверенность в связи")


class RelationUpdate(BaseModel):
    description: Optional[str] = Field(None, max_length=1000)
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0)


class RelationResponse(BaseSchema):
    source_entity_id: int
    target_entity_id: int
    relation_type: RelationType
    description: Optional[str] = None
    confidence: float


# --- Схемы для Source ---
class SourceType(str, Enum):
    WEB_PAGE = "web_page"
    DOCUMENT = "document"
    DATABASE = "database"
    API = "api"
    MANUAL = "manual"


class SourceCreate(BaseModel):
    url: Optional[str] = Field(None, max_length=2048, description="URL источника")
    source_type: SourceType = Field(..., description="Тип источника")
    title: Optional[str] = Field(None, max_length=500, description="Заголовок")
    content_hash: Optional[str] = Field(None, max_length=64, description="Хэш содержимого")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class SourceResponse(BaseSchema):
    url: Optional[str] = None
    source_type: SourceType
    title: Optional[str] = None
    content_hash: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


# --- Схемы для AuditLog ---
class AuditAction(str, Enum):
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    REVIEW = "review"
    SYNC = "sync"


class AuditLogResponse(BaseSchema):
    user_id: Optional[int] = None
    action: AuditAction
    entity_type: str
    entity_id: Optional[int] = None
    changes: Dict[str, Any] = Field(default_factory=dict)
    comment: Optional[str] = None


# --- Схемы для ответов API ---
class PaginatedResponse(BaseModel):
    items: List[Any]
    total: int
    page: int
    page_size: int
    pages: int


class ErrorResponse(BaseModel):
    detail: str
    code: Optional[str] = None


# --- Схемы для Auth ---
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    username: Optional[str] = None
    user_id: Optional[int] = None


class LoginRequest(BaseModel):
    username: str
    password: str


class UserCreateAuth(BaseModel):
    username: str
    email: str
    password: str
    full_name: Optional[str] = None
