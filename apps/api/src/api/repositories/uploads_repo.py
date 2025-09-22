from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from api.db.models import Upload

async def create_upload(db: AsyncSession, *, owner_id: UUID, content_type: str, bytes: int, storage_url: str) -> Upload:
    up = Upload(owner_id=owner_id, content_type=content_type, bytes=bytes, storage_url=storage_url)
    db.add(up)
    await db.commit()
    await db.refresh(up)
    return up

async def get_upload(db: AsyncSession, *, upload_id: UUID, owner_id: UUID) -> Upload | None:
    res = await db.execute(select(Upload).where(Upload.id == upload_id, Upload.owner_id == owner_id))
    return res.scalar_one_or_none()