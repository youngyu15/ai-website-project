from __future__ import annotations
from datetime import datetime
from enum import Enum
from typing import List, Literal
from uuid import UUID
from pydantic import BaseModel, Field, HttpUrl
from common.schemas.base import ORMBase

Label = Literal["cat", "dog"]

class PredictionStatus(str, Enum):
    pending = "pending"
    processing = "processing"
    succeeded = "succeeded"
    failed = "failed"

class Stage(BaseModel):
    name: Literal["face_detection", "classification"]
    status: PredictionStatus
    result: dict | None = None

class ClassificationResult(BaseModel):
    face_detected: bool
    label: Label
    confidence: float = Field(ge=0.0, le=1.0)
    image_url: HttpUrl | None = None

class CreatePredictionRequest(BaseModel):
    file_id: UUID
    idempotency_key: str | None = None

class PredictionOut(ORMBase):
    id: UUID
    status: PredictionStatus
    created_at: datetime
    updated_at: datetime
    file_id: UUID
    stages: List[Stage] | None = None
    result: ClassificationResult | None = None
    error: dict | None = None
    label: Label | None = None
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)

class PredictionPage(BaseModel):
    items: List[PredictionOut]
    next_cursor: str | None = None

class PublicPredictionOut(PredictionOut):
    pass