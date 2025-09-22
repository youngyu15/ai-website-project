from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, SecretStr, model_validator
from typing import List, Literal
import json

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False, extra="ignore")

    # Non-secret with safe defaults
    app_name: str = "AI Website API"
    app_env: Literal["dev","staging","prod"] = "dev"

    # REQUIRED secrets (no defaults)
    secret_key: SecretStr = Field(..., description="JWT signing key")
    database_url: str = Field(..., description="async SQLAlchemy URL")

    # S3 (bucket required, endpoint optional)
    s3_bucket: str = Field(...)
    aws_region: str = "us-east-1"
    s3_endpoint_url: str | None = None

    # Service URLs (default for dev; can override with env)
    face_url: str = "http://face-detection:8001"
    classifier_url: str = "http://catdog-classifier:8002"

    max_upload_bytes: int = 10 * 1024 * 1024
    webhook_signature_header: str = "X-Webhook-Signature"

    cors_origins: List[str] = []
    cors_origins_raw: str | None = Field(
        default=None,
        validation_alias="CORS_ORIGINS",  # read this env var into the raw field
    )

    @model_validator(mode="after")
    def _normalize_cors(self):
        s = (self.cors_origins_raw or "").strip()
        if not s:
            self.cors_origins = []
            return self

        # Allow JSON list OR comma-separated string
        if s.startswith("["):
            try:
                arr = json.loads(s)
                if isinstance(arr, list):
                    self.cors_origins = [str(i).strip() for i in arr if str(i).strip()]
                    return self
            except Exception:
                # fall through to CSV parsing
                pass

        self.cors_origins = [part.strip() for part in s.split(",") if part.strip()]
        return self

settings = Settings()
