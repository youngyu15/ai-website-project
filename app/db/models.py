# app/db/models.py
from __future__ import annotations

from datetime import datetime, timedelta
from enum import Enum
from typing import List, Optional
from uuid import UUID, uuid4

from sqlalchemy import Column, Index, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB, ARRAY
from sqlmodel import Field, Relationship, SQLModel


# ---------- Enums ----------
class PredictionStatus(str, Enum):
    pending = "pending"
    processing = "processing"
    succeeded = "succeeded"
    failed = "failed"


# ---------- Base mixins ----------
class Timestamped(SQLModel):
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False, index=True)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False, index=True)


# ---------- User & Auth ----------
class User(SQLModel, table=True):
    __tablename__ = "users"
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    email: str = Field(sa_column=Column(String(320), unique=True, index=True, nullable=False))
    password_hash: str = Field(sa_column=Column(String(255), nullable=False))
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False, index=True)

    # relationships
    uploads: List["Upload"] = Relationship(back_populates="owner")
    predictions: List["Prediction"] = Relationship(back_populates="owner")
    refresh_tokens: List["RefreshToken"] = Relationship(back_populates="user")
    webhooks: List["Webhook"] = Relationship(back_populates="owner")


class RefreshToken(SQLModel, table=True):
    """
    Store hashed refresh tokens (never store raw token). Revoke by setting revoked=True.
    """
    __tablename__ = "refresh_tokens"
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id", nullable=False, index=True)
    token_hash: str = Field(sa_column=Column(String(255), nullable=False, unique=True))  # hash of token
    expires_at: datetime = Field(nullable=False, index=True)
    revoked: bool = Field(default=False, nullable=False, index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False, index=True)

    user: Optional[User] = Relationship(back_populates="refresh_tokens")


# ---------- Storage / Uploads ----------
class Upload(SQLModel, table=True):
    """
    Metadata for a user upload stored in object storage (e.g., S3/GCS).
    """
    __tablename__ = "uploads"
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    owner_id: UUID = Field(foreign_key="users.id", nullable=False, index=True)
    content_type: str = Field(sa_column=Column(String(100), nullable=False, index=True))
    bytes: int = Field(nullable=False)
    storage_url: str = Field(sa_column=Column(String(2048), nullable=False))  # e.g., s3://bucket/key or https URL
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False, index=True)

    owner: Optional[User] = Relationship(back_populates="uploads")

    __table_args__ = (
        Index("ix_uploads_owner_created", "owner_id", "created_at"),
    )


# ---------- Predictions (async job) ----------
class Prediction(SQLModel, table=True):
    """
    Async classification job. 'stages', 'result', and 'error' are JSONB blobs.
    Keep a denormalized 'label' and 'confidence' for fast filtering/sorting.
    """
    __tablename__ = "predictions"
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    owner_id: UUID = Field(foreign_key="users.id", nullable=False, index=True)
    file_id: UUID = Field(foreign_key="uploads.id", nullable=False, index=True)

    status: PredictionStatus = Field(default=PredictionStatus.pending, nullable=False, index=True)

    # JSON fields (Postgres JSONB)
    stages: Optional[dict] = Field(default=None, sa_column=Column(JSONB, nullable=True))
    result: Optional[dict] = Field(default=None, sa_column=Column(JSONB, nullable=True))
    error: Optional[dict] = Field(default=None, sa_column=Column(JSONB, nullable=True))

    # denormalized for filtering
    label: Optional[str] = Field(default=None, index=True)       # "cat" | "dog"
    confidence: Optional[float] = Field(default=None, index=True)

    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False, index=True)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False, index=True)

    owner: Optional[User] = Relationship(back_populates="predictions")
    upload: Optional[Upload] = Relationship()

    __table_args__ = (
        Index("ix_predictions_owner_created", "owner_id", "created_at"),
        Index("ix_predictions_label_conf", "label", "confidence"),
    )


# ---------- Public Shares ----------
class Share(SQLModel, table=True):
    """
    Public, unauthenticated handle to a prediction.
    public_id is what you expose in the URL (think 'shr_xxx'); it's unique and revocable.
    """
    __tablename__ = "shares"
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    prediction_id: UUID = Field(foreign_key="predictions.id", nullable=False, index=True)
    public_id: str = Field(sa_column=Column(String(80), unique=True, nullable=False, index=True))
    expires_at: datetime = Field(nullable=False, index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False, index=True)

    prediction: Optional[Prediction] = Relationship()

    __table_args__ = (
        Index("ix_shares_pred_expires", "prediction_id", "expires_at"),
    )


# ---------- Webhooks ----------
class Webhook(SQLModel, table=True):
    """
    User-registered webhook endpoints to receive job status notifications.
    """
    __tablename__ = "webhooks"
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    owner_id: UUID = Field(foreign_key="users.id", nullable=False, index=True)
    url: str = Field(sa_column=Column(String(2048), nullable=False))
    secret_hash: Optional[str] = Field(default=None, sa_column=Column(String(255), nullable=True))  # store hash, not raw
    events: List[str] = Field(default_factory=lambda: ["prediction.succeeded", "prediction.failed"],
                              sa_column=Column(ARRAY(String)))
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False, index=True)

    owner: Optional[User] = Relationship(back_populates="webhooks")

    __table_args__ = (
        Index("ix_webhooks_owner_created", "owner_id", "created_at"),
    )


class WebhookDelivery(SQLModel, table=True):
    """
    Delivery log for webhook posts (for retries/observability).
    """
    __tablename__ = "webhook_deliveries"
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    webhook_id: UUID = Field(foreign_key="webhooks.id", nullable=False, index=True)
    prediction_id: Optional[UUID] = Field(default=None, foreign_key="predictions.id", index=True)
    status: str = Field(default="pending", index=True)   # pending|delivered|failed
    attempts: int = Field(default=0, nullable=False)
    last_error: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False, index=True)
    delivered_at: Optional[datetime] = Field(default=None, index=True)


# ---------- Idempotency ----------
class IdempotencyKey(SQLModel, table=True):
    """
    Ensures POST retries don't create duplicates.
    Enforce uniqueness per (user_id, key).
    """
    __tablename__ = "idempotency_keys"
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id", nullable=False, index=True)
    key: str = Field(sa_column=Column(String(120), nullable=False))
    target_resource_type: str = Field(sa_column=Column(String(50), nullable=False))  # e.g., 'prediction' or 'upload'
    target_resource_id: Optional[UUID] = Field(default=None, sa_column=Column(PG_UUID(as_uuid=True), nullable=True))
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False, index=True)

    __table_args__ = (
        UniqueConstraint("user_id", "key", name="uq_idem_user_key"),
    )
