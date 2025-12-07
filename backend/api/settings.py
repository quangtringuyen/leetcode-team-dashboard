from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List
import json
from datetime import datetime

from backend.api.auth import get_current_user
from backend.core.database import get_db_connection

router = APIRouter()

class SettingUpdate(BaseModel):
    key: str
    value: Any

@router.get("/")
def get_settings(current_user: dict = Depends(get_current_user)):
    """Get all system settings"""
    # Check cache first (settings don't change often)
    from backend.core.database import get_cached_data, set_cached_data
    
    cache_key = "system_settings_all"
    cached_settings = get_cached_data(cache_key, ttl_seconds=60)  # Cache for 1 minute
    if cached_settings:
        return cached_settings

    settings = {}
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT key, value FROM system_settings")
        rows = cursor.fetchall()
        
        for row in rows:
            try:
                # Try to parse JSON, otherwise return as string
                settings[row["key"]] = json.loads(row["value"])
            except:
                settings[row["key"]] = row["value"]
    
    # Save to cache
    set_cached_data(cache_key, settings)
    return settings

@router.post("/")
def update_setting(setting: SettingUpdate, current_user: dict = Depends(get_current_user)):
    """Update a system setting"""
    
    # Only allow certain keys for now to prevent abuse
    ALLOWED_KEYS = [
        "weekly_goal", 
        "team_name", 
        "refresh_interval",
        "snapshot_schedule_day",
        "snapshot_schedule_time",
        "notification_check_interval",
        "problems_per_member_weekly"
    ]
    
    if setting.key not in ALLOWED_KEYS:
        raise HTTPException(status_code=400, detail=f"Setting key '{setting.key}' is not allowed")
    
    value_str = json.dumps(setting.value)
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        INSERT OR REPLACE INTO system_settings (key, value, updated_at)
        VALUES (?, ?, ?)
        """, (setting.key, value_str, datetime.utcnow().isoformat()))
        conn.commit()
        
        # Invalidate cache
        cursor.execute("DELETE FROM api_cache WHERE key = 'system_settings_all'")
        conn.commit()
        
    return {"message": "Setting updated successfully", "key": setting.key, "value": setting.value}
