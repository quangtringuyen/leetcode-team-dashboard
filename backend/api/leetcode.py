from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any
from backend.api.auth import get_current_user
from backend.utils.leetcodeapi import fetch_daily_challenge, fetch_recent_submissions
from datetime import date, datetime

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

@router.get("/daily/completions")
async def get_daily_challenge_completions(current_user: dict = Depends(get_current_user)):
    """
    Check which team members have completed today's daily challenge.
    Returns list of members with their completion status.
    """
    # Get today's daily challenge
    challenge = fetch_daily_challenge()
    if not challenge:
        raise HTTPException(status_code=404, detail="Daily challenge not found")
    
    title_slug = challenge.get("titleSlug")
    if not title_slug:
        raise HTTPException(status_code=500, detail="Could not get challenge title slug")
    
    # Get all team members
    from backend.api.team import get_members_list_internal
    from backend.utils.leetcodeapi import fetch_user_data
    
    members = get_members_list_internal(current_user["username"])
    
    completions = []
    today = date.today()
    
    # Check each member's recent submissions
    def check_member_completion(member):
        try:
            # Fetch recent submissions
            submissions = fetch_recent_submissions(member["username"], limit=50)
            
            # Check if any submission matches today's challenge
            completed = False
            completion_time = None
            
            for sub in submissions:
                if sub.get("titleSlug") == title_slug:
                    # Check if submission was made today
                    timestamp = int(sub.get("timestamp", 0))
                    submission_date = datetime.fromtimestamp(timestamp).date()
                    
                    if submission_date == today:
                        completed = True
                        completion_time = datetime.fromtimestamp(timestamp).strftime("%H:%M")
                        break
            
            # Get user profile data for avatar
            user_data = fetch_user_data(member["username"])
            
            return {
                "username": member["username"],
                "name": member.get("name", member["username"]),
                "avatar": user_data.get("avatar") if user_data else None,
                "completed": completed,
                "completionTime": completion_time
            }
        except Exception as e:
            logger.error(f"Error checking completion for {member['username']}: {e}")
            return {
                "username": member["username"],
                "name": member.get("name", member["username"]),
                "avatar": None,
                "completed": False,
                "completionTime": None
            }
    
    # Check all members concurrently
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(check_member_completion, m) for m in members]
        for future in as_completed(futures):
            try:
                result = future.result()
                completions.append(result)
            except Exception as e:
                logger.error(f"Error processing member completion: {e}")
    
    # Sort: completed first, then by completion time, then by name
    completions.sort(key=lambda x: (
        not x["completed"],  # False (completed) comes before True (not completed)
        x["completionTime"] or "99:99",  # Earlier times first
        x["name"]
    ))
    
    return {
        "challenge": challenge,
        "completions": completions,
        "totalMembers": len(completions),
        "completedCount": sum(1 for c in completions if c["completed"])
    }

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
    from backend.api.team import get_members_list_internal
    
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
