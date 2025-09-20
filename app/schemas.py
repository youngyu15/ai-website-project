from __future__ import annotations
from datetime import datetime
from typing import List, Literal, Optional
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field, HttpUrl

class ORMBase(BaseModel):
    model_config = {"from_attributes": True}

# Auth
class SignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)

class LoginRequest(SignupRequest):
    pass

class RefreshRequest(BaseModel):
    refresh_token: str

class AuthResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: Literal["Bearer"] = "Bearer"
    expires_in: int = 900

# Users
class UserOut(ORMBase):
    id: UUID
    email: EmailStr
    created_at: datetime

# Uploads
class CreateUploadRequest(BaseModel):
    content_type: Literal["image/jpeg", "image/png"]
    file_bytes: int = Field(ge=1)

class UploadCreated(BaseModel):
    file_id: UUID
    upload_url: HttpUrl
    content_type: str
    max_bytes: int
    expires_at: datetime

class UploadOut(ORMBase):
    id: UUID = Field(alias="file_id")
    owner_id: UUID
    content_type: str
    bytes: int
    storage_url: HttpUrl
    created_at: datetime

# Predictions
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

# Shares
class CreateShareRequest(BaseModel):
    ttl_seconds: Optional[int] = Field(default=86400, ge=60, le=604800)

class ShareOut(ORMBase):
    share_id: str = Field(alias="public_id")
    url: HttpUrl
    expires_at: datetime

class PublicPredictionOut(PredictionOut):
    pass

# Webhooks
class WebhookCreateRequest(BaseModel):
    url: HttpUrl
    secret: Optional[str] = None
    events: List[Literal["prediction.succeeded", "prediction.failed"]] = [
        "prediction.succeeded", "prediction.failed"
    ]

class WebhookOut(ORMBase):
    id: UUID
    url: HttpUrl
    events: List[str]
    created_at: datetime

# Errors
class APIError(BaseModel):
    code: str
    message: str

class ErrorResponse(BaseModel):
    error: APIError
    request_id: str