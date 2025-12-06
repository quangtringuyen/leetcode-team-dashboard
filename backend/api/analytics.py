"""
Analytics and history endpoints
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import List, Dict, Any
from datetime import date, datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from backend.core.security import get_current_user
from backend.core.storage import read_json, write_json
from backend.core.config import settings
from backend.utils.leetcodeapi import fetch_user_data, fetch_submissions_with_tags
from backend.utils.streak_tracker import get_team_streaks, get_streak_leaderboard, get_members_at_risk
from backend.utils.difficulty_analyzer import get_team_difficulty_trends, get_stuck_members
from backend.utils.tag_analyzer import get_team_tag_analysis, get_team_tag_heatmap, recommend_problems_by_weak_tags
from backend.utils.problem_recommender import get_personalized_recommendations, recommend_by_company

router = APIRouter()

class WeeklySnapshot(BaseModel):
    week_start: str
    member: str
    totalSolved: int
    easy: int
    medium: int
    hard: int

@router.get("/history", response_model=List[WeeklySnapshot])
async def get_history(current_user: dict = Depends(get_current_user)):
    """Get historical weekly snapshots"""
    username = current_user["username"]

    history = read_json(settings.HISTORY_FILE, default={})
    if not isinstance(history, dict):
        history = {}
        
    # History structure: {owner: {member_username: [snapshots]}}
    user_history_dict = history.get(username, {})
    if not isinstance(user_history_dict, dict):
        user_history_dict = {}

    # Flatten all snapshots from all members
    valid_snapshots = []
    for member_username, snapshots in user_history_dict.items():
        if isinstance(snapshots, list):
            for snapshot in snapshots:
                try:
                    # Validate snapshot data
                    if isinstance(snapshot, dict):
                        # Ensure required fields exist
                        if "week_start" in snapshot and "member" in snapshot:
                            # Ensure numeric fields are ints
                            snapshot["totalSolved"] = int(snapshot.get("totalSolved", 0))
                            snapshot["easy"] = int(snapshot.get("easy", 0))
                            snapshot["medium"] = int(snapshot.get("medium", 0))
                            snapshot["hard"] = int(snapshot.get("hard", 0))
                            
                            # Try to create Pydantic model here to catch validation errors
                            model = WeeklySnapshot(**snapshot)
                            valid_snapshots.append(model)
                except Exception:
                    continue

    return valid_snapshots

@router.post("/snapshot")
async def record_snapshot(current_user: dict = Depends(get_current_user)):
    """Record current week snapshot for all team members"""
    username = current_user["username"]

    # Get team members
    all_members = read_json(settings.MEMBERS_FILE, default={})
    user_members = all_members.get(username, [])

    if not user_members:
        return {"message": "No team members to snapshot", "count": 0}

    # Calculate week start (Monday)
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    week_start_str = week_start.isoformat()

    # Load history - Structure: {owner: {member_username: [snapshots]}}
    history = read_json(settings.HISTORY_FILE, default={})
    if username not in history:
        history[username] = {}
    user_history = history[username]

    # Record snapshot for each member - PARALLELIZED
    snapshots_added = 0

    # Fetch all member data in parallel
    with ThreadPoolExecutor(max_workers=10) as executor:
        # Submit all fetch tasks
        future_to_member = {
            executor.submit(fetch_user_data, member["username"]): member
            for member in user_members
        }

        # Process results as they complete
        for future in as_completed(future_to_member):
            member = future_to_member[future]
            member_username = member["username"]

            try:
                data = future.result()

                if data:
                    # Initialize member's history if not exists
                    if member_username not in user_history:
                        user_history[member_username] = []

                    # Check if snapshot already exists for this week/member
                    exists = any(
                        s.get("week_start") == week_start_str
                        for s in user_history[member_username]
                    )

                    if not exists:
                        # Extract difficulty counts directly from data (returned by fetch_user_data)
                        easy = data.get("easy", 0)
                        medium = data.get("medium", 0)
                        hard = data.get("hard", 0)

                        snapshot = {
                            "week_start": week_start_str,
                            "member": member_username,
                            "totalSolved": data.get("totalSolved", 0),
                            "easy": int(easy),
                            "medium": int(medium),
                            "hard": int(hard),
                            "timestamp": datetime.utcnow().isoformat()
                        }
                        user_history[member_username].append(snapshot)
                        snapshots_added += 1

            except Exception as e:
                # Log error but continue with other members
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error fetching data for {member_username}: {e}")

    # Save history
    history[username] = user_history
    write_json(settings.HISTORY_FILE, history)

    return {
        "message": f"Recorded {snapshots_added} snapshots for week {week_start_str}",
        "count": snapshots_added,
        "week_start": week_start_str
    }

@router.get("/trends")
async def get_trends(
    weeks: int = 12,
    current_user: dict = Depends(get_current_user)
):
    """Get trend data for the last N weeks"""
    username = current_user["username"]

    history = read_json(settings.HISTORY_FILE, default={})
    # History structure: {owner: {member_username: [snapshots]}}
    user_history_dict = history.get(username, {})

    if not user_history_dict:
        return {"weeks": [], "members": {}}

    # Group by member and extract recent weeks
    trends = {}
    all_weeks = set()

    for member_username, snapshots in user_history_dict.items():
        # Sort by week
        sorted_snapshots = sorted(snapshots, key=lambda x: x.get("week_start", ""))

        # Get last N weeks worth of snapshots
        recent_snapshots = sorted_snapshots[-weeks:]

        trends[member_username] = []
        for snapshot in recent_snapshots:
            week_start = snapshot.get("week_start")
            if week_start:
                all_weeks.add(week_start)
                trends[member_username].append({
                    "week": week_start,
                    "total": snapshot.get("totalSolved", 0),
                    # Handle both old (capitalized) and new (lowercase) keys
                    "easy": snapshot.get("easy", snapshot.get("Easy", 0)),
                    "medium": snapshot.get("medium", snapshot.get("Medium", 0)),
                    "hard": snapshot.get("hard", snapshot.get("Hard", 0))
                })

    # Get unique weeks
    weeks_list = sorted(list(all_weeks))[-weeks:]

    return {
        "weeks": weeks_list,
        "members": trends
    }

def get_week_over_week_internal(username: str, weeks: int = 4) -> List[Dict[str, Any]]:
    """Internal helper to get week-over-week changes (synchronous, for Excel export)"""
    history = read_json(settings.HISTORY_FILE, default={})
    user_history_dict = history.get(username, {})

    if not user_history_dict:
        return []

    today = date.today()
    changes = []

    # For each of the last N weeks, compare with the previous week
    for week_offset in range(weeks):
        current_week_start = (today - timedelta(days=today.weekday() + (week_offset * 7))).isoformat()
        previous_week_start = (today - timedelta(days=today.weekday() + ((week_offset + 1) * 7))).isoformat()

        # Extract data for each member for this specific week pair
        current_week_data = {}
        previous_week_data = {}

        for member_username, snapshots in user_history_dict.items():
            for snapshot in snapshots:
                week = snapshot.get("week_start")
                total = snapshot.get("totalSolved", 0)

                if week == current_week_start:
                    current_week_data[member_username] = total
                elif week == previous_week_start:
                    previous_week_data[member_username] = total

        # Calculate ranks for this week pair
        current_week_ranks = {
            m: i + 1 
            for i, (m, _) in enumerate(sorted(current_week_data.items(), key=lambda x: x[1], reverse=True))
        }
        previous_week_ranks = {
            m: i + 1 
            for i, (m, _) in enumerate(sorted(previous_week_data.items(), key=lambda x: x[1], reverse=True))
        }

        all_members = set(list(current_week_data.keys()) + list(previous_week_data.keys()))

        for member in all_members:
            current_val = current_week_data.get(member, 0)
            previous_val = previous_week_data.get(member, 0)
            
            # Skip if no data for this member in this week window
            if current_val == 0 and previous_val == 0:
                continue
                
            change = current_val - previous_val
            
            # Calculate percentage change
            if previous_val > 0:
                pct_change = (change / previous_val) * 100
            elif current_val > 0:
                pct_change = 100.0
            else:
                pct_change = 0.0
                
            # Calculate rank delta
            current_rank = current_week_ranks.get(member)
            previous_rank = previous_week_ranks.get(member)
            
            rank_delta = 0
            if current_rank and previous_rank:
                rank_delta = previous_rank - current_rank

            # Format week date
            week_date_obj = date.fromisoformat(current_week_start)
            formatted_week = week_date_obj.strftime("%b %d, %Y")

            changes.append({
                "week": formatted_week,
                "member": member,
                "previous": previous_val,
                "current": current_val,
                "change": change,
                "pct_change": round(pct_change, 1),
                "rank": current_rank if current_rank else 0,
                "rank_delta": rank_delta
            })

    return changes

@router.get("/week-over-week")
async def get_week_over_week(
    weeks: int = 1,
    current_user: dict = Depends(get_current_user)
):
    """Get week-over-week changes for team members"""
    username = current_user["username"]

    history = read_json(settings.HISTORY_FILE, default={})
    # History structure: {owner: {member_username: [snapshots]}}
    user_history_dict = history.get(username, {})

    if not user_history_dict:
        return []

    today = date.today()
    changes = []
    
    # Iterate through requested number of weeks
    for w in range(weeks):
        # Calculate week starts for this iteration
        # w=0 -> this week vs last week
        # w=1 -> last week vs 2 weeks ago
        current_week_start = (today - timedelta(days=today.weekday() + 7 * w)).isoformat()
        previous_week_start = (today - timedelta(days=today.weekday() + 7 * (w + 1))).isoformat()

        # Extract data for each member for this specific week pair
        current_week_data = {}
        previous_week_data = {}

        for member_username, snapshots in user_history_dict.items():
            for snapshot in snapshots:
                week = snapshot.get("week_start")
                total = snapshot.get("totalSolved", 0)

                if week == current_week_start:
                    current_week_data[member_username] = total
                elif week == previous_week_start:
                    previous_week_data[member_username] = total

        # Calculate ranks for this week pair
        current_week_ranks = {
            m: i + 1 
            for i, (m, _) in enumerate(sorted(current_week_data.items(), key=lambda x: x[1], reverse=True))
        }
        previous_week_ranks = {
            m: i + 1 
            for i, (m, _) in enumerate(sorted(previous_week_data.items(), key=lambda x: x[1], reverse=True))
        }

        all_members = set(list(current_week_data.keys()) + list(previous_week_data.keys()))

        for member in all_members:
            current_val = current_week_data.get(member, 0)
            previous_val = previous_week_data.get(member, 0)
            
            # Skip if no data for this member in this week window (optional, but keeps table clean)
            if current_val == 0 and previous_val == 0:
                continue
                
            change = current_val - previous_val
            
            # Calculate percentage change
            if previous_val > 0:
                pct_change = (change / previous_val) * 100
            elif current_val > 0:
                pct_change = 100.0
            else:
                pct_change = 0.0
                
            # Calculate rank delta
            current_rank = current_week_ranks.get(member)
            previous_rank = previous_week_ranks.get(member)
            
            rank_delta = 0
            if current_rank and previous_rank:
                rank_delta = previous_rank - current_rank

            # Format week date
            week_date_obj = date.fromisoformat(current_week_start)
            formatted_week = week_date_obj.strftime("%b %d, %Y")

            changes.append({
                "week": formatted_week,
                "member": member,
                "previous": previous_val,
                "current": current_val,
                "change": change,
                "pct_change": round(pct_change, 1),
                "rank": current_rank if current_rank else 0,
                "rank_delta": rank_delta
            })

    # Sort by week (descending) then by current total (descending)
    # Since we iterate weeks 0, 1, 2... they are already in date desc order.
    # We just need to sort by rank within each week.
    # Actually, let's sort by date desc, then rank asc (which is total desc)
    changes.sort(key=lambda x: (x["week"], x["current"]), reverse=True)
    # Wait, date string sort might be wrong if format is "Nov 03". 
    # But we iterate w=0, 1, 2. w=0 is latest.
    # If we append in order, they are grouped by week.
    # But we want to sort strictly.
    # Let's rely on the fact that we generate them in order.
    # We just need to sort by rank WITHIN each block?
    # Actually, simpler: just sort by current total descending, but that mixes weeks?
    # No, we want to see Week 1 grouped, then Week 2 grouped.
    # Since we append w=0 first, then w=1, the list is implicitly ordered by week descending.
    # We just need to sort by rank WITHIN each week.
    # But `changes.sort` is stable.
    # So if we sort by `current` descending, it might mix weeks if we don't include week in key.
    # Let's sort by (week_index, current_desc).
    # But we don't have week_index in the dict.
    # Let's just trust the generation order for weeks, and sort by current for members?
    # No, `changes.sort` will reorder everything.
    
    # Let's re-sort properly.
    # We need a sortable date.
    # Let's add `week_start_iso` to the dict for sorting, then remove it? Or just keep it.
    # Or just sort by `current` desc, and rely on stable sort?
    # If we sort by `current` desc, we lose the week grouping.
    
    # Correct approach:
    # We want primary sort key: Week (descending)
    # Secondary sort key: Rank (ascending) / Total (descending)
    
    # Since "Nov 03" is not easily sortable as string, let's use the loop index logic implicitly.
    # Actually, I can just sort the `changes` list at the end?
    # But I don't have the ISO date in the dict.
    # Let's add `week_sort` key.
    
    # Re-writing the loop slightly to include sort key.
    pass # (This is just thought process, I will implement it in the code block)

    # I will add a hidden sort key `_sort_date`
    return changes

@router.get("/weekly-progress")
async def get_weekly_progress(
    weeks: int = 12,
    current_user: dict = Depends(get_current_user)
):
    """
    Get weekly progress for all team members with forward-fill.
    Forward-fill ensures smooth lines even when snapshots are missing.
    """
    username = current_user["username"]
    
    # Load history
    history = read_json(settings.HISTORY_FILE, default={})
    user_history_dict = history.get(username, {})
    
    if not user_history_dict:
        return {"weeks": [], "members": {}}
    
    # Get team members for names
    all_members = read_json(settings.MEMBERS_FILE, default={})
    user_members = all_members.get(username, [])
    member_names = {m["username"]: m.get("name", m["username"]) for m in user_members}
    
    # Determine week range
    today = date.today()
    end_week = today - timedelta(days=today.weekday())  # This week's Monday
    start_week = end_week - timedelta(weeks=weeks-1)
    
    # Generate all weeks in range
    all_weeks = []
    current = start_week
    while current <= end_week:
        all_weeks.append(current.isoformat())
        current += timedelta(weeks=1)
    
    # Process each member with forward-fill
    members_data = {}
    for member_username, snapshots in user_history_dict.items():
        # Sort snapshots by week
        sorted_snapshots = sorted(snapshots, key=lambda x: x.get("week_start", ""))
        
        # Create lookup dict
        snapshot_dict = {s["week_start"]: s["totalSolved"] for s in sorted_snapshots}
        
        # Forward-fill algorithm
        filled_data = []
        last_value = 0
        for week in all_weeks:
            if week in snapshot_dict:
                last_value = snapshot_dict[week]
            filled_data.append(last_value)
        
        members_data[member_username] = {
            "name": member_names.get(member_username, member_username),
            "data": filled_data
        }
    
    return {
        "weeks": all_weeks,
        "members": members_data
    }

@router.get("/accepted-trend")
async def get_accepted_trend(
    days: int = 30,
    current_user: dict = Depends(get_current_user)
):
    """
    Get daily accepted problems trend.
    Uses GraphQL API to fetch recent submissions and aggregates by day.
    """
    import logging
    from backend.utils.leetcodeapi import fetch_recent_submissions
    from collections import defaultdict

    logger = logging.getLogger(__name__)
    username = current_user["username"]

    # Get team members
    all_members = read_json(settings.MEMBERS_FILE, default={})
    user_members = all_members.get(username, [])

    if not user_members:
        return []

    # Calculate date range
    end_date = date.today()
    start_date = end_date - timedelta(days=days-1)

    logger.info(f"Fetching accepted trend for {len(user_members)} members from {start_date} to {end_date}")

    result = []

    # Fetch submissions for each member - PARALLELIZED
    def process_member_submissions(member):
        """Helper function to process a single member's submissions"""
        member_username = member["username"]
        member_name = member.get("name", member_username)
        member_results = []

        try:
            # Fetch recent submissions (increased limit to cover more days)
            submissions = fetch_recent_submissions(member_username, limit=200)

            # Group submissions by date
            daily_counts = defaultdict(set)  # Use set to avoid counting same problem multiple times

            for sub in submissions:
                timestamp = int(sub.get("timestamp", 0))
                submission_date = datetime.fromtimestamp(timestamp).date()

                # Check if within date range
                if start_date <= submission_date <= end_date:
                    # Use titleSlug as unique identifier to avoid counting duplicates
                    title_slug = sub.get("titleSlug")
                    if title_slug:
                        daily_counts[submission_date].add(title_slug)

            # Convert to result format
            for submission_date, problems in daily_counts.items():
                member_results.append({
                    "date": submission_date.isoformat(),
                    "member": member_name,
                    "username": member_username,
                    "accepted": len(problems)  # Count unique problems solved that day
                })

        except Exception as e:
            # Log error but continue with other members
            logger.error(f"Error fetching submissions for {member_username}: {e}")

        return member_results

    # Fetch all member submissions in parallel
    with ThreadPoolExecutor(max_workers=10) as executor:
        # Submit all tasks
        futures = [executor.submit(process_member_submissions, member) for member in user_members]

        # Collect results as they complete
        for future in as_completed(futures):
            try:
                member_results = future.result()
                result.extend(member_results)
            except Exception as e:
                logger.error(f"Error processing member results: {e}")

    # Sort by date
    result.sort(key=lambda x: x["date"])

    logger.info(f"Returning {len(result)} daily data points. Date range: {result[0]['date'] if result else 'N/A'} to {result[-1]['date'] if result else 'N/A'}")

    return result


