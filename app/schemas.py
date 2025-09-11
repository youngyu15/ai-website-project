# app/schemas.py (Pydantic models)
from pydantic import BaseModel, EmailStr, HttpUrl, Field
from typing import Optional, List, Literal
from datetime import datetime

class ORMBase(BaseModel):
    model_config = {"from_attributes": True}

class AuthResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: Literal["Bearer"] = "Bearer"
    expires_in: int = 3600

class SignupRequest(BaseModel):
    email: EmailStr
    password: str

class LoginRequest(SignupRequest):
    pass

class RefreshRequest(BaseModel):
    refresh_token: str

class UserBase(BaseModel):
    id: str
    email: EmailStr
    created_at: datetime

class CreateUploadRequest(BaseModel):
    content_type: str
    file_bytes: int

class UploadCreated(BaseModel):
    file_id: str
    upload_url: HttpUrl
    content_type: str
    max_bytes: int
    expires_at: datetime

class UploadBase(BaseModel):
    file_id: str
    owner_id: str
    content_type: str
    bytes: int
    created_at: datetime
    storage_url: HttpUrl

class Stage(BaseModel):
    name: Literal["face_detection", "classification"]
    status: Literal["pending", "processing", "succeeded", "failed"]
    result: Optional[dict] = None

class ClassificationResult(BaseModel):
    face_detected: bool
    label: Literal["cat", "dog"]
    confidence: float = Field(ge=0, le=1)
    image_url: Optional[HttpUrl]

class PredictionBase(BaseModel):
    id: str
    status: Literal["pending", "processing", "succeeded", "failed"]
    created_at: datetime
    updated_at: datetime
    file_id: str
    stages: List[Stage]
    result: Optional[ClassificationResult] = None
    error: Optional[dict] = None

class PredictionPage(BaseModel):
    items: List[PredictionBase]
    next_cursor: Optional[str]

class CreatePredictionRequest(BaseModel):
    file_id: str
    idempotency_key: Optional[str]

class CreateShareRequest(BaseModel):
    ttl_seconds: Optional[int] = 86400

class ShareBase(BaseModel):
    share_id: str
    url: HttpUrl
    expires_at: datetime

class WebhookCreateRequest(BaseModel):
    url: HttpUrl
    secret: Optional[str]
    events: List[str] = ["prediction.succeeded", "prediction.failed"]

class WebhookBase(BaseModel):
    id: str
    url: HttpUrl
    events: List[str]
    created_at: datetime