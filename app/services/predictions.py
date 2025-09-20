import asyncio
from datetime import datetime, timezone
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories import predictions as repo

# Simulate ML pipeline: face detection + classification
async def run_dummy_pipeline(db: AsyncSession, *, pred_id: UUID):
    pred = await repo.get_prediction(db, pred_id=pred_id)
    if not pred:
        return
    # mark processing
    pred.status = pred.status.processing if hasattr(pred.status, "processing") else "processing"
    pred.updated_at = datetime.now(timezone.utc)
    pred.stages = [
        {"name": "face_detection", "status": "processing", "result": None},
        {"name": "classification", "status": "pending", "result": None},
    ]
    await db.commit(); await db.refresh(pred)

    # fake face detection
    await asyncio.sleep(0.3)
    pred.stages[0] = {"name": "face_detection", "status": "succeeded", "result": {"detected": True}}
    pred.stages[1] = {"name": "classification", "status": "processing", "result": None}
    await db.commit(); await db.refresh(pred)

    # fake classification
    await asyncio.sleep(0.3)
    result = {"face_detected": True, "label": "cat", "confidence": 0.98, "image_url": None}
    pred.status = "succeeded"
    pred.stages[1] = {"name": "classification", "status": "succeeded", "result": {"label": "cat", "confidence": 0.98}}
    pred.result = result
    pred.label = "cat"
    pred.confidence = 0.98
    pred.updated_at = datetime.now(timezone.utc)
    await db.commit(); await db.refresh(pred)