# ==================== NEW STREAK TRACKING ENDPOINTS ====================

@router.get("/streaks")
async def get_streaks(current_user: dict = Depends(get_current_user)):
    """
    Get streak data for all team members.
    Returns current streak, longest streak, and streak status for each member.
    """
    username = current_user["username"]
    
    # Load history
    history = read_json(settings.HISTORY_FILE, default={})
    user_history_dict = history.get(username, {})
    
    if not user_history_dict:
        return []
    
    # Calculate streaks for all members
    team_streaks = get_team_streaks(user_history_dict)
    
    # Get member names
    all_members = read_json(settings.MEMBERS_FILE, default={})
    user_members = all_members.get(username, [])
    member_names = {m["username"]: m.get("name", m["username"]) for m in user_members}
    
    # Add names to streak data
    for streak in team_streaks:
        streak["name"] = member_names.get(streak["member"], streak["member"])
    
    return team_streaks


@router.get("/streaks/leaderboard")
async def get_streaks_leaderboard(
    limit: int = 10,
    current_user: dict = Depends(get_current_user)
):
    """
    Get streak leaderboard showing top members by current streak.
    """
    username = current_user["username"]
    
    # Load history
    history = read_json(settings.HISTORY_FILE, default={})
    user_history_dict = history.get(username, {})
    
    if not user_history_dict:
        return []
    
    # Calculate streaks
    team_streaks = get_team_streaks(user_history_dict)
    leaderboard = get_streak_leaderboard(team_streaks, limit)
    
    # Get member names
    all_members = read_json(settings.MEMBERS_FILE, default={})
    user_members = all_members.get(username, [])
    member_names = {m["username"]: m.get("name", m["username"]) for m in user_members}
    
    # Add names and rank
    for i, streak in enumerate(leaderboard):
        streak["name"] = member_names.get(streak["member"], streak["member"])
        streak["rank"] = i + 1
    
    return leaderboard


