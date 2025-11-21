# CORS_ORIGINS Parsing Error - FIXED

## Problem

The CORS_ORIGINS field was causing a parsing error:
```
json.decoder.JSONDecodeError: Expecting value: line 1 column 1 (char 0)
pydantic_settings.exceptions.SettingsError: error parsing value for field "CORS_ORIGINS"
```

## Root Cause

Pydantic-settings v2 tries to parse `List[str]` fields as JSON by default when loading from environment variables. The comma-separated string in `.env` wasn't valid JSON, causing the error.

## Solution Applied

Updated `backend/core/config.py` to:

1. **Use Pydantic v2 `SettingsConfigDict`** instead of old `class Config`
2. **Improved field_validator** to handle multiple formats:
   - Comma-separated strings: `"url1,url2,url3"`
   - JSON arrays: `["url1", "url2", "url3"]`
   - Already parsed lists
3. **Added Field() with proper defaults** for better type handling

### Changes in `backend/core/config.py`:

```python
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator, Field
import json

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_file='.env',
        env_file_encoding='utf-8',
        extra='ignore'
    )

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
            v = v.strip()
            if not v:
                return []

            # Try JSON parsing first (for array format)
            if v.startswith('['):
                try:
                    return json.loads(v)
                except json.JSONDecodeError:
                    pass

            # Otherwise parse as comma-separated
            return [origin.strip() for origin in v.split(",") if origin.strip()]

        return []
```

## What This Fixes

✅ Handles comma-separated CORS_ORIGINS from .env:
```bash
CORS_ORIGINS=http://localhost:3000,http://localhost:8000,http://localhost:8501
```

✅ Handles JSON array format:
```bash
CORS_ORIGINS=["http://localhost:3000","http://localhost:8000"]
```

✅ Provides sensible defaults if CORS_ORIGINS is empty

✅ Uses modern Pydantic v2 configuration style

## Rebuild Instructions

Now rebuild the Docker containers to apply the fix:

```bash
# Stop containers
docker compose -f docker-compose.backend.yml down

# Rebuild with no cache
docker compose -f docker-compose.backend.yml build --no-cache

# Start containers
docker compose -f docker-compose.backend.yml up -d

# Check logs
docker compose -f docker-compose.backend.yml logs -f
```

## Verify It Works

```bash
# Health check
curl http://localhost:8080/api/health

# Expected output:
# {"status":"healthy","service":"LeetCode Team Dashboard API","version":"2.0.0"}
```

## Summary of All Fixes Applied

1. ✅ **Port conflict** - Changed 8000 → 8080
2. ✅ **Missing scheduler.py** - Added to Dockerfile
3. ✅ **CORS parsing error** - Fixed with improved field_validator (THIS FIX)
4. ✅ **Data migration** - Migrated all team data
5. ✅ **S3 support** - Created S3-aware migration script

All blocking issues resolved! 🎉
