"""
Storage abstraction for S3 or local file system
Migrated from original app.py
"""

import json
import os
from typing import Any, Dict
import boto3
from backend.core.config import settings

def use_s3() -> bool:
    """Check if S3 storage is configured"""
    return all([
        settings.AWS_ACCESS_KEY_ID,
        settings.AWS_SECRET_ACCESS_KEY,
        settings.AWS_DEFAULT_REGION,
        settings.S3_BUCKET_NAME
    ])

def get_s3_client():
    """Get S3 client"""
    return boto3.client(
        "s3",
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_DEFAULT_REGION
    )

def get_s3_key(local_path: str) -> tuple:
    """Get S3 bucket and key from local path"""
    bucket = settings.S3_BUCKET_NAME
    prefix = settings.S3_PREFIX.rstrip("/")
    key = f"{prefix}/{local_path.lstrip('/')}"
    return bucket, key

def read_json(local_path: str, default: Any = None) -> Any:
    """Read JSON from S3 or local file"""
    if use_s3():
        try:
            s3 = get_s3_client()
            bucket, key = get_s3_key(local_path)
            obj = s3.get_object(Bucket=bucket, Key=key)
            return json.loads(obj["Body"].read().decode("utf-8"))
        except Exception as e:
            print(f"S3 read error: {e}")
            return default
    else:
        full_path = os.path.join(settings.DATA_DIR, local_path)
        if not os.path.exists(full_path):
            return default
        try:
            with open(full_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Local read error: {e}")
            return default

def write_json(local_path: str, data: Any) -> bool:
    """Write JSON to S3 or local file"""
    try:
        if use_s3():
            s3 = get_s3_client()
            bucket, key = get_s3_key(local_path)
            s3.put_object(
                Bucket=bucket,
                Key=key,
                Body=json.dumps(data, indent=2, ensure_ascii=False).encode("utf-8")
            )
        else:
            full_path = os.path.join(settings.DATA_DIR, local_path)
            os.makedirs(os.path.dirname(full_path) or settings.DATA_DIR, exist_ok=True)
            with open(full_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Write error: {e}")
        return False
