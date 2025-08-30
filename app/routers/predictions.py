# app/routers/predictions.py
from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException, status
from typing import Optional, List
from uuid import uuid4
from datetime import timedelta
from app.models import (
    CreatePredictionRequest, Prediction, PredictionPage, Stage, ClassificationResult
)
from app.deps import get_current_user, User as DepUser
from app.store import predictions, uploads, now

router = APIRouter()

@router.get("", response_model=PredictionPage)
def list_predictions(cursor: Optional[str] = None, limit: int = 20, current: DepUser = Depends(get_current_user)):
    items: List[Prediction] = []
    # naive: return all owned predictions
    for p in predictions.values():
        if p["owner_id"] == current.id:
            items.append(Prediction(**p["data"]))
    return PredictionPage(items=sorted(items, key=lambda x: x.created_at, reverse=True)[:limit], next_cursor=None)

@router.post("", response_model=Prediction, status_code=status.HTTP_202_ACCEPTED)
def create_prediction(body: CreatePredictionRequest, background: BackgroundTasks, current: DepUser = Depends(get_current_user)):
    if body.file_id not in uploads:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="file_id not found")
    pred_id = f"pred_{uuid4().hex}"
    data = Prediction(
        id=pred_id,
        status="pending",
        created_at=now(),
        updated_at=now(),
        file_id=body.file_id,
        stages=[
            Stage(name="face_detection", status="pending"),
            Stage(name="classification", status="pending"),
        ],
        result=None,
        error=None,
    )
    predictions[pred_id] = {"owner_id": current.id, "data": data.model_dump()}

    background.add_task(_run_pipeline, pred_id)
    return data

@router.get("/{pred_id}", response_model=Prediction)
def get_prediction(pred_id: str, current: DepUser = Depends(get_current_user)):
    rec = predictions.get(pred_id)
    if not rec or rec["owner_id"] != current.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return Prediction(**rec["data"])

# --- background pipeline (fake) ---

def _run_pipeline(pred_id: str):
    import time
    rec = predictions[pred_id]
    data = rec["data"]

    # face detection
    data["status"] = "processing"
    data["stages"][0]["status"] = "processing"
    _persist(pred_id, data)
    time.sleep(0.5)
    data["stages"][0]["status"] = "succeeded"

    # classification
    data["stages"][1]["status"] = "processing"
    _persist(pred_id, data)
    time.sleep(0.5)

    # fake result
    data["stages"][1]["status"] = "succeeded"
    data["status"] = "succeeded"
    data["updated_at"] = now()
    data["result"] = ClassificationResult(
        face_detected=True,
        label="cat",
        confidence=0.98,
        image_url="https://cdn.example.com/some-thumb.jpg",
    ).model_dump()
    _persist(pred_id, data)


def _persist(pred_id: str, data: dict):
    predictions[pred_id]["data"] = data