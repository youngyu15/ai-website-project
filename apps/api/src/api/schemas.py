from __future__ import annotations
from datetime import datetime
from typing import List, Literal, Optional
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field, HttpUrl
from packages.common.src.common.schemas.base import ORMBase

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

# Shares
class CreateShareRequest(BaseModel):
    ttl_seconds: Optional[int] = Field(default=86400, ge=60, le=604800)

class ShareOut(ORMBase):
    share_id: str = Field(alias="public_id")
    url: HttpUrl
    expires_at: datetime

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