from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import Share, Prediction

async def create_share(db: AsyncSession, *, prediction_id: UUID, ttl_seconds: int) -> Share:
    public_id = f"shr_{uuid4().hex[:20]}"
    share = Share(prediction_id=prediction_id, public_id=public_id, expires_at=datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds))
    db.add(share)
    await db.commit()
    await db.refresh(share)
    return share

async def get_share(db: AsyncSession, *, public_id: str) -> Share | None:
    res = await db.execute(select(Share).where(Share.public_id == public_id))
    return res.scalar_one_or_none()