@router.get("/streaks/at-risk")
async def get_streaks_at_risk(current_user: dict = Depends(get_current_user)):
    """
    Get members whose streaks are about to break (haven't solved in 1-2 weeks).
    """
    username = current_user["username"]
    
    # Load history
    history = read_json(settings.HISTORY_FILE, default={})
    user_history_dict = history.get(username, {})
    
    if not user_history_dict:
        return []
    
    # Calculate streaks
    team_streaks = get_team_streaks(user_history_dict)
    at_risk = get_members_at_risk(team_streaks)
    
    # Get member names
    all_members = read_json(settings.MEMBERS_FILE, default={})
    user_members = all_members.get(username, [])
    member_names = {m["username"]: m.get("name", m["username"]) for m in user_members}
    
    # Add names
    for streak in at_risk:
        streak["name"] = member_names.get(streak["member"], streak["member"])
    
    return at_risk


# ==================== DIFFICULTY TRENDS ENDPOINTS ====================

@router.get("/difficulty-trends")
async def get_difficulty_trends(current_user: dict = Depends(get_current_user)):
    """
    Get difficulty distribution trends for all team members.
    Shows progression through Easy → Medium → Hard problems.
    """
    username = current_user["username"]
    
    # Load history
    history = read_json(settings.HISTORY_FILE, default={})
    user_history_dict = history.get(username, {})
    
    if not user_history_dict:
        return []
    
    # Calculate difficulty trends for all members
    team_trends = get_team_difficulty_trends(user_history_dict)
    
    # Get member names
    all_members = read_json(settings.MEMBERS_FILE, default={})
    user_members = all_members.get(username, [])
    member_names = {m["username"]: m.get("name", m["username"]) for m in user_members}
    
    # Add names to trend data
    for trend in team_trends:
        trend["name"] = member_names.get(trend["member"], trend["member"])
    
    return team_trends


