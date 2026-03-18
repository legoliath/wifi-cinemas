import uuid
from datetime import datetime
from pydantic import BaseModel

class UserBase(BaseModel):
    email: str
    name: str
    phone: str | None = None
    lang: str = "fr"

class UserCreate(UserBase):
    role: str = "user"
    firebase_uid: str | None = None

class UserUpdate(BaseModel):
    name: str | None = None
    phone: str | None = None
    lang: str | None = None

class UserResponse(UserBase):
    id: uuid.UUID
    role: str
    is_active: bool
    created_at: datetime
    model_config = {"from_attributes": True}

class UserListResponse(BaseModel):
    users: list[UserResponse]
    total: int
