from typing import Optional
from datetime import datetime
from .base import BaseSchema


class UserCreate(BaseSchema):
    username: str
    email: str
    password: str
    full_name: Optional[str] = None


class UserUpdate(BaseSchema):
    username: Optional[str] = None
    email: Optional[str] = None
    full_name: Optional[str] = None
    is_active: Optional[bool] = None


class UserResponse(BaseSchema):
    id: int
    username: str
    email: str
    full_name: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime
