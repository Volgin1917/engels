from typing import Optional, Dict, Any
from datetime import datetime
from .base import BaseSchema


class AuditLogResponse(BaseSchema):
    id: int
    action: str
    entity_type: str
    entity_id: int
    old_values: Optional[Dict[str, Any]] = None
    new_values: Optional[Dict[str, Any]] = None
    timestamp: datetime
    user_id: int
