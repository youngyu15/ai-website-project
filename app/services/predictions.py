import asyncio
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.db import repo  # your repository helpers
from app.clients.ml_services import detect_faces_from_bytes, classify_catdog_from_bytes
from app.services.storage import get_object_bytes  # you already have S3 helper that returns bytes

# If you have an enum for status, adapt these to your enum names.
STATUS_QUEUED = "queued"
STATUS_PROCESSING = "processing"
STATUS_SUCCEEDED = "succeeded"
STATUS_FAILED = "failed"

def _now():
    return datetime.now(timezone.utc)

async def _mark(
    db: AsyncSession,
    pred,
    *,
    status: Optional[str] = None,
    stages: Optional[list] = None,
    result: Optional[Dict[str, Any]] = None,
    label: Optional[str] = None,
    confidence: Optional[float] = None,
):
    if status is not None:
        pred.status = status
    if stages is not None:
        pred.stages = stages
    if result is not None:
        pred.result = result
    if label is not None:
        pred.label = label
    if confidence is not None:
        pred.confidence = confidence
    pred.updated_at = _now()
    await db.commit()
    await db.refresh(pred)
    return pred

async def run_ml_pipeline(db: AsyncSession, *, pred_id: UUID) -> None:
    """
    Orchestrates: fetch file -> face detection -> (if any face) cat/dog classification.
    Updates DB after each stage.
    """
    pred = await repo.get_prediction(db, pred_id=pred_id)
    if not pred:
        return

    # Start
    stages = [
        {"name": "face_detection", "status": "processing", "result": None},
        {"name": "classification", "status": "pending", "result": None},
    ]
    await _mark(db, pred, status=STATUS_PROCESSING, stages=stages)

    # Load the image bytes (from S3 or disk via your storage layer)
    # Assumes pred.file_uri or similar points to your object. Adjust as needed.
    file_uri = getattr(pred, "file_uri", None) or getattr(pred, "input_uri", None)
    if not file_uri:
        await _mark(
            db,
            pred,
            status=STATUS_FAILED,
            stages=[
                {"name": "face_detection", "status": "skipped", "result": None},
                {"name": "classification", "status": "skipped", "result": None},
            ],
            result={"error": "No input file_uri on prediction"},
        )
        return

    try:
        img_bytes = await get_object_bytes(file_uri)
    except Exception as e:
        await _mark(
            db,
            pred,
            status=STATUS_FAILED,
            result={"error": f"Failed to read input bytes: {e}"},
            stages=[
                {"name": "face_detection", "status": "failed", "result": {"error": str(e)}},
                {"name": "classification", "status": "skipped", "result": None},
            ],
        )
        return

    # ---- 1) Face detection
    try:
        face_res = await detect_faces_from_bytes(img_bytes, filename=file_uri.split("/")[-1])
        faces = (face_res or {}).get("faces", [])
        face_detected = bool(faces)
        stages[0] = {"name": "face_detection", "status": "succeeded", "result": {"faces": faces}}
        stages[1] = {"name": "classification", "status": "processing" if face_detected else "skipped", "result": None}
        await _mark(db, pred, stages=stages)
    except Exception as e:
        stages[0] = {"name": "face_detection", "status": "failed", "result": {"error": str(e)}}
        stages[1] = {"name": "classification", "status": "skipped", "result": None}
        await _mark(
            db, pred, status=STATUS_FAILED, stages=stages,
            result={"face_detection_error": str(e)}
        )
        return

    # If no face, complete with a clear result
    if not face_detected:
        final = {
            "face_detected": False,
            "label": None,
            "confidence": None,
            "image_url": None,
            "faces": faces,
        }
        await _mark(db, pred, status=STATUS_SUCCEEDED, stages=stages, result=final, label=None, confidence=None)
        return

    # ---- 2) Cat/Dog classification
    try:
        cls = await classify_catdog_from_bytes(img_bytes, filename=file_uri.split("/")[-1])
        label = cls.get("label")
        score = cls.get("score")
        stages[1] = {"name": "classification", "status": "succeeded", "result": {"label": label, "confidence": score}}

        final = {
            "face_detected": True,
            "label": label,
            "confidence": score,
            "image_url": None,    # populate if you serve the uploaded image publicly
            "faces": faces,
            "raw": cls.get("raw"),
        }
        await _mark(db, pred, status=STATUS_SUCCEEDED, stages=stages, result=final, label=label, confidence=score)

    except Exception as e:
        stages[1] = {"name": "classification", "status": "failed", "result": {"error": str(e)}}
        # Result still includes face info; classification failed
        partial = {
            "face_detected": True,
            "label": None,
            "confidence": None,
            "image_url": None,
            "faces": faces,
            "error": {"classification": str(e)},
        }
        await _mark(db, pred, status=STATUS_FAILED, stages=stages, result=partial)
