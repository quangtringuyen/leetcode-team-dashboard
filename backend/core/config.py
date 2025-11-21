"""
Configuration settings
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_serializer
from typing import List
import os

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

    # CORS - Use string type, parse it later
    # This avoids pydantic-settings trying to JSON parse it
    cors_origins_str: str = Field(
        default="http://localhost:3000,http://localhost:8000,http://127.0.0.1:3000,http://127.0.0.1:8000",
        alias="CORS_ORIGINS"
    )

    @property
    def CORS_ORIGINS(self) -> List[str]:
        """Parse CORS_ORIGINS from comma-separated string"""
        if not self.cors_origins_str:
            return []
        return [origin.strip() for origin in self.cors_origins_str.split(",") if origin.strip()]

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
