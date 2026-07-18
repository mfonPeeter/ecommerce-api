import uuid
from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field

from app.categories.schemas import CategoryPublicResponse


class ProductImagePublicResponse(SQLModel):
    id: uuid.UUID
    name: str
    url: str
    size: int
    mime_type: str
    created_at: datetime


class ProductPublicResponse(SQLModel):
    id: uuid.UUID
    name: str
    description: str
    quantity: int
    price: int
    is_available: bool
    category_id: Optional[uuid.UUID]
    category: Optional[CategoryPublicResponse]
    images: list[ProductImagePublicResponse] = []
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None


class ProductCreate(SQLModel):
    name: str = Field(min_length=1, max_length=100)
    description: str = Field(min_length=1)
    category_id: Optional[uuid.UUID] = None
    quantity: int
    price: int
    is_available: bool = True


class ProductUpdate(SQLModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    description: Optional[str] = Field(default=None, min_length=1)
    category_id: Optional[uuid.UUID] = None
    quantity: Optional[int] = None
    price: Optional[int] = None
    is_available: Optional[bool] = None
