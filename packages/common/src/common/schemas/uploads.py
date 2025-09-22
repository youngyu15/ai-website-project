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