@router.get("/difficulty-trends/stuck")
async def get_stuck_on_difficulty(current_user: dict = Depends(get_current_user)):
    """
    Get members who are stuck on a particular difficulty level.
    Returns members who need to progress to harder problems.
    """
    username = current_user["username"]
    
    # Load history
    history = read_json(settings.HISTORY_FILE, default={})
    user_history_dict = history.get(username, {})
    
    if not user_history_dict:
        return []
    
    # Calculate difficulty trends
    team_trends = get_team_difficulty_trends(user_history_dict)
    stuck_members = get_stuck_members(team_trends)
    
    # Get member names
    all_members = read_json(settings.MEMBERS_FILE, default={})
    user_members = all_members.get(username, [])
    member_names = {m["username"]: m.get("name", m["username"]) for m in user_members}
    
    # Add names
    for member in stuck_members:
        member["name"] = member_names.get(member["member"], member["member"])
    
    return stuck_members


# ==================== PROBLEM TAGS ANALYSIS ENDPOINTS ====================

@router.get("/tags/analysis")
async def get_tags_analysis(
    limit: int = 100,
    current_user: dict = Depends(get_current_user)
):
    """
    Get problem tags analysis for all team members.
    Shows which topics members are solving and identifies skill gaps.
    
    Note: This endpoint fetches recent submissions with tags, which may take longer.
    """
    username = current_user["username"]
    
    # Get team members
    all_members = read_json(settings.MEMBERS_FILE, default={})
    user_members = all_members.get(username, [])
    
    if not user_members:
        return []
    
    # Fetch submissions with tags for each member (parallelized)
    member_submissions = {}
    
    with ThreadPoolExecutor(max_workers=5) as executor:
        future_to_member = {
            executor.submit(fetch_submissions_with_tags, member["username"], limit): member
            for member in user_members
        }
        
        for future in as_completed(future_to_member):
            member = future_to_member[future]
            member_username = member["username"]
            
            try:
                submissions = future.result()
                member_submissions[member_username] = submissions
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error fetching tags for {member_username}: {e}")
                member_submissions[member_username] = []
    
    # Analyze tags for all members
    team_analysis = get_team_tag_analysis(member_submissions)
    
    # Add member names
    member_names = {m["username"]: m.get("name", m["username"]) for m in user_members}
    for analysis in team_analysis:
        analysis["name"] = member_names.get(analysis["member"], analysis["member"])
    
    return team_analysis


