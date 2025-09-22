from __future__ import annotations
from datetime import datetime
from typing import List, Literal, Optional
from uuid import UUID
from pydantic import BaseModel, Field, HttpUrl
from common.schemas.base import ORMBase

PredictionStatus = Literal["pending", "processing", "succeeded", "failed"]
Label = Literal["cat", "dog"]

class Stage(BaseModel):
    name: Literal["face_detection", "classification"]
    status: PredictionStatus
    result: Optional[dict] = None

class ClassificationResult(BaseModel):
    face_detected: bool
    label: Label
    confidence: float = Field(ge=0.0, le=1.0)
    image_url: Optional[HttpUrl] = None

class CreatePredictionRequest(BaseModel):
    file_id: UUID
    idempotency_key: Optional[str] = None

class PredictionOut(ORMBase):
    id: UUID
    status: PredictionStatus
    created_at: datetime
    updated_at: datetime
    file_id: UUID
    stages: Optional[List[Stage]] = None
    result: Optional[ClassificationResult] = None
    error: Optional[dict] = None
    label: Optional[Label] = None
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)

class PredictionPage(BaseModel):
    items: List[PredictionOut]
    next_cursor: Optional[str] = None

class PublicPredictionOut(PredictionOut):
    pass