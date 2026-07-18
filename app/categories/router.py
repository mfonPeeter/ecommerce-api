import uuid
from typing import Annotated
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, status, Query
from sqlmodel import select
from sqlalchemy.exc import MultipleResultsFound

from .schemas import (
    CategoryPublicResponse,
    CategoryCreate,
    CategoryUpdate,
    CategoryFilterParams,
)
from .models import Category
from app.database import SessionDep
from app.auth.dependencies import CurrentUser, CurrentVendor

router = APIRouter(prefix="/api/v1/category", tags=["Category"])


@router.get("", response_model=list[CategoryPublicResponse])
async def get_categories(
    _: CurrentUser,
    filters: Annotated[CategoryFilterParams, Query()],
    session: SessionDep,
):
    """Return all categories"""
    query = select(Category)

    if filters.search:
        query = query.where(Category.name.icontains(filters.search))

    categories = session.exec(query).all()
    return categories


@router.post(
    "", response_model=CategoryPublicResponse, status_code=status.HTTP_201_CREATED
)
async def create_category(
    payload: CategoryCreate, _: CurrentVendor, session: SessionDep
):
    """Create a new category"""
    try:
        existing_category = session.exec(
            select(Category).where(Category.name == payload.name)
        ).one_or_none()
    except MultipleResultsFound:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Data integrity error",
        )

    if existing_category:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Category already exists"
        )

    category = Category.model_validate(payload)
    session.add(category)
    session.commit()
    session.refresh(category)

    return category


@router.patch("/{category_id}", response_model=CategoryPublicResponse)
async def update_category(
    category_id: uuid.UUID,
    payload: CategoryUpdate,
    _: CurrentVendor,
    session: SessionDep,
):
    """Update an exisitng category"""
    category_db = session.get(Category, category_id)
    if not category_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Category does not exist"
        )

    if payload.name and payload.name != category_db.name:
        try:
            existing_category = session.exec(
                select(Category).where(Category.name == payload.name)
            ).one_or_none()
        except MultipleResultsFound:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Data integrity error",
            )

        if existing_category:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="Category already exists"
            )

    category_data = payload.model_dump(exclude_unset=True)
    category_data["updated_at"] = datetime.now(timezone.utc)
    category_db.sqlmodel_update(category_data)
    session.add(category_db)
    session.commit()
    session.refresh(category_db)

    return category_db


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(
    category_id: uuid.UUID,
    _: CurrentVendor,
    session: SessionDep,
):
    """Delete an existing category"""
    category_db = session.get(Category, category_id)

    if not category_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Category does not exist"
        )

    session.delete(category_db)
    session.commit()
