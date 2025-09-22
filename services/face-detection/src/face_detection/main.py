from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from typing import List, Dict, Any
from PIL import Image
import numpy as np
import io
import mediapipe as mp

app = FastAPI(title="Face Detection Service", version="1.0.0")

mp_face = mp.solutions.face_detection
# model_selection: 0 = short-range (best for faces within ~2m), 1 = full-range
detector = mp_face.FaceDetection(model_selection=0, min_detection_confidence=0.5)

@app.get("/health")
def health():
    return {"ok": True}

def _np_from_upload(upload: UploadFile) -> np.ndarray:
    data = upload.file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Empty file")
    img = Image.open(io.BytesIO(data)).convert("RGB")
    return np.array(img)

@app.post("/v1/face/detect")
def detect_faces(file: UploadFile = File(...)) -> Dict[str, Any]:
    """
    Returns face boxes in normalized xywh, plus score. For multiple faces.
    """
    arr = _np_from_upload(file)
    # MediaPipe expects RGB ndarray
    results = detector.process(arr)
    items: List[Dict[str, Any]] = []
    if results.detections:
        h, w = arr.shape[:2]
        for det in results.detections:
            loc = det.location_data
            # relative_bounding_box: xmin, ymin, width, height in [0..1]
            rbb = loc.relative_bounding_box
            items.append({
                "score": float(det.score[0]) if det.score else None,
                "box": {
                    "x": float(rbb.xmin),
                    "y": float(rbb.ymin),
                    "w": float(rbb.width),
                    "h": float(rbb.height),
                }
            })
    return {"faces": items}
