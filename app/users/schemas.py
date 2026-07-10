import uuid
from datetime import datetime
from sqlmodel import SQLModel, Field
from pydantic import EmailStr
from typing import Optional

from .models import UserRole


class UserPublicResponse(SQLModel):
    id: uuid.UUID
    email: EmailStr
    first_name: str
    last_name: str
    phone_no: Optional[str]
    is_verified: bool
    role: UserRole
    created_at: datetime
    updated_at: datetime


class UserCreate(SQLModel):
    email: EmailStr
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    phone_no: Optional[str] = Field(default=None, min_length=5, max_length=20)
    password: str = Field(min_length=8)
    role: UserRole = Field(default=UserRole.CUSTOMER)


class UserUpdate(SQLModel):
    first_name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    phone_no: Optional[str] = Field(default=None, min_length=5, max_length=20)


class UserPasswordUpdate(SQLModel):
    current_password: str = Field(min_length=8)
    new_password: str = Field(min_length=8)
