from typing import Optional, Dict, Any
from datetime import datetime
from .base import BaseSchema


class RelationshipCreate(BaseSchema):
    source_entity_id: int
    target_entity_id: int
    relationship_type: str
    description: Optional[str] = None
    strength: float = 1.0
    metadata: Optional[Dict[str, Any]] = None


class RelationshipUpdate(BaseSchema):
    relationship_type: Optional[str] = None
    description: Optional[str] = None
    strength: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None


class RelationshipResponse(BaseSchema):
    id: int
    source_entity_id: int
    target_entity_id: int
    relationship_type: str
    description: Optional[str]
    strength: float
    metadata: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime
    created_by: int
    updated_by: int
