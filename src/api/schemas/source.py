from typing import Optional, Dict, Any
from datetime import datetime
from .base import BaseSchema


class SourceCreate(BaseSchema):
    name: str
    type: str
    config: Dict[str, Any]
    is_active: bool = True


class SourceUpdate(BaseSchema):
    name: Optional[str] = None
    type: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class SourceResponse(BaseSchema):
    id: int
    name: str
    type: str
    config: Dict[str, Any]
    is_active: bool
    last_sync: Optional[datetime]
    created_at: datetime
    updated_at: datetime
