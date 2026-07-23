import uuid
from typing import Annotated
from fastapi import APIRouter, HTTPException, status, Form, File, UploadFile

from .models import Product, ProductImage
from .schemas import ProductPublicResponse, ProductCreate
from app.auth.dependencies import CurrentVendor
from app.database import SessionDep
from app.services.s3 import validate_image, upload_file_to_s3, delete_from_s3

router = APIRouter(prefix="/api/v1/products", tags=["Products"])


@router.post(
    "", response_model=ProductPublicResponse, status_code=status.HTTP_201_CREATED
)
async def create_products(
    current_user: CurrentVendor,
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

    product = Product.model_validate(product_data, update={"user_id": current_user.id})

    for file in files:
        validate_image(file)

    session.add(product)
    session.commit()
    session.refresh(product)

    uploaded_keys = []

    try:
        for file in files:
            url, key = upload_file_to_s3(file, str(current_user.id))
            uploaded_keys.append(key)
            product_image = ProductImage(
                product_id=product.id,
                name=file.filename,
                url=url,
                size=file.size,
                mime_type=file.content_type,
            )
            session.add(product_image)
        session.commit()
        session.refresh(product)
    except HTTPException:
        # delete product from database
        session.delete(product)
        session.commit()
        # delete already uploaded files from S3
        for key in uploaded_keys:
            delete_from_s3(key)
        raise

    return product
