import os
import boto3
from pathlib import Path

s3 = boto3.client("s3")

async def get_object_bytes(src: str) -> bytes:
    """
    Load bytes from a given URI.
    Supports:
      - s3://bucket/key
      - file:///absolute/path or plain /path
    """
    from urllib.parse import urlparse
    scheme = urlparse(src).scheme

    if scheme in ("", None):  # local path like "var/uploads/.."
        return Path(src).read_bytes()

    if scheme == "file":
        return Path(urlparse(src).path).read_bytes()

    if scheme == "s3":
        import boto3
        from urllib.parse import urlparse
        u = urlparse(src)
        s3 = boto3.client("s3")
        obj = s3.get_object(Bucket=u.netloc, Key=u.path.lstrip("/"))
        return obj["Body"].read()

    raise ValueError(f"Unsupported URI scheme: {scheme}")
