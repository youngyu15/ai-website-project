# app/services/uploads.py
from datetime import datetime, timedelta, timezone
from uuid import UUID
import boto3
import mimetypes
from botocore.config import Config
from api.settings import settings

_s3 = boto3.client(
    "s3",
    region_name=settings.aws_region,
    endpoint_url=(settings.s3_endpoint_url or None),  # works for AWS/MinIO/localstack
    aws_access_key_id=settings.aws_access_key_id,
    aws_secret_access_key=settings.aws_secret_access_key.get_secret_value(),
    config=Config(signature_version="s3v4", s3={"addressing_style": "path"}),
)

def _ext_for(content_type: str) -> str:
    ext = mimetypes.guess_extension(content_type) or ""
    if content_type == "image/jpeg" and ext == ".jpe":
        ext = ".jpg"
    return ext

def object_key_for(file_id: UUID, content_type: str) -> str:
    return f"uploads/{file_id}{_ext_for(content_type)}"

def create_presigned_upload(*, file_id: UUID, content_type: str) -> dict:
    """
    Return a pre-signed **PUT** URL for S3.
    Frontend should PUT the file to `upload_url` with header `Content-Type`.
    """
    object_key = object_key_for(file_id, content_type)
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
