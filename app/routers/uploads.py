# app/routers/uploads.py
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.deps import get_current_user
from app.schemas import CreateUploadRequest, UploadCreated, UploadOut
from app.services.uploads import create_presigned_upload
from app.repositories.uploads import create_upload, get_upload
from app.db.engine import get_session

router = APIRouter()

@router.post("", response_model=UploadCreated, status_code=201)
async def create_upload_route(
    body: CreateUploadRequest,
    user = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    if body.file_bytes > settings.max_upload_bytes:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)

    # Presign first so we know the exact key
    presigned = create_presigned_upload(file_id=user.id, content_type=body.content_type)  # temp; replaced below

    # Create DB record with final S3 location using upload id as the key
    # (Regenerate presign bound to the created Upload.id)
    up = await create_upload(
        db,
        owner_id=user.id,
        content_type=body.content_type,
        bytes=0,
        storage_url="s3://placeholder",  # set after we have up.id
    )
    presigned = create_presigned_upload(file_id=up.id, content_type=body.content_type)

    # Update storage_url to match
    up.storage_url = f"s3://{settings.s3_bucket}/{presigned['object_key']}"
    await db.commit()

    return UploadCreated(
        file_id=up.id,
        upload_url=presigned["upload_url"],
        content_type=body.content_type,
        max_bytes=presigned["max_bytes"],
        expires_at=presigned["expires_at"],
    )

@router.get("/{file_id}", response_model=UploadOut)
async def get_upload_route(
    file_id: UUID,
    user = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    up = await get_upload(db, upload_id=file_id, owner_id=user.id)
    if not up:
        raise HTTPException(status_code=404)
    return UploadOut.model_validate(up, from_attributes=True)
