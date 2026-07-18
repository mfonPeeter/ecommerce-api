import uuid
from typing import Optional, TYPE_CHECKING
from sqlalchemy import Text
from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime, timezone

if TYPE_CHECKING:
    from app.users.models import User


class Category(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = Field(max_length=100, unique=True)
    description: str = Field(sa_type=Text)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    products: list["Product"] = Relationship(back_populates="category")


class Product(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="user.id", ondelete="CASCADE")
    category_id: Optional[uuid.UUID] = Field(
        default=None, foreign_key="category.id", ondelete="SET NULL"
    )
    name: str = Field(max_length=100, index=True)
    description: str = Field(sa_type=Text)
    quantity: int
    price: int
    is_available: bool = Field(default=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    deleted_at: Optional[datetime] = Field(default=None)

    images: list["ProductImage"] = Relationship(back_populates="product")
    category: Category | None = Relationship(back_populates="products")
    vendor: "User" = Relationship(back_populates="products")


class ProductImage(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    product_id: uuid.UUID = Field(foreign_key="product.id", ondelete="CASCADE")
    name: str = Field(max_length=255)
    url: str = Field(max_length=2048)
    size: int
    mime_type: str = Field(max_length=50)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    product: Product = Relationship(back_populates="images")
