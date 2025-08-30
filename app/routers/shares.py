# app/routers/shares.py
from fastapi import APIRouter, Depends, HTTPException, status
from uuid import uuid4
from datetime import timedelta
from app.deps import get_current_user, User as DepUser
from app.models import CreateShareRequest, Share, Prediction
from app.store import shares, predictions, now

router = APIRouter()

@router.post("/{pred_id}/share", response_model=Share, status_code=status.HTTP_201_CREATED)
def create_share(pred_id: str, body: CreateShareRequest | None = None, current: DepUser = Depends(get_current_user)):
    rec = predictions.get(pred_id)
    if not rec or rec["owner_id"] != current.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    share_id = f"shr_{uuid4().hex}"
    ttl = timedelta(seconds=(body.ttl_seconds if body and body.ttl_seconds else 86400))
    exp = now() + ttl
    shares[share_id] = {"pred_id": pred_id, "expires_at": exp}
    return Share(share_id=share_id, url=f"https://api.example.com/v1/shares/{share_id}", expires_at=exp)

@router.get("/{share_id}", response_model=Prediction)
def get_share(share_id: str):
    rec = shares.get(share_id)
    if not rec or rec["expires_at"] < now():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    pred = predictions.get(rec["pred_id"])  # public read of snapshot (here live)
    if not pred:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return Prediction(**pred["data"])

@router.delete("/{share_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_share(share_id: str, current: DepUser = Depends(get_current_user)):
    rec = shares.get(share_id)
    if not rec:
        return None
    # optional: enforce owner check by mapping share->owner via prediction
    shares.pop(share_id, None)
    return None