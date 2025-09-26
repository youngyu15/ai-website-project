from datetime import datetime, timedelta, timezone
from typing import Any
from jose import jwt
from passlib.context import CryptContext
from uuid import UUID

from api.settings import settings

ALGORITHM = "HS256"
_pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Password hashing

def hash_password(password: str) -> str:
    return _pwd.hash(password)

def verify_password(password: str, password_hash: str) -> bool:
    return _pwd.verify(password, password_hash)

# JWT helpers

def _create_token(subject: str, expires_delta: timedelta, token_type: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": subject,
        "iat": int(now.timestamp()),
        "exp": int((now + expires_delta).timestamp()),
        "type": token_type,
    }
    key = settings.secret_key.get_secret_value()
    return jwt.encode(payload, key, algorithm=ALGORITHM)


def create_access_token(user_id: UUID) -> str:
    return _create_token(str(user_id), timedelta(minutes=settings.access_token_expire_minutes), "access")


def create_refresh_token(user_id: UUID) -> str:
    return _create_token(str(user_id), timedelta(days=settings.refresh_token_expire_days), "refresh")


def decode_token(token: str) -> dict[str, Any]:
    key = settings.secret_key.get_secret_value()
    return jwt.decode(token, key, algorithms=[ALGORITHM])