from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid4
from typing import List

from sqlalchemy import Index, UniqueConstraint, Column, String, DateTime, func, text
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.dialects.postgresql import JSONB, ARRAY, UUID as PG_UUID
from sqlmodel import Field, Relationship, SQLModel

def utcnow() -> datetime:
    return datetime.now(timezone.utc)

# Enums
class PredictionStatus(str, Enum):
    pending = "pending"
    processing = "processing"
    succeeded = "succeeded"
    failed = "failed"

class StageName(str, Enum):
    face_detection = "face_detection"
    classification = "classification"

# Users & tokens
class User(SQLModel, table=True):
    __tablename__ = "users"
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    email: str = Field(index=True, unique=True)
    password_hash: str
    created_at: datetime = Field(
        default_factory=utcnow,
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), index=True))

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
    created_at: datetime = Field(
        default_factory=utcnow,
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), index=True))

    user: User | None = Relationship(back_populates="refresh_tokens")

# Uploads
class Upload(SQLModel, table=True):
    __tablename__ = "uploads"
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    owner_id: UUID = Field(foreign_key="users.id", index=True)
    content_type: str = Field(index=True)
    bytes: int
    storage_url: str
    created_at: datetime = Field(
        default_factory=utcnow,
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), index=True))

    owner: User | None = Relationship(back_populates="uploads")

    __table_args__ = (Index("ix_uploads_owner_created", "owner_id", "created_at"),)

# Predictions
class Prediction(SQLModel, table=True):
    __tablename__ = "predictions"
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    owner_id: UUID = Field(foreign_key="users.id", index=True)
    file_id: UUID = Field(foreign_key="uploads.id", index=True)

    status: PredictionStatus = Field(default=PredictionStatus.pending, index=True)

    stages: dict[str, dict] = Field(
        default_factory=dict,
        sa_column=Column(
            MutableDict.as_mutable(JSONB),
            nullable=False,
            server_default=text("'{}'::jsonb"),
        ),
    )
    result: dict | None = Field(default=None, sa_column=Column(JSONB))
    error: dict | None = Field(default=None, sa_column=Column(JSONB))

    label: str | None = Field(default=None, index=True)
    confidence: float | None = Field(default=None, index=True)

    created_at: datetime = Field(
        default_factory=utcnow,
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), index=True))
    updated_at: datetime = Field(
        default_factory=utcnow,
        sa_column=Column(DateTime(timezone=True), onupdate=func.now(), index=True))

    owner: User | None = Relationship(back_populates="predictions")
    upload: Upload | None = Relationship()

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
    expires_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), index=True))
    created_at: datetime = Field(
        default_factory=utcnow,
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), index=True))

# Webhooks (optional)
class Webhook(SQLModel, table=True):
    __tablename__ = "webhooks"
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    owner_id: UUID = Field(foreign_key="users.id", index=True)
    url: str
    secret_hash: str | None = None
    events: list[str] | None = Field(
        default_factory=lambda: ["prediction.succeeded", "prediction.failed"],
        sa_column=Column(ARRAY(String)))
    created_at: datetime = Field(
        default_factory=utcnow,
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), index=True))

    owner: User | None = Relationship(back_populates="webhooks")

class WebhookDelivery(SQLModel, table=True):
    __tablename__ = "webhook_deliveries"
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    webhook_id: UUID = Field(foreign_key="webhooks.id", index=True)
    prediction_id: UUID | None = Field(default=None, foreign_key="predictions.id", index=True)
    status: str = Field(default="pending", index=True)  # pending|delivered|failed
    attempts: int = 0
    last_error: str | None = None
    created_at: datetime = Field(
        default_factory=utcnow,
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), index=True))
    delivered_at: datetime | None = None

# Idempotency
class IdempotencyKey(SQLModel, table=True):
    __tablename__ = "idempotency_keys"
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id", index=True)
    key: str
    target_resource_type: str  # 'prediction' | 'upload'
    target_resource_id: UUID | None = None
    created_at: datetime = Field(
        default_factory=utcnow,
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), index=True))

    __table_args__ = (UniqueConstraint("user_id", "key", name="uq_idem_user_key"),)