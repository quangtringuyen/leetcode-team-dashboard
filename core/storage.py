# core/storage.py
from __future__ import annotations
import json, os, io
from dataclasses import dataclass
from typing import Any, Tuple

try:
    import streamlit as st
    HAS_ST = True
except Exception:
    HAS_ST = False


class Storage:
    """Abstract JSON storage interface."""

    def read_json(self, path: str, default: Any) -> Any:
        raise NotImplementedError

    def write_json(self, path: str, payload: Any) -> None:
        raise NotImplementedError


class LocalStorage(Storage):
    def read_json(self, path: str, default: Any) -> Any:
        if not os.path.exists(path):
            return default
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def write_json(self, path: str, payload: Any) -> None:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)


@dataclass
class S3Config:
    bucket: str
    prefix: str
    access_key: str
    secret_key: str
    region: str


class S3Storage(Storage):
    def __init__(self, cfg: S3Config):
        import boto3
        self.cfg = cfg
        self.client = boto3.client(
            "s3",
            aws_access_key_id=cfg.access_key,
            aws_secret_access_key=cfg.secret_key,
            region_name=cfg.region,
        )

    def _bk(self, path: str) -> Tuple[str, str]:
        key = f"{self.cfg.prefix.rstrip('/')}/{path.lstrip('/')}"
        return self.cfg.bucket, key

    def read_json(self, path: str, default: Any) -> Any:
        try:
            b, k = self._bk(path)
            obj = self.client.get_object(Bucket=b, Key=k)
            return json.loads(obj["Body"].read().decode("utf-8"))
        except Exception:
            return default

    def write_json(self, path: str, payload: Any) -> None:
        b, k = self._bk(path)
        buf = io.BytesIO(json.dumps(payload, indent=2).encode("utf-8"))
        self.client.upload_fileobj(buf, b, k)


def choose_storage() -> Storage:
    """Select S3 or local based on environment variables."""
    try:
        required = ["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_DEFAULT_REGION", "S3_BUCKET_NAME", "S3_PREFIX"]
        if all(os.environ.get(k) for k in required):
            cfg = S3Config(
                bucket=os.environ.get("S3_BUCKET_NAME"),
                prefix=os.environ.get("S3_PREFIX"),
                access_key=os.environ.get("AWS_ACCESS_KEY_ID"),
                secret_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
                region=os.environ.get("AWS_DEFAULT_REGION"),
            )
            return S3Storage(cfg)
    except Exception:
        pass
    return LocalStorage()
