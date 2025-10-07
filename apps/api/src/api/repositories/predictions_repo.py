from datetime import datetime, timezone
from typing import Sequence
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from api.db.models import Prediction, PredictionStatus

DEFAULT_STAGES = {
    "face_detection": {"name": "face_detection", "status": "pending", "result": None},
    "classification": {"name": "classification", "status": "pending", "result": None},
}

async def create_prediction(db: AsyncSession, *, owner_id: UUID, file_id: UUID) -> Prediction:
    pred = Prediction(owner_id=owner_id, file_id=file_id, status=PredictionStatus.pending)
    db.add(pred)
    await db.commit()
    await db.refresh(pred)
    return pred

async def get_prediction(db: AsyncSession, *, pred_id: UUID, owner_id: UUID | None = None) -> Prediction | None:
    stmt = select(Prediction).where(Prediction.id == pred_id)
    if owner_id:
        stmt = stmt.where(Prediction.owner_id == owner_id)
    res = await db.execute(stmt)
    return res.scalar_one_or_none()

async def list_predictions(db: AsyncSession, *, owner_id: UUID, limit: int = 20, before: datetime | None = None) -> Sequence[Prediction]:
    stmt = select(Prediction).where(Prediction.owner_id == owner_id)
    if before:
        stmt = stmt.where(Prediction.created_at < before)
    stmt = stmt.order_by(Prediction.created_at.desc()).limit(limit)
    res = await db.execute(stmt)
    return res.scalars().all()

async def update_stage(db: AsyncSession, pred: Prediction, *, name: str, status: str, result: dict | None = None) -> Prediction:
    stages = dict(pred.stages or {})
    if name not in stages:
        stages[name] = DEFAULT_STAGES[name] if name in DEFAULT_STAGES else {
            "name": name, "status": "pending", "result": None
        }

    prev = dict(stages[name] or {})
    new_stage = {**prev, "name": name, "status": status, "result": result}
    stages[name] = new_stage

    pred.stages = stages

    pred.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(pred)
    return pred

async def mark_processing(db: AsyncSession, pred: Prediction) -> Prediction:
    pred.status = PredictionStatus.processing
    pred.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(pred)
    return pred

async def mark_succeeded(db: AsyncSession, pred: Prediction, *, result: dict) -> Prediction:
    pred.status = PredictionStatus.succeeded
    pred.result = result
    pred.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(pred)
    return pred

async def mark_failed(db: AsyncSession, pred: Prediction, *, error: dict) -> Prediction:
    pred.status = PredictionStatus.failed
    pred.error = error
    pred.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(pred)
    return pred
