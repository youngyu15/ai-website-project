# services/catdog-service/app/main.py
import os
from typing import Dict, Any, Tuple
from fastapi import FastAPI, File, UploadFile, HTTPException
from PIL import Image
import numpy as np
import io
import tensorflow as tf
from tensorflow import keras

MODEL_PATH = os.getenv("MODEL_PATH", "/models/model.h5")
IMG_SIZE_ENV = os.getenv("IMG_SIZE")  # optional override, e.g. "128"

app = FastAPI(title="CatDog Classifier Service", version="1.2.0")

# --- Load H5 ---------------------------------------------------------------
if not (os.path.isfile(MODEL_PATH) and MODEL_PATH.endswith((".h5", ".keras"))):
    raise RuntimeError(
        f"MODEL_PATH must be an .h5/.keras file. Got: {MODEL_PATH}"
    )

model = keras.models.load_model(MODEL_PATH, compile=False)

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
    return {"ok": True, "model_path": MODEL_PATH, "img_size": [H, W]}

# --- Pre/post --------------------------------------------------------------
def _from_upload(upload: UploadFile) -> Image.Image:
    data = upload.file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Empty file")
    return Image.open(io.BytesIO(data))

def _preprocess(img: Image.Image) -> np.ndarray:
    img = img.convert("RGB").resize((W, H))
    arr = np.asarray(img).astype("float32") / 255.0
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
