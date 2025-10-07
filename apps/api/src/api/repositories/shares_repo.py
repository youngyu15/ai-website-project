from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from api.db.models import Share, Prediction

async def create_share(db: AsyncSession, *, prediction_id: UUID, ttl_seconds: int) -> Share:
    public_id = f"shr_{uuid4().hex[:20]}"
    share = Share(prediction_id=prediction_id, public_id=public_id, expires_at=datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds))
    db.add(share)
    await db.commit()
    await db.refresh(share)
    return share

async def get_share(db: AsyncSession, *, public_id: str) -> Share | None:
    now = datetime.now(timezone.utc)
    res = await db.execute(select(Share).where(Share.public_id == public_id, Share.expires_at > now).order_by(Share.created_at.desc()).limit(1))
    return res.scalar_one_or_none()

async def get_active_share_for_prediction(db: AsyncSession, *, prediction_id: UUID) -> Share | None:
    now = datetime.now(timezone.utc)
    stmt = select(Share).where(Share.prediction_id == prediction_id, Share.expires_at > now).order_by(Share.created_at.desc()).limit(1)
    res = await db.execute(stmt)
    return res.scalar_one_or_none()