import asyncio
from datetime import datetime
from uuid import UUID
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from packages.common.src.common.schemas.predictions import CreatePredictionRequest, PredictionOut, PredictionPage
from api.deps import get_current_user
from api.repositories import predictions_repo as repo
from api.repositories.uploads_repo import get_upload
from api.db.base import get_session, async_session_factory
from api.services.predictions_service import run_ml_pipeline

router = APIRouter()

@router.get("", response_model=PredictionPage)
async def list_predictions(limit: int = 20, cursor: str | None = None, user = Depends(get_current_user), db: AsyncSession = Depends(get_session)):
    before = datetime.fromisoformat(cursor) if cursor else None
    items = await repo.list_predictions(db, owner_id=user.id, limit=limit, before=before)
    return PredictionPage(items=[PredictionOut.model_validate(p, from_attributes=True) for p in items], next_cursor=None)

@router.post("", response_model=PredictionOut, status_code=status.HTTP_202_ACCEPTED)
async def create_prediction(body: CreatePredictionRequest, background: BackgroundTasks, user = Depends(get_current_user), db: AsyncSession = Depends(get_session)):
    up = await get_upload(db, upload_id=body.file_id, owner_id=user.id)
    if not up:
        raise HTTPException(status_code=422, detail="file_id not found")
    pred = await repo.create_prediction(db, owner_id=user.id, file_id=body.file_id)

    def _run_detached(pred_id: UUID):
        async def _go():
            async with async_session_factory() as s:
                await run_ml_pipeline(s, pred_id=pred_id)
        asyncio.run(_go())

    background.add_task(_run_detached, pred.id)

@router.get("/{pred_id}", response_model=PredictionOut)
async def get_prediction(pred_id: UUID, user = Depends(get_current_user), db: AsyncSession = Depends(get_session)):
    pred = await repo.get_prediction(db, pred_id=pred_id, owner_id=user.id)
    if not pred:
        raise HTTPException(status_code=404)
    return PredictionOut.model_validate(pred, from_attributes=True)