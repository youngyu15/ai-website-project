# services/catdog-classifier/src/catdog_classifier/main.py
from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, Any, Tuple

from fastapi import FastAPI, File, UploadFile, HTTPException
from PIL import Image
import numpy as np
import io

import keras

# Resolve the default model **relative to this file**, not the CWD
_THIS_DIR = Path(__file__).resolve().parent

MODEL_PATH = Path(_THIS_DIR, os.getenv("CATDOG_MODEL_PATH", "models/model_v-03.h5"))
IMG_SIZE_ENV = os.getenv("IMG_SIZE")  # optional override, e.g. "128"

app = FastAPI(title="CatDog Classifier Service", version="1.2.0")

# --- Load model ------------------------------------------------------------
print("CWD:", os.getcwd())
print("Resolved model path:", MODEL_PATH)

if not (MODEL_PATH.suffix in {".h5", ".keras"} and MODEL_PATH.is_file()):
    # Helpful diagnostics if things go wrong
    maybe_models_dir = MODEL_PATH.parent
    nearby = []
    if maybe_models_dir.exists():
        nearby = [p.name for p in maybe_models_dir.iterdir()]
    raise RuntimeError(
        "Model file not found or wrong extension.\n"
        f"Expected: {MODEL_PATH}\n"
        f"Exists?  {MODEL_PATH.exists()}\n"
        f"Parent:  {maybe_models_dir}\n"
        f"Parent contents: {nearby}\n"
        "Tip: set CATDOG_MODEL_PATH to an absolute path, "
        "or place the model in src/catdog_classifier/models/."
    )

model = keras.models.load_model(str(MODEL_PATH), compile=False)

def infer_img_size() -> Tuple[int, int]:
    if IMG_SIZE_ENV:
        s = int(IMG_SIZE_ENV)
        return s, s
    ishape = model.inputs[0].shape  # e.g. (None, 128, 128, 3)
    H = int(ishape[1]) if ishape[1] is not None else 128
    W = int(ishape[2]) if ishape[2] is not None else 128
    return H, W

H, W = infer_img_size()

@app.get("/healthz")
def healthz():
    return {"ok": True, "model_path": str(MODEL_PATH), "img_size": [H, W]}

# --- Pre/post --------------------------------------------------------------
def _from_upload(upload: UploadFile) -> Image.Image:
    data = upload.file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Empty file")
    return Image.open(io.BytesIO(data))

def _preprocess(img: Image.Image) -> np.ndarray:
    img = img.convert("RGB").resize((W, H))
    arr = np.asarray(img, dtype=np.float32) / 255.0
    return np.expand_dims(arr, 0)  # [1, H, W, 3]

# --- Predict ---------------------------------------------------------------
@app.post("/v1/predict")
def predict(file: UploadFile = File(...)) -> Dict[str, Any]:
    x = _preprocess(_from_upload(file))
    y = model.predict(x, verbose=0)

    # handle binary heads: sigmoid [1,1] or softmax [1,2]
    if y.ndim == 2 and y.shape[1] == 1:
        score_dog = float(y[0, 0])          # assume 1.0==dog
        score_cat = 1.0 - score_dog
    elif y.ndim == 2 and y.shape[1] == 2:
        score_cat = float(y[0, 0])
        score_dog = float(y[0, 1])
    else:
        raise HTTPException(status_code=500, detail=f"Unexpected output shape: {y.shape}")

    label = "dog" if score_dog >= score_cat else "cat"
    score = max(score_dog, score_cat)
    return {"label": label, "score": score, "raw": [score_cat, score_dog]}
