from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from packages.common.src.common.http.clients import detect_faces_from_bytes, classify_catdog_from_bytes
from api.repositories import predictions_repo, uploads_repo  # your repository helpers
from api.services.storage import get_object_bytes
from api.services.uploads_service import object_key_for
import api.settings
from api.settings import settings

async def run_ml_pipeline(db: AsyncSession, *, pred_id: UUID) -> None:
    """
    Orchestrates: fetch file -> face detection -> (if any face) cat/dog classification.
    Updates DB after each stage.
    """
    pred = await predictions_repo.get_prediction(db, pred_id=pred_id)
    if not pred:
        return
    
    await predictions_repo.mark_processing(db, pred)
    await predictions_repo.update_stage(db, pred, name="face_detection", status="processing")

    up = await uploads_repo.get_upload(db, upload_id=pred.file_id, owner_id=pred.owner_id)
    if not up:
        await predictions_repo.update_stage(db, pred, name="face_detection", status="failed")
        error = {"error": "upload not found"}
        await predictions_repo.mark_failed(db=db, pred=pred, error=error)
        return

    object_key = getattr(up, "object_key", None) or object_key_for(pred.file_id, getattr(up, "content_type", "image/jpeg"))

    if api.settings.DEBUG == "true":
        file_uri = up.storage_url
    else:
        file_uri = f"s3://{settings.s3_bucket}/{object_key}"

    try:
        img_bytes = await get_object_bytes(file_uri)
    except Exception as e:
        await predictions_repo.update_stage(db, pred, name="face_detection", status="failed")
        error = {"error": f"Failed to read input bytes: {e}"}
        await predictions_repo.mark_failed(db=db, pred=pred, error=error)
        return
    
    try:
        fd = await detect_faces_from_bytes(img_bytes, filename=str(pred.file_id))
        faces = (fd or {}).get("faces", [])
        await predictions_repo.update_stage(db, pred, name="face_detection", status="succeeded", result={"faces": faces})
    except Exception as e:
        await predictions_repo.update_stage(db, pred, name="face_detection", status="failed")
        error = {"face_detection": str(e)}
        await predictions_repo.mark_failed(db=db, pred=pred, error=error)
        return
    
    if not faces:
        await predictions_repo.update_stage(db, pred, name="face_detection", status="succeeded", result={"skipped": True, "reason": "no_face"})
        result = {"face_detected": False, "label": None, "confidence": None, "faces": []}
        await predictions_repo.mark_succeeded(db=db, pred=pred, result=result)
        return
    
    await predictions_repo.update_stage(db, pred, name="classification", status="processing")
    try:
        cls = await classify_catdog_from_bytes(img_bytes, filename=str(pred.file_id))
        label = cls.get("label"); score = cls.get("score")
        await predictions_repo.update_stage(
            db, pred, name="classification", status="succeeded",
            result={"label": label, "confidence": score}
        )
        result = {"face_detected": True, "label": label, "confidence": score, "faces": faces, "raw": cls.get("raw")}
        await predictions_repo.mark_succeeded(db=db, pred=pred, result=result)
    except Exception as e:
        result = {"face_detected": True, "label": None, "confidence": None, "faces": faces}
        error = {"classification": str(e)}
        await predictions_repo.update_stage(db, pred, name="classification", status="failed", result=result)
        await predictions_repo.mark_failed(db=db, pred=pred, error=error)

    # pred = await predictions_repo.get_prediction(db, pred_id=pred_id)
    # if not pred:
    #     return

    # # Start
    # stages = [
    #     {"name": "face_detection", "status": "processing", "result": None},
    #     {"name": "classification", "status": "pending", "result": None},
    # ]
    # await _mark(db, pred, status=STATUS_PROCESSING, stages=stages)

    # # Load the image bytes (from S3 or disk via your storage layer)
    # # Assumes pred.file_uri or similar points to your object. Adjust as needed.
    # file_uri = getattr(pred, "file_uri", None) or getattr(pred, "input_uri", None)
    # if not file_uri:
    #     await _mark(
    #         db,
    #         pred,
    #         status=STATUS_FAILED,
    #         stages=[
    #             {"name": "face_detection", "status": "skipped", "result": None},
    #             {"name": "classification", "status": "skipped", "result": None},
    #         ],
    #         result={"error": "No input file_uri on prediction"},
    #     )
    #     return

    # try:
    #     img_bytes = await get_object_bytes(file_uri)
    # except Exception as e:
    #     await _mark(
    #         db,
    #         pred,
    #         status=STATUS_FAILED,
    #         result={"error": f"Failed to read input bytes: {e}"},
    #         stages=[
    #             {"name": "face_detection", "status": "failed", "result": {"error": str(e)}},
    #             {"name": "classification", "status": "skipped", "result": None},
    #         ],
    #     )
    #     return

    # # ---- 1) Face detection
    # try:
    #     face_res = await detect_faces_from_bytes(img_bytes, filename=file_uri.split("/")[-1])
    #     faces = (face_res or {}).get("faces", [])
    #     face_detected = bool(faces)
    #     stages[0] = {"name": "face_detection", "status": "succeeded", "result": {"faces": faces}}
    #     stages[1] = {"name": "classification", "status": "processing" if face_detected else "skipped", "result": None}
    #     await _mark(db, pred, stages=stages)
    # except Exception as e:
    #     stages[0] = {"name": "face_detection", "status": "failed", "result": {"error": str(e)}}
    #     stages[1] = {"name": "classification", "status": "skipped", "result": None}
    #     await _mark(
    #         db, pred, status=STATUS_FAILED, stages=stages,
    #         result={"face_detection_error": str(e)}
    #     )
    #     return

    # # If no face, complete with a clear result
    # if not face_detected:
    #     final = {
    #         "face_detected": False,
    #         "label": None,
    #         "confidence": None,
    #         "image_url": None,
    #         "faces": faces,
    #     }
    #     await _mark(db, pred, status=STATUS_SUCCEEDED, stages=stages, result=final, label=None, confidence=None)
    #     return

    # # ---- 2) Cat/Dog classification
    # try:
    #     cls = await classify_catdog_from_bytes(img_bytes, filename=file_uri.split("/")[-1])
    #     label = cls.get("label")
    #     score = cls.get("score")
    #     stages[1] = {"name": "classification", "status": "succeeded", "result": {"label": label, "confidence": score}}

    #     final = {
    #         "face_detected": True,
    #         "label": label,
    #         "confidence": score,
    #         "image_url": None,    # populate if you serve the uploaded image publicly
    #         "faces": faces,
    #         "raw": cls.get("raw"),
    #     }
    #     await _mark(db, pred, status=STATUS_SUCCEEDED, stages=stages, result=final, label=label, confidence=score)

    # except Exception as e:
    #     stages[1] = {"name": "classification", "status": "failed", "result": {"error": str(e)}}
    #     # Result still includes face info; classification failed
    #     partial = {
    #         "face_detected": True,
    #         "label": None,
    #         "confidence": None,
    #         "image_url": None,
    #         "faces": faces,
    #         "error": {"classification": str(e)},
    #     }
    #     await _mark(db, pred, status=STATUS_FAILED, stages=stages, result=partial)
