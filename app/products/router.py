import uuid
import logging
from datetime import datetime, timezone
from typing import Annotated, Optional
from fastapi import (
    APIRouter,
    HTTPException,
    status,
    Form,
    File,
    UploadFile,
    Query,
    Request,
)
from sqlmodel import select, func

from .models import Product, ProductImage
from .schemas import (
    ProductPublicResponse,
    ProductCreate,
    ProductFilterParams,
    ProductListResponse,
    PaginationMeta,
    ProductUpdate,
)
from app.auth.dependencies import CurrentVendor
from app.database import SessionDep
from app.services.s3 import validate_image, upload_file_to_s3, delete_from_s3

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/products", tags=["Products"])


# --------------------------------------
# PUBLICLY ACCESSIBLE
# --------------------------------------


@router.get("", response_model=ProductListResponse)
async def get_products(
    session: SessionDep, filters: Annotated[ProductFilterParams, Query()]
):
    """Return all products with optional filtering and pagination. Publicly accessible."""
    query = select(Product)

    if filters.search:
        query = query.where(Product.name.icontains(filters.search))
    if filters.category_id:
        query = query.where(Product.category_id == filters.category_id)
    if filters.min_price:
        query = query.where(Product.price >= filters.min_price)
    if filters.max_price:
        query = query.where(Product.price <= filters.max_price)

    query = query.where(Product.is_available == True)

    # exclude soft deleted products
    query = query.where(Product.deleted_at == None)

    # count filtered results before pagination so total reflects actual matches
    total = session.exec(select(func.count()).select_from(query.subquery())).one()

    # apply pagination after counting
    query = query.limit(filters.limit).offset(filters.offset)
    products = session.exec(query).all()

    logger.debug("Retrieved all products")
    return ProductListResponse(
        products=products,
        pagination=PaginationMeta(
            total=total, limit=filters.limit, offset=filters.offset
        ),
    )


@router.get("/{product_id}", response_model=ProductPublicResponse)
async def get_product(product_id: uuid.UUID, session: SessionDep):
    """Return the details of a single product. Publicly accessible."""
    product = session.get(Product, product_id)

    if not product or product.deleted_at is not None:
        logger.warning(f"Retrieval attempt of a non existent product: {product_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Product does not exist"
        )

    logger.info(f"Retrieved product {product.id}")
    return product


# --------------------------------------
# VENDOR ACCESSIBLE
# --------------------------------------


@router.get("/vendor", response_model=ProductListResponse)
async def get_vendor_products(
    current_vendor: CurrentVendor,
    session: SessionDep,
    filters: Annotated[ProductFilterParams, Query()],
):
    """Return all products for the currently authenticated vendor with optional filtering and pagination."""
    query = select(Product).where(Product.user_id == current_vendor.id)

    if filters.search:
        query = query.where(Product.name.icontains(filters.search))
    if filters.category_id:
        query = query.where(Product.category_id == filters.category_id)
    if filters.min_price:
        query = query.where(Product.price >= filters.min_price)
    if filters.max_price:
        query = query.where(Product.price <= filters.max_price)

    # exclude soft deleted products
    query = query.where(Product.deleted_at == None)

    # count filtered results before pagination so total reflects actual matches
    total = session.exec(select(func.count()).select_from(query.subquery())).one()

    # apply pagination after counting
    query = query.limit(filters.limit).offset(filters.offset)
    products = session.exec(query).all()

    logger.debug(f"Retrieved all products for vendor {current_vendor.id}")
    return ProductListResponse(
        products=products,
        pagination=PaginationMeta(
            total=total, limit=filters.limit, offset=filters.offset
        ),
    )


