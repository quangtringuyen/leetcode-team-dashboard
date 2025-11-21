"""
LeetCode API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from backend.core.security import get_current_user
from utils.leetcodeapi import (
    fetch_user_data,
    fetch_recent_submissions,
    fetch_daily_challenge
)

router = APIRouter()

class LeetCodeUser(BaseModel):
    username: str
    realName: Optional[str] = None
    avatar: str
    ranking: Optional[int] = None
    totalSolved: int
    totalAttempted: int
    acceptanceRate: Optional[float] = None
    submissions: List[Dict[str, Any]]

class RecentSubmission(BaseModel):
    title: str
    titleSlug: str
    date: str
    timestamp: int

class DailyChallenge(BaseModel):
    date: str
    link: str
    title: str
    titleSlug: str
    difficulty: str
    questionId: str

@router.get("/user/{username}", response_model=LeetCodeUser)
async def get_user_stats(
    username: str,
    current_user: dict = Depends(get_current_user)
):
    """Get LeetCode user statistics"""
    data = fetch_user_data(username)

    if not data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User '{username}' not found on LeetCode"
        )

    return LeetCodeUser(**data)

@router.get("/user/{username}/recent", response_model=List[RecentSubmission])
async def get_recent_submissions(
    username: str,
    limit: int = 20,
    current_user: dict = Depends(get_current_user)
):
    """Get recent accepted submissions for a user"""
    submissions = fetch_recent_submissions(username, limit=limit)

    return [
        RecentSubmission(
            title=sub["title"],
            titleSlug=sub["titleSlug"],
            date=str(sub["date"]),
            timestamp=sub["timestamp"]
        )
        for sub in submissions
    ]

@router.get("/daily-challenge", response_model=DailyChallenge)
async def get_daily_challenge():
    """Get today's LeetCode daily challenge"""
    challenge = fetch_daily_challenge()

    if not challenge:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Daily challenge not available"
        )

    return DailyChallenge(**challenge)

@router.post("/refresh/{username}")
async def refresh_user_data(
    username: str,
    current_user: dict = Depends(get_current_user)
):
    """Force refresh user data from LeetCode"""
    data = fetch_user_data(username)

    if not data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Failed to fetch data for user '{username}'"
        )

    return {"message": f"Data refreshed for {username}", "data": data}
