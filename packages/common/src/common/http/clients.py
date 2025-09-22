import os
import httpx
from typing import Any, Dict

FACE_URL = os.getenv("FACE_SERVICE_URL", "http://face-detection:8000")
CATDOG_URL = os.getenv("CATDOG_SERVICE_URL", "http://catdog-classifier:8001")

async def detect_faces_from_bytes(img_bytes: bytes, filename: str = "image.jpg") -> Dict[str, Any]:
    async with httpx.AsyncClient(timeout=30.0) as client:
        files = {"file": (filename, img_bytes, "image/jpeg")}
        r = await client.post(f"{FACE_URL}/v1/face/detect", files=files)
        r.raise_for_status()
        return r.json()

async def classify_catdog_from_bytes(img_bytes: bytes, filename: str = "image.jpg") -> Dict[str, Any]:
    async with httpx.AsyncClient(timeout=30.0) as client:
        files = {"file": (filename, img_bytes, "image/jpeg")}
        r = await client.post(f"{CATDOG_URL}/v1/predict", files=files)
        r.raise_for_status()
        return r.json()
