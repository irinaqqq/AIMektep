from enum import Enum
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr


class StatusRole(str, Enum):
    user = "user"
    # admin = "admin"


class UserBase(BaseModel):
    email: EmailStr
    phone_number: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class UserCreate(UserBase):
    password: str
    role: StatusRole = StatusRole.user


class UserUpdate(BaseModel):
    phone_number: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class UserSchema(UserBase):
    model_config = {
        "from_attributes": True
    } 


class UserAdmin(UserSchema):
    id: int
    role: str
    created_at: datetime