from __future__ import annotations
from datetime import datetime
from typing import Literal
from uuid import UUID
from pydantic import BaseModel, Field, HttpUrl
from common.schemas.predictions import ORMBase

class CreateUploadRequest(BaseModel):
    content_type: Literal["image/jpeg", "image/png"]
    file_bytes: int = Field(ge=1)

class UploadCreated(BaseModel):
    file_id: UUID
    upload_url: str
    content_type: str
    max_bytes: int
    expires_at: datetime

class UploadOut(ORMBase):
    file_id: UUID = Field(alias="id")
    owner_id: UUID
    content_type: str
    bytes: int
    storage_url: str
    created_at: datetime