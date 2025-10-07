# app/routers/uploads.py
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from packages.common.src.common.schemas.uploads import CreateUploadRequest, UploadCreated, UploadOut
from api.settings import settings
from api.deps import get_current_user
from api.services.uploads_service import create_presigned_upload
from api.repositories.uploads_repo import create_upload, get_upload
from api.db.base import get_session
from uuid import uuid4
from pathlib import Path
import shutil

router = APIRouter()
UPLOAD_DIR = Path("./var/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

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

@router.post("/dev-direct", response_model=UploadCreated, status_code=201)
async def dev_direct_upload(
    file: UploadFile = File(...),
    user = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)):

    allowed_ext = {".jpg",".jpeg",".png",".gif",".webp"}

    ext = Path(file.filename or "").suffix.lower()
    if not (file.content_type.startswith("image/") or ext in allowed_ext):
        raise HTTPException(400, "Only images are allowed")
    fid = f"{uuid4()}"
    ext = (Path(file.filename).suffix or ".bin")[:10]
    dest = UPLOAD_DIR / f"{fid}{ext}"
    with dest.open("wb") as f:
        shutil.copyfileobj(file.file, f)

    up = await create_upload(
        db,
        owner_id=user.id,
        content_type=ext,
        bytes=0,
        storage_url=str(dest),  # set after we have up.id
    )

    return UploadCreated(
        file_id=up.id,
        upload_url=str(dest),
        content_type=file.content_type,
        max_bytes=settings.max_upload_bytes,
        expires_at=settings.access_token_expire_minutes * 60,
    )
