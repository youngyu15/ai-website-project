from __future__ import annotations
from collections.abc import Mapping
from datetime import datetime
from enum import Enum
from typing import List, Literal
from uuid import UUID
from pydantic import BaseModel, Field, HttpUrl, field_validator
from common.schemas.base import ORMBase

Label = Literal["cat", "dog"]
StageName = Literal["face_detection", "classification"]

def _default_stage_dict(name: str) -> dict:
    return {"name": name, "status": "pending", "result": None}

def _ensure_default_stages(d: dict | None) -> dict:
    d = dict(d or {})
    d.setdefault("face_detection", _default_stage_dict("face_detection"))
    d.setdefault("classification", _default_stage_dict("classification"))
    # normalize inner dicts just in case
    for k in ("face_detection", "classification"):
        if not isinstance(d[k], dict):
            d[k] = _default_stage_dict(k)
        else:
            d[k].setdefault("name", k)
            d[k].setdefault("status", "pending")
            d[k].setdefault("result", None)
    return d

class PredictionStatus(str, Enum):
    pending = "pending"
    processing = "processing"
    succeeded = "succeeded"
    failed = "failed"

class Stage(BaseModel):
    name: StageName
    status: PredictionStatus
    result: dict | None = None

class Stages(BaseModel):
    face_detection: Stage
    classification: Stage

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
    stages: Stages
    result: ClassificationResult | None = None
    error: dict | None = None
    label: Label | None = None
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)

    @field_validator("stages", mode="before")
    @classmethod
    def _coerce_stages(cls, v):
        # Accept None, {}, or Mapping/MutableDict and turn into full dict for Stages
        if v is None:
            return _ensure_default_stages(None)
        if isinstance(v, Mapping):
            return _ensure_default_stages(dict(v))
        # If already a Stages-ish object, let pydantic handle it; otherwise fallback
        return _ensure_default_stages(v)

class PredictionPage(BaseModel):
    items: List[PredictionOut]
    next_cursor: str | None = None

class PublicPredictionOut(ORMBase):
    id: UUID
    status: PredictionStatus
    created_at: datetime
    stages: Stages
    result: ClassificationResult | None = None

    @field_validator("stages", mode="before")
    @classmethod
    def _coerce_stages(cls, v):
        # Accept None, {}, or Mapping/MutableDict and turn into full dict for Stages
        if v is None:
            return _ensure_default_stages(None)
        if isinstance(v, Mapping):
            return _ensure_default_stages(dict(v))
        # If already a Stages-ish object, let pydantic handle it; otherwise fallback
        return _ensure_default_stages(v)