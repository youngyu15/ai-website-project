import asyncio
from datetime import datetime, timezone
from uuid import UUID
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession
from packages.common.src.common.schemas.predictions import CreatePredictionRequest, PredictionOut, PredictionPage
from api.deps import get_current_user
from api.repositories import predictions_repo as repo
from api.repositories.uploads_repo import get_upload
from api.db.base import get_session, async_session_factory
from api.services.predictions_service import run_ml_pipeline
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("", response_model=PredictionPage)
async def list_predictions(limit: int = 20, cursor: str | None = None, user = Depends(get_current_user), db: AsyncSession = Depends(get_session)):
    before = datetime.fromisoformat(cursor) if cursor else None
    items = await repo.list_predictions(db, owner_id=user.id, limit=limit, before=before)

    out: list[PredictionOut] = []
    for p in items:
        try:
            logger.debug(
                "Validating pred id=%s stages_type=%s stages_keys=%s",
                getattr(p, "id", None),
                type(getattr(p, "stages", None)),
                list((getattr(p, "stages", {}) or {}).keys()),
            )
            out.append(PredictionOut.model_validate(p, from_attributes=True))
        except ValidationError:
            # Fallback: coerce stages and build explicitly
            payload = {
                "id": p.id,
                "status": p.status,
                "created_at": p.created_at,
                "updated_at": p.updated_at,
                "file_id": p.file_id,
                "stages": ensure_default_stages(p.stages),
                "result": p.result,
                "error": p.error,
                "label": p.label,
                "confidence": p.confidence,
            }
            logger.warning("Coerced stages for pred id=%s", p.id)
            out.append(PredictionOut.model_validate(payload))

    return PredictionPage(items=[PredictionOut.model_validate(p, from_attributes=True) for p in items], next_cursor=None)

@router.post("", response_model=PredictionOut, status_code=status.HTTP_202_ACCEPTED)
async def create_prediction(body: CreatePredictionRequest, background: BackgroundTasks, user = Depends(get_current_user), db: AsyncSession = Depends(get_session)):
    up = await get_upload(db, upload_id=body.file_id, owner_id=user.id)
    if not up:
        raise HTTPException(status_code=422, detail="file_id not found")
    
    pred = await repo.create_prediction(db, owner_id=user.id, file_id=body.file_id)
    if pred is None:
        raise HTTPException(500, "Failed to create prediction")

    async def _run_detached(pred_id: UUID):
        async with async_session_factory() as s:
            await run_ml_pipeline(s, pred_id=pred_id)

    background.add_task(_run_detached, pred.id)
    return PredictionOut.model_validate(pred, from_attributes=True)

@router.get("/{pred_id}", response_model=PredictionOut)
async def get_prediction(pred_id: UUID, user = Depends(get_current_user), db: AsyncSession = Depends(get_session)):
    pred = await repo.get_prediction(db, pred_id=pred_id, owner_id=user.id)
    logger.debug(
        "Before update: stages type=%s keys=%s",
        type(pred.stages),
        list((pred.stages or {}).keys())
    )
    if not pred:
        raise HTTPException(status_code=404)
    return PredictionOut.model_validate(pred, from_attributes=True)

@router.post("/{pred_id}/retry", response_model=PredictionOut, status_code=202)
async def retry_prediction(
    pred_id: UUID,
    background: BackgroundTasks,
    user = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    pred = await repo.get_prediction(db, pred_id=pred_id, owner_id=user.id)
    if not pred:
        raise HTTPException(status_code=404)

    # Only retry if not terminal
    terminal = {"succeeded", "failed"}
    if pred.status in terminal:
        return PredictionOut.model_validate(pred, from_attributes=True)

    # Guard: if it's already "processing" and recently updated, skip duplicate
    if pred.status == "processing" and (pred.updated_at and (datetime.now(timezone.utc) - pred.updated_at).total_seconds() < 10):
        return PredictionOut.model_validate(pred, from_attributes=True)

    # Reset to processing + clear/normalize stages for a clean rerun
    pred.status = "processing"
    pred.error = None
    pred.stages = [
        {"name": "face_detection", "status": "processing", "result": None},
        {"name": "classification", "status": "pending", "result": None},
    ]
    pred.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(pred)

    async def _run(pred_id: UUID):
        async with async_session_factory() as s:
            await run_ml_pipeline(s, pred_id=pred_id)

    # Use create_task or BackgroundTasks; both are fine
    asyncio.create_task(_run(pred.id))
    return PredictionOut.model_validate(pred, from_attributes=True)

def ensure_default_stages(d: dict | None) -> dict:
    d = dict(d or {})
    d.setdefault("face_detection", {"name": "face_detection", "status": "pending", "result": None})
    d.setdefault("classification", {"name": "classification", "status": "pending", "result": None})
    # normalize inner dicts
    for k in ("face_detection", "classification"):
        if not isinstance(d[k], dict):
            d[k] = {"name": k, "status": "pending", "result": None}
        else:
            d[k].setdefault("name", k)
            d[k].setdefault("status", "pending")
            d[k].setdefault("result", None)
    return d