@router.get("/vendor/deleted", response_model=ProductListResponse)
async def get_deleted_products(
    current_vendor: CurrentVendor,
    session: SessionDep,
    filters: Annotated[ProductFilterParams, Query()],
):
    """Return all deleted products for the currently authenticated vendor"""
    query = select(Product).where(
        Product.user_id == current_vendor.id, Product.deleted_at != None
    )

    if filters.search:
        query = query.where(Product.name.icontains(filters.search))
    if filters.category_id:
        query = query.where(Product.category_id == filters.category_id)
    if filters.min_price:
        query = query.where(Product.price >= filters.min_price)
    if filters.max_price:
        query = query.where(Product.price <= filters.max_price)

    total = session.exec(select(func.count()).select_from(query.subquery())).one()

    query = query.limit(filters.limit).offset(filters.offset)
    products = session.exec(query).all()

    logger.info(f"Retrieved all deleted products for vendor {current_vendor.id}")
    return ProductListResponse(
        products=products,
        pagination=PaginationMeta(
            total=total, limit=filters.limit, offset=filters.offset
        ),
    )


@router.get("/vendor/{product_id}", response_model=ProductPublicResponse)
async def get_vendor_product(
    product_id: uuid.UUID, current_vendor: CurrentVendor, session: SessionDep
):
    """Return the details of a single product for the currently authenticated vendor."""
    product = session.exec(
        select(Product).where(
            Product.user_id == current_vendor.id, Product.id == product_id
        )
    ).one_or_none()

    if not product or product.deleted_at is not None:
        logger.warning(f"Retrieval attempt of a non existent product: {product_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Product does not exist"
        )

    logger.info(f"Retrieved product {product.id} for vendor {current_vendor.id}")
    return product


@router.post(
    "/vendor", response_model=ProductPublicResponse, status_code=status.HTTP_201_CREATED
)
async def create_products(
    current_vendor: CurrentVendor,
    session: SessionDep,
    name: Annotated[str, Form()],
    description: Annotated[str, Form()],
    quantity: Annotated[int, Form()],
    price: Annotated[int, Form()],
    files: Annotated[list[UploadFile], File()],
    category_id: Annotated[uuid.UUID | None, Form()] = None,
    is_available: Annotated[bool, Form()] = True,
):
    """Create a new product with images. Only vendors can create products."""
    product_data = ProductCreate(
        name=name,
        description=description,
        category_id=category_id,
        quantity=quantity,
        price=price,
        is_available=is_available,
    )

    product = Product.model_validate(
        product_data, update={"user_id": current_vendor.id}
    )

    for file in files:
        validate_image(file)

    session.add(product)
    session.commit()
    session.refresh(product)

    uploaded_keys = []

    try:
        for file in files:
            url, key = upload_file_to_s3(file, str(current_vendor.id))
            uploaded_keys.append(key)
            product_image = ProductImage(
                product_id=product.id,
                name=file.filename,
                url=url,
                key=key,
                size=file.size,
                mime_type=file.content_type,
            )
            session.add(product_image)
        session.commit()
        session.refresh(product)
    except HTTPException:
        logger.warning(
            f"Product creation failed for vendor {current_vendor.id} - rolling back"
        )
        # delete product from database
        session.delete(product)
        session.commit()
        # delete already uploaded files from S3
        for key in uploaded_keys:
            delete_from_s3(key)
        raise

    logger.info(f"New product {product.id} created by vendor {current_vendor.id}")
    return product


