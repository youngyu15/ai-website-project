# app/routers/uploads.py
from fastapi import APIRouter, Depends, HTTPException, status
from app.deps import get_current_user, User as DepUser
from app.models import CreateUploadRequest, UploadCreated, Upload
from app.store import uploads, MAX_UPLOAD_BYTES, now
from uuid import uuid4

router = APIRouter()

@router.post("", response_model=UploadCreated, status_code=status.HTTP_201_CREATED)
def create_upload(body: CreateUploadRequest, current: DepUser = Depends(get_current_user)):
    if body.file_bytes > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)
    file_id = f"file_{uuid4().hex}"
    uploads[file_id] = {
        "file_id": file_id,
        "owner_id": current.id,
        "content_type": body.content_type,
        "bytes": 0,
        "created_at": now(),
        "storage_url": f"https://storage.example.com/{file_id}",
    }
    return UploadCreated(
        file_id=file_id,
        upload_url=f"https://storage.example.com/upload/{file_id}?signature=fake",
        content_type=body.content_type,
        max_bytes=MAX_UPLOAD_BYTES,
        expires_at=now() + __import__("datetime").timedelta(minutes=10),
    )

@router.get("/{file_id}", response_model=Upload)
def get_upload(file_id: str, current: DepUser = Depends(get_current_user)):
    up = uploads.get(file_id)
    if not up or up["owner_id"] != current.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return Upload(**up)