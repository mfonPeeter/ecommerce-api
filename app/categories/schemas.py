import uuid
from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field


class CategoryPublicResponse(SQLModel):
    id: uuid.UUID
    name: str
    description: str
    created_at: datetime
    updated_at: datetime


class CategoryCreate(SQLModel):
    name: str = Field(min_length=1, max_length=100)
    description: str = Field(min_length=1)


class CategoryUpdate(SQLModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    description: Optional[str] = Field(default=None, min_length=1)
