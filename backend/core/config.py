"""
Configuration settings
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator, Field
from typing import List, Union, Any
import os
import json

class Settings(BaseSettings):
    """Application settings"""

    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_file='.env',
        env_file_encoding='utf-8',
        extra='ignore'
    )

    # API Settings
    API_V1_STR: str = "/api"
    PROJECT_NAME: str = "LeetCode Team Dashboard"

    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # CORS - Keep as List[str] type for proper typing
    CORS_ORIGINS: List[str] = Field(
        default=[
            "http://localhost:3000",
            "http://localhost:8000",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:8000",
        ]
    )

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Any) -> List[str]:
        """Parse CORS_ORIGINS from various formats"""
        # If it's already a list, return it
        if isinstance(v, list):
            return v

        # If it's a string, try to parse it
        if isinstance(v, str):
            # Remove any whitespace
            v = v.strip()

            # Empty string returns default
            if not v:
                return []

            # Try JSON parsing first (for array format like ["url1", "url2"])
            if v.startswith('['):
                try:
                    return json.loads(v)
                except json.JSONDecodeError:
                    pass

            # Otherwise parse as comma-separated
            return [origin.strip() for origin in v.split(",") if origin.strip()]

        # Fallback to empty list
        return []

    # AWS S3 (Optional)
    AWS_ACCESS_KEY_ID: str = os.getenv("AWS_ACCESS_KEY_ID", "")
    AWS_SECRET_ACCESS_KEY: str = os.getenv("AWS_SECRET_ACCESS_KEY", "")
    AWS_DEFAULT_REGION: str = os.getenv("AWS_DEFAULT_REGION", "ap-southeast-1")
    S3_BUCKET_NAME: str = os.getenv("S3_BUCKET_NAME", "")
    S3_PREFIX: str = os.getenv("S3_PREFIX", "prod")

    # Storage paths
    DATA_DIR: str = "data"
    MEMBERS_FILE: str = "members.json"
    HISTORY_FILE: str = "history.json"
    USERS_FILE: str = "users.json"

settings = Settings()
