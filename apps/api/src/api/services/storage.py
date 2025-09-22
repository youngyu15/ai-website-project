import os
import boto3
from urllib.parse import urlparse

s3 = boto3.client("s3")

async def get_object_bytes(uri: str) -> bytes:
    """
    Load bytes from a given URI.
    Supports:
      - s3://bucket/key
      - file:///absolute/path or plain /path
    """
    parsed = urlparse(uri)

    if parsed.scheme == "s3":
        bucket = parsed.netloc
        key = parsed.path.lstrip("/")
        resp = s3.get_object(Bucket=bucket, Key=key)
        return resp["Body"].read()

    if parsed.scheme == "file":
        with open(parsed.path, "rb") as f:
            return f.read()

    if parsed.scheme == "":
        # assume it's a plain local path
        with open(uri, "rb") as f:
            return f.read()

    raise ValueError(f"Unsupported URI scheme: {parsed.scheme}")