@router.patch("/vendor/{product_id}", response_model=ProductPublicResponse)
async def update_product(
    request: Request,
    product_id: uuid.UUID,
    current_vendor: CurrentVendor,
    session: SessionDep,
    name: Annotated[Optional[str], Form()] = None,
    description: Annotated[Optional[str], Form()] = None,
    category_id: Annotated[Optional[uuid.UUID], Form()] = None,
    quantity: Annotated[Optional[int], Form()] = None,
    price: Annotated[Optional[int], Form()] = None,
    is_available: Annotated[Optional[bool], Form()] = None,
    files: Annotated[Optional[list[UploadFile]], File()] = None,
):
    """Update a product. Only vendors can update products."""
    product_db = session.exec(
        select(Product).where(
            Product.user_id == current_vendor.id, Product.id == product_id
        )
    ).one_or_none()

    if not product_db or product_db.deleted_at is not None:
        logger.warning(f"Retrieval attempt of a non existent product: {product_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Product does not exist"
        )

    # get submitted form keys to distinguish between unset fields and explictily cleared fields
    form_data = await request.form()
    submitted_keys = set(form_data.keys())

    product_data = ProductUpdate(
        name=name,
        description=description,
        category_id=category_id,
        quantity=quantity,
        price=price,
        is_available=is_available,
    )
    product = product_data.model_dump(include=submitted_keys, exclude_unset=True)
    product["updated_at"] = datetime.now(timezone.utc)

    if files:
        # validate all files before touching the database
        for file in files:
            validate_image(file)

    product_db.sqlmodel_update(product)
    session.add(product_db)
    session.commit()
    session.refresh(product_db)

    if files:
        # upload new images to S3 and save URLs to database
        # if any upload fails, clean up already uploaded S3 files
        uploaded_keys = []
        try:
            for file in files:
                url, key = upload_file_to_s3(file, str(current_vendor.id))
                uploaded_keys.append(key)
                product_image = ProductImage(
                    product_id=product_db.id,
                    name=file.filename,
                    url=url,
                    key=key,
                    size=file.size,
                    mime_type=file.content_type,
                )
                session.add(product_image)
            session.commit()
            session.refresh(product_db)
        except HTTPException:
            logger.warning(
                f"Product update failed for vendor {current_vendor.id} - rolling back"
            )
            for key in uploaded_keys:
                delete_from_s3(key)
            raise

    logger.info(f"Product {product.id} updated by vendor {current_vendor.id}")
    return product_db


@router.delete("/vendor/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: uuid.UUID, current_vendor: CurrentVendor, session: SessionDep
):
    """Soft delete a product. The product is hidden from public listings, but not permanently removed."""
    product_db = session.exec(
        select(Product).where(
            Product.user_id == current_vendor.id, Product.id == product_id
        )
    ).one_or_none()

    if not product_db or product_db.deleted_at is not None:
        logger.warning(f"Retrieval attempt of a non existent product: {product_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Product does not exist"
        )

    logger.info(f"Product {product_db.id} soft deleted by vendor {current_vendor.id}")
    product_db.deleted_at = datetime.now(timezone.utc)
    session.add(product_db)
    session.commit()


@router.post("/vendor/{product_id}/restore", response_model=ProductPublicResponse)
async def restore_deleted_product(
    product_id: uuid.UUID, current_vendor: CurrentVendor, session: SessionDep
):
    """Restore a soft deleted product and make it visible in public listings again."""
    product_db = session.exec(
        select(Product).where(
            Product.user_id == current_vendor.id, Product.id == product_id
        )
    ).one_or_none()

    if not product_db or product_db.deleted_at is None:
        logger.warning(
            f"Retrieval attempt of a non existent or non deleted product: {product_id}"
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product does not exist or is not deleted",
        )

    product_db.deleted_at = None
    session.add(product_db)
    session.commit()
    session.refresh(product_db)

    logger.info(f"Product {product_db.id} restored by vendor {current_vendor.id}")
    return product_db


@router.delete(
    "/vendor/{product_id}/image/{image_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def delete_product_image(
    product_id: uuid.UUID,
    image_id: uuid.UUID,
    current_vendor: CurrentVendor,
    session: SessionDep,
):
    """Delete a single image file."""
    product_image_db = session.exec(
        select(ProductImage)
        .join(Product, ProductImage.product_id == Product.id)
        .where(
            ProductImage.id == image_id,
            ProductImage.product_id == product_id,
            Product.user_id == current_vendor.id,
        )
    ).one_or_none()

    if not product_image_db:
        logger.warning(f"Retrieval attempt of a non existent product: {product_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Product image does not exist"
        )

    delete_from_s3(product_image_db.key)

    logger.info(
        f"Product {product_image_db.product_id} image {product_image_db.id} deleted by vendor {current_vendor.id}"
    )
    session.delete(product_image_db)
    session.commit()