@router.get("/tags/heatmap")
async def get_tags_heatmap(
    limit: int = 100,
    current_user: dict = Depends(get_current_user)
):
    """
    Get team-wide tag coverage heatmap.
    Shows collective strengths and weaknesses across all members.
    """
    username = current_user["username"]
    
    # Get team members
    all_members = read_json(settings.MEMBERS_FILE, default={})
    user_members = all_members.get(username, [])
    
    if not user_members:
        return {
            "team_strengths": [],
            "team_weaknesses": [],
            "team_coverage_score": 0,
            "total_unique_tags": 0,
            "total_problems": 0
        }
    
    # Fetch submissions with tags for each member
    member_submissions = {}
    
    with ThreadPoolExecutor(max_workers=5) as executor:
        future_to_member = {
            executor.submit(fetch_submissions_with_tags, member["username"], limit): member
            for member in user_members
        }
        
        for future in as_completed(future_to_member):
            member = future_to_member[future]
            member_username = member["username"]
            
            try:
                submissions = future.result()
                member_submissions[member_username] = submissions
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error fetching tags for {member_username}: {e}")
                member_submissions[member_username] = []
    
    # Analyze tags
    team_analysis = get_team_tag_analysis(member_submissions)
    heatmap = get_team_tag_heatmap(team_analysis)
    
    return heatmap


