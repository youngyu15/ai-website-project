from uuid import UUID
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.deps import get_current_user
from app.schemas import CreateShareRequest, ShareOut, PublicPredictionOut
from app.repositories.shares import create_share, get_share
from app.repositories.predictions import get_prediction
from app.db.engine import get_session

router = APIRouter()

@router.post("/{pred_id}/share", response_model=ShareOut, status_code=201)
async def create_share_route(pred_id: UUID, body: CreateShareRequest | None = None, user = Depends(get_current_user), db: AsyncSession = Depends(get_session)):
    pred = await get_prediction(db, pred_id=pred_id, owner_id=user.id)
    if not pred:
        raise HTTPException(status_code=404)
    ttl = body.ttl_seconds if body and body.ttl_seconds else 86400
    share = await create_share(db, prediction_id=pred_id, ttl_seconds=ttl)
    return ShareOut(share_id=share.public_id, url=f"/v1/shares/{share.public_id}", expires_at=share.expires_at)

@router.get("/{public_id}", response_model=PublicPredictionOut, include_in_schema=False)
async def get_public_share(public_id: str, db: AsyncSession = Depends(get_session)):
    share = await get_share(db, public_id=public_id)
    if not share or share.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=404)
    pred = await get_prediction(db, pred_id=share.prediction_id)
    if not pred:
        raise HTTPException(status_code=404)
    return PublicPredictionOut.model_validate(pred, from_attributes=True)