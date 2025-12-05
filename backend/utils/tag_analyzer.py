"""
Problem tags analysis utilities
Tracks which topics members solve (Arrays, DP, Trees, etc.)
"""

from typing import Dict, List, Any, Set
from collections import defaultdict, Counter


# Common LeetCode problem tags/topics
COMMON_TAGS = [
    "Array", "String", "Hash Table", "Dynamic Programming", "Math",
    "Sorting", "Greedy", "Depth-First Search", "Binary Search", "Tree",
    "Breadth-First Search", "Database", "Two Pointers", "Bit Manipulation",
    "Stack", "Design", "Heap (Priority Queue)", "Graph", "Simulation",
    "Backtracking", "Sliding Window", "Union Find", "Linked List",
    "Ordered Set", "Monotonic Stack", "Trie", "Divide and Conquer",
    "Binary Search Tree", "Recursion", "Binary Tree", "Counting",
    "Matrix", "Queue", "Memoization", "Prefix Sum", "Number Theory"
]


def analyze_problem_tags(submissions: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analyze problem tags from submission history.
    
    Args:
        submissions: List of submissions with problem metadata
        
    Returns:
        Dict with tag counts, strengths, weaknesses, and recommendations
    """
    if not submissions:
        return {
            "tag_counts": {},
            "total_unique_tags": 0,
            "top_tags": [],
            "weak_tags": [],
            "coverage_score": 0,
            "recommendation": "Start solving problems to build tag history"
        }
    
    # Count tags
    tag_counter = Counter()
    for sub in submissions:
        tags = sub.get("tags", [])
        for tag in tags:
            tag_counter[tag] += 1
    
    # Calculate statistics
    total_unique_tags = len(tag_counter)
    total_problems = len(submissions)
    
    # Get top tags (strengths)
    top_tags = [
        {"tag": tag, "count": count, "percentage": round((count / total_problems) * 100, 1)}
        for tag, count in tag_counter.most_common(10)
    ]
    
    # Identify weak tags (common tags with low counts)
    solved_tags = set(tag_counter.keys())
    common_tags_set = set(COMMON_TAGS)
    
    # Tags that are common but not solved much
    weak_tags = []
    for tag in COMMON_TAGS[:20]:  # Check top 20 common tags
        if tag in tag_counter:
            count = tag_counter[tag]
            if count < 3:  # Less than 3 problems
                weak_tags.append({
                    "tag": tag,
                    "count": count,
                    "recommendation": f"Practice more {tag} problems"
                })
        else:
            weak_tags.append({
                "tag": tag,
                "count": 0,
                "recommendation": f"Start with {tag} problems"
            })
    
    # Limit weak tags to top 5
    weak_tags = weak_tags[:5]
    
    # Calculate coverage score (how many common tags are covered)
    covered_common_tags = len(solved_tags & common_tags_set)
    coverage_score = round((covered_common_tags / len(COMMON_TAGS)) * 100, 1)
    
    # Generate recommendation
    if not top_tags:
        recommendation = "Start solving problems across different topics"
    elif coverage_score < 30:
        recommendation = f"Expand your topic coverage. Try: {', '.join([t['tag'] for t in weak_tags[:3]])}"
    elif coverage_score < 60:
        recommendation = f"Good progress! Focus on: {', '.join([t['tag'] for t in weak_tags[:2]])}"
    else:
        recommendation = "Excellent topic coverage! Keep diversifying"
    
    return {
        "tag_counts": dict(tag_counter),
        "total_unique_tags": total_unique_tags,
        "top_tags": top_tags,
        "weak_tags": weak_tags,
        "coverage_score": coverage_score,
        "recommendation": recommendation
    }


def get_team_tag_analysis(member_submissions: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
    """
    Analyze tags for all team members.
    
    Args:
        member_submissions: Dict mapping member usernames to their submissions
        
    Returns:
        List of dicts with member and their tag analysis
    """
    team_analysis = []
    
    for member, submissions in member_submissions.items():
        analysis = analyze_problem_tags(submissions)
        
        team_analysis.append({
            "member": member,
            **analysis
        })
    
    # Sort by coverage score (descending)
    team_analysis.sort(key=lambda x: x["coverage_score"], reverse=True)
    
    return team_analysis


def get_team_tag_heatmap(team_analysis: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Create a heatmap of team's collective tag coverage.
    
    Args:
        team_analysis: Output from get_team_tag_analysis()
        
    Returns:
        Dict with team-wide tag statistics
    """
    # Aggregate all tags across team
    team_tag_counter = Counter()
    
    for member_data in team_analysis:
        tag_counts = member_data.get("tag_counts", {})
        for tag, count in tag_counts.items():
            team_tag_counter[tag] += count
    
    # Calculate team strengths and weaknesses
    total_team_problems = sum(team_tag_counter.values())
    
    team_strengths = [
        {
            "tag": tag,
            "count": count,
            "percentage": round((count / total_team_problems) * 100, 1) if total_team_problems > 0 else 0
        }
        for tag, count in team_tag_counter.most_common(10)
    ]
    
    # Team weaknesses (common tags with low coverage)
    solved_tags = set(team_tag_counter.keys())
    common_tags_set = set(COMMON_TAGS)
    
    team_weaknesses = []
    for tag in COMMON_TAGS[:15]:
        if tag not in team_tag_counter or team_tag_counter[tag] < 5:
            count = team_tag_counter.get(tag, 0)
            team_weaknesses.append({
                "tag": tag,
                "count": count,
                "recommendation": f"Team should focus on {tag}"
            })
    
    team_weaknesses = team_weaknesses[:5]
    
    # Coverage score
    covered_tags = len(solved_tags & common_tags_set)
    team_coverage = round((covered_tags / len(COMMON_TAGS)) * 100, 1)
    
    return {
        "team_strengths": team_strengths,
        "team_weaknesses": team_weaknesses,
        "team_coverage_score": team_coverage,
        "total_unique_tags": len(team_tag_counter),
        "total_problems": total_team_problems
    }


def recommend_problems_by_weak_tags(
    weak_tags: List[Dict[str, Any]],
    difficulty: str = "medium"
) -> List[Dict[str, str]]:
    """
    Recommend problems based on weak tags.
    
    Args:
        weak_tags: List of weak tags from analysis
        difficulty: Preferred difficulty level
        
    Returns:
        List of problem recommendations
    """
    recommendations = []
    
    for weak_tag in weak_tags[:3]:  # Top 3 weak tags
        tag = weak_tag["tag"]
        recommendations.append({
            "tag": tag,
            "difficulty": difficulty,
            "reason": f"Strengthen your {tag} skills",
            "search_query": f"{tag} {difficulty}"
        })
    
    return recommendations