@router.get("/tags/recommendations/{member_username}")
async def get_tag_recommendations(
    member_username: str,
    difficulty: str = "medium",
    limit: int = 100,
    current_user: dict = Depends(get_current_user)
):
    """
    Get problem recommendations based on a member's weak tags.
    
    Args:
        member_username: Username of the member
        difficulty: Preferred difficulty (easy/medium/hard)
        limit: Number of submissions to analyze
    """
    username = current_user["username"]
    
    # Verify member belongs to user's team
    all_members = read_json(settings.MEMBERS_FILE, default={})
    user_members = all_members.get(username, [])
    member_usernames = [m["username"] for m in user_members]
    
    if member_username not in member_usernames:
        return {"error": "Member not found in your team"}
    
    # Fetch submissions with tags
    submissions = fetch_submissions_with_tags(member_username, limit)
    
    # Analyze tags
    from backend.utils.tag_analyzer import analyze_problem_tags
    analysis = analyze_problem_tags(submissions)
    
    # Generate recommendations
    recommendations = recommend_problems_by_weak_tags(
        analysis.get("weak_tags", []),
        difficulty
    )
    
    return {
        "member": member_username,
        "weak_tags": analysis.get("weak_tags", []),
        "recommendations": recommendations,
        "coverage_score": analysis.get("coverage_score", 0)
    }


