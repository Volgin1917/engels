from typing import Optional, Dict, Any
from datetime import datetime
from .base import BaseSchema


class EntityCreate(BaseSchema):
    name: str
    description: Optional[str] = None
    type: str
    meta: Optional[Dict[str, Any]] = None


class EntityUpdate(BaseSchema):
    name: Optional[str] = None
    description: Optional[str] = None
    type: Optional[str] = None
    meta: Optional[Dict[str, Any]] = None


class EntityResponse(BaseSchema):
    id: int
    name: str
    description: Optional[str]
    type: str
    meta: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime
    created_by: int
    updated_by: int
