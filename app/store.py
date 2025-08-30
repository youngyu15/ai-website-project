# app/store.py (fake in-memory stores)
from typing import Dict
from datetime import datetime, timezone

predictions: Dict[str, dict] = {}
uploads: Dict[str, dict] = {}
shares: Dict[str, dict] = {}
webhooks: Dict[str, dict] = {}

MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # 10MB


def now():
    return datetime.now(timezone.utc)