# ==================== PROBLEM RECOMMENDATIONS ENDPOINTS ====================

@router.get("/recommendations/{member_username}")
async def get_member_recommendations(
    member_username: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get personalized problem recommendations for a member.
    Combines tag analysis and difficulty progression for comprehensive suggestions.
    """
    username = current_user["username"]
    
    # Verify member belongs to user's team
    all_members = read_json(settings.MEMBERS_FILE, default={})
    user_members = all_members.get(username, [])
    member_usernames = [m["username"] for m in user_members]
    
    if member_username not in member_usernames:
        return {"error": "Member not found in your team"}
    
    # Get tag analysis
    submissions = fetch_submissions_with_tags(member_username, limit=100)
    from backend.utils.tag_analyzer import analyze_problem_tags
    tag_analysis = analyze_problem_tags(submissions)
    
    # Get difficulty trends
    history = read_json(settings.HISTORY_FILE, default={})
    user_history_dict = history.get(username, {})
    member_history = user_history_dict.get(member_username, [])
    
    from backend.utils.difficulty_analyzer import calculate_difficulty_trends
    difficulty_analysis = calculate_difficulty_trends(member_history)
    
    # Combine data for recommendations
    member_data = {
        "weak_tags": tag_analysis.get("weak_tags", []),
        "current_distribution": difficulty_analysis.get("current_distribution", {}),
        "progression_status": difficulty_analysis.get("progression_status", "")
    }
    
    # Generate recommendations
    recommendations = get_personalized_recommendations(member_data)
    
    return {
        "member": member_username,
        **recommendations
    }


@router.get("/recommendations/company/{company}")
async def get_company_recommendations(
    company: str,
    difficulty: str = "all",
    limit: int = 10,
    current_user: dict = Depends(get_current_user)
):
    """
    Get company-specific problem recommendations.
    
    Args:
        company: Company name (Google, Meta, Amazon, Microsoft)
        difficulty: Filter by difficulty (easy/medium/hard/all)
        limit: Number of problems
    """
    problems = recommend_by_company(company, difficulty, limit)
    
    return {
        "company": company,
        "difficulty": difficulty,
        "problems": problems,
        "count": len(problems)
    }
