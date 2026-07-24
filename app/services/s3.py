import logging
import uuid
import boto3
from botocore.exceptions import ClientError
from fastapi import UploadFile, HTTPException, status
from app.config import settings

logger = logging.getLogger(__name__)

s3_client = boto3.client(
    "s3",
    aws_access_key_id=settings.aws_access_key_id,
    aws_secret_access_key=settings.aws_secret_access_key,
    region_name=settings.aws_default_region,
    endpoint_url=f"https://s3.{settings.aws_default_region}.amazonaws.com",
)

ALLOWED_MIME_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
}

MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB


def validate_image(file: UploadFile) -> None:
    """Validate file type and size before uploading to S3."""
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only JPEG, PNGN and WebP images are allowed",
        )

    if file.size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size must not exceed 5MB",
        )


def upload_file_to_s3(file: UploadFile, vendor_id: str) -> tuple[str, str]:
    """Upload an image to S3 and return the public URL."""
    key = f"products/{vendor_id}/{uuid.uuid4()}-{file.filename}"

    try:
        s3_client.upload_fileobj(
            file.file,
            settings.aws_bucket_name,
            key,
            ExtraArgs={"ContentType": file.content_type},
        )
    except ClientError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload image",
        )

    url = f"https://{settings.aws_bucket_name}.s3.{settings.aws_default_region}.amazonaws.com/{key}"
    return url, key


def delete_from_s3(key: str) -> None:
    """Delete a file from S3 by key."""
    try:
        s3_client.delete_object(
            Bucket=settings.aws_bucket_name,
            Key=key,
        )
    except ClientError as e:
        logger.exception(f"Failed to delete file from S3: {key} - {e}")
