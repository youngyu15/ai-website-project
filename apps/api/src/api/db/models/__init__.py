from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional
from uuid import UUID, uuid4

from sqlalchemy import Index, UniqueConstraint, Column, String
from sqlalchemy.dialects.postgresql import JSONB, ARRAY
from sqlmodel import Field, Relationship, SQLModel

def utcnow() -> datetime:
    return datetime.now(timezone.utc)

# Enums
class PredictionStatus(str, Enum):
    pending = "pending"
    processing = "processing"
    succeeded = "succeeded"
    failed = "failed"

# Users & tokens
class User(SQLModel, table=True):
    __tablename__ = "users"
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    email: str = Field(index=True, unique=True)
    password_hash: str
    created_at: datetime = Field(default_factory=utcnow, index=True)

    uploads: List["Upload"] = Relationship(back_populates="owner")
    predictions: List["Prediction"] = Relationship(back_populates="owner")
    refresh_tokens: List["RefreshToken"] = Relationship(back_populates="user")
    webhooks: List["Webhook"] = Relationship(back_populates="owner")

class RefreshToken(SQLModel, table=True):
    __tablename__ = "refresh_tokens"
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id", index=True)
    token_hash: str = Field(unique=True)
    expires_at: datetime = Field(index=True)
    revoked: bool = Field(default=False, index=True)
    created_at: datetime = Field(default_factory=utcnow, index=True)

    user: Optional[User] = Relationship(back_populates="refresh_tokens")

# Uploads
class Upload(SQLModel, table=True):
    __tablename__ = "uploads"
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    owner_id: UUID = Field(foreign_key="users.id", index=True)
    content_type: str = Field(index=True)
    bytes: int
    storage_url: str
    created_at: datetime = Field(default_factory=utcnow, index=True)

    owner: Optional[User] = Relationship(back_populates="uploads")

    __table_args__ = (Index("ix_uploads_owner_created", "owner_id", "created_at"),)

# Predictions
class Prediction(SQLModel, table=True):
    __tablename__ = "predictions"
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    owner_id: UUID = Field(foreign_key="users.id", index=True)
    file_id: UUID = Field(foreign_key="uploads.id", index=True)

    status: PredictionStatus = Field(default=PredictionStatus.pending, index=True)

    stages: Optional[dict] = Field(default=None, sa_column=Column(JSONB))
    result: Optional[dict] = Field(default=None, sa_column=Column(JSONB))
    error: Optional[dict] = Field(default=None, sa_column=Column(JSONB))

    label: Optional[str] = Field(default=None, index=True)
    confidence: Optional[float] = Field(default=None, index=True)

    created_at: datetime = Field(default_factory=utcnow, index=True)
    updated_at: datetime = Field(default_factory=utcnow, index=True)

    owner: Optional[User] = Relationship(back_populates="predictions")
    upload: Optional[Upload] = Relationship()

    __table_args__ = (
        Index("ix_predictions_owner_created", "owner_id", "created_at"),
        Index("ix_predictions_label_conf", "label", "confidence"),
    )

# Shares
class Share(SQLModel, table=True):
    __tablename__ = "shares"
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    prediction_id: UUID = Field(foreign_key="predictions.id", index=True)
    public_id: str = Field(unique=True, index=True)
    expires_at: datetime = Field(index=True)
    created_at: datetime = Field(default_factory=utcnow, index=True)

# Webhooks (optional)
class Webhook(SQLModel, table=True):
    __tablename__ = "webhooks"
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    owner_id: UUID = Field(foreign_key="users.id", index=True)
    url: str
    secret_hash: Optional[str] = None
    events: Optional[list[str]] = Field(
        default_factory=lambda: ["prediction.succeeded", "prediction.failed"],
        sa_column=Column(ARRAY(String)))
    created_at: datetime = Field(default_factory=utcnow, index=True)

    owner: Optional[User] = Relationship(back_populates="webhooks")

class WebhookDelivery(SQLModel, table=True):
    __tablename__ = "webhook_deliveries"
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    webhook_id: UUID = Field(foreign_key="webhooks.id", index=True)
    prediction_id: Optional[UUID] = Field(default=None, foreign_key="predictions.id", index=True)
    status: str = Field(default="pending", index=True)  # pending|delivered|failed
    attempts: int = 0
    last_error: Optional[str] = None
    created_at: datetime = Field(default_factory=utcnow, index=True)
    delivered_at: Optional[datetime] = None

# Idempotency
class IdempotencyKey(SQLModel, table=True):
    __tablename__ = "idempotency_keys"
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id", index=True)
    key: str
    target_resource_type: str  # 'prediction' | 'upload'
    target_resource_id: Optional[UUID] = None
    created_at: datetime = Field(default_factory=utcnow, index=True)

    __table_args__ = (UniqueConstraint("user_id", "key", name="uq_idem_user_key"),)