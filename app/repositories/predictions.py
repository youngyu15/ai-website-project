# app/repositories/predictions.py
from typing import Optional, Sequence
from uuid import UUID
from sqlalchemy import select
from sqlmodel import col
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import Prediction, PredictionStatus

async def create_prediction(db: AsyncSession, *, owner_id: UUID, file_id: UUID) -> Prediction:
    pred = Prediction(owner_id=owner_id, file_id=file_id, status=PredictionStatus.pending)
    db.add(pred)
    await db.commit()
    await db.refresh(pred)
    return pred

async def get_prediction(db: AsyncSession, *, pred_id: UUID, owner_id: Optional[UUID] = None) -> Optional[Prediction]:
    stmt = select(Prediction).where(Prediction.id == pred_id)
    if owner_id:
        stmt = stmt.where(Prediction.owner_id == owner_id)
    res = await db.execute(stmt)
    return res.scalar_one_or_none()

async def list_predictions(
    db: AsyncSession, *, owner_id: UUID, limit: int = 20, cursor: Optional[datetime] = None
) -> Sequence[Prediction]:
    stmt = (
        select(Prediction)
        .where(Prediction.owner_id == owner_id)
        .order_by(Prediction.created_at.desc())
        .limit(limit)
    )
    if cursor:
        stmt = stmt.where(Prediction.created_at < cursor)
    res = await db.execute(stmt)
    return res.scalars().all()

async def mark_prediction_succeeded(
    db: AsyncSession, *, pred: Prediction, result: dict, label: Optional[str], confidence: Optional[float]
) -> Prediction:
    pred.status = PredictionStatus.succeeded
    pred.result = result
    pred.error = None
    pred.label = label
    pred.confidence = confidence
    await db.commit()
    await db.refresh(pred)
    return pred

async def mark_prediction_failed(db: AsyncSession, *, pred: Prediction, error: dict) -> Prediction:
    pred.status = PredictionStatus.failed
    pred.error = error
    await db.commit()
    await db.refresh(pred)
    return pred
