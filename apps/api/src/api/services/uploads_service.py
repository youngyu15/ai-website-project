# app/services/uploads.py
from datetime import datetime, timedelta, timezone
from uuid import UUID
import boto3
from botocore.config import Config
from api.settings import settings

_s3 = boto3.client(
    "s3",
    region_name=settings.aws_region,
    endpoint_url=(settings.s3_endpoint_url or None),  # works for AWS/MinIO/localstack
    config=Config(signature_version="s3v4"),
)

def create_presigned_upload(*, file_id: UUID, content_type: str) -> dict:
    """
    Return a pre-signed **PUT** URL for S3.
    Frontend should PUT the file to `upload_url` with header `Content-Type`.
    """
    object_key = f"uploads/{file_id}"
    url = _s3.generate_presigned_url(
        ClientMethod="put_object",
        Params={
            "Bucket": settings.s3_bucket,
            "Key": object_key,
            "ContentType": content_type,
        },
        ExpiresIn=600,  # seconds
    )
    return {
        "upload_url": url,
        "expires_at": datetime.now(timezone.utc) + timedelta(minutes=10),
        "content_type": content_type,
        "max_bytes": settings.max_upload_bytes,
        "object_key": object_key,
    }
