# app/core/config.py
from pydantic import BaseModel, field_validator
from typing import List
import os

class Settings(BaseModel):
    app_name: str = os.getenv("APP_NAME", "AI Website API")
    app_env: str = os.getenv("APP_ENV", "dev")

    secret_key: str = os.getenv("SECRET_KEY", "change-me")
    access_token_expire_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "15"))
    refresh_token_expire_days: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

    cors_origins: List[str] = []

    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://postgres:postgres@localhost:5432/ai_website",
    )

    # S3
    s3_bucket: str = os.getenv("S3_BUCKET", "your-bucket")
    aws_region: str = os.getenv("AWS_REGION", "us-east-1")
    s3_endpoint_url: str | None = os.getenv("S3_ENDPOINT_URL")

    max_upload_bytes: int = int(os.getenv("MAX_UPLOAD_BYTES", str(10 * 1024 * 1024)))

    webhook_signature_header: str = os.getenv(
        "WEBHOOK_SIGNATURE_HEADER", "X-Webhook-Signature"
    )

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors(cls, v):
        if not v:
            v = os.getenv("CORS_ORIGINS", "")
        if isinstance(v, str):
            return [i.strip() for i in v.split(",") if i.strip()]
        return v

settings = Settings()