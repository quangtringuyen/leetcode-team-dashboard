from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any
from api.auth import get_current_user
from utils.leetcodeapi import fetch_daily_challenge, fetch_recent_submissions
from api.team import get_members
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/daily")
async def get_daily_challenge(current_user: dict = Depends(get_current_user)):
    """
    Get today's LeetCode daily challenge.
    """
    challenge = fetch_daily_challenge()
    if not challenge:
        raise HTTPException(status_code=404, detail="Daily challenge not found")
    return challenge

@router.get("/recent")
async def get_recent_submissions(
    limit: int = 50,
    current_user: dict = Depends(get_current_user)
):
    """
    Get recent accepted submissions from all team members.
    Aggregates submissions from all members and sorts by timestamp.
    """
    # Get all team members
    # We import here to avoid circular imports if any
    from api.team import get_members_list_internal
    
    members = get_members_list_internal(current_user["username"])
    
    all_submissions = []
    
    # Fetch submissions concurrently
    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_user = {
            executor.submit(fetch_recent_submissions, m["username"], 20): m 
            for m in members
        }
        
        for future in as_completed(future_to_user):
            member = future_to_user[future]
            try:
                submissions = future.result()
                # Add member info to each submission
                for sub in submissions:
                    sub["username"] = member["username"]
                    sub["name"] = member.get("name", member["username"])
                    sub["avatar"] = member.get("avatar")
                    all_submissions.append(sub)
            except Exception as e:
                logger.error(f"Error fetching submissions for {member['username']}: {e}")
    
    # Sort by timestamp descending
    all_submissions.sort(key=lambda x: int(x.get("timestamp", 0)), reverse=True)
    
    return all_submissions[:limit]
