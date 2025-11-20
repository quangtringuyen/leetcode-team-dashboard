"""
Example Integration of Modern UI Components
This file shows how to update app.py to use the new modern UI components
"""

import streamlit as st
import pandas as pd
from ui.components import (
    inject_base_css,
    modern_title,
    section_header,
    glass_card,
    stat_card,
    badge,
    podium_display,
    leaderboard,
    profile_header,
    pie_difficulty,
    team_bar,
    activity_heatmap,
    trend_chart,
    loading_skeleton,
    metric_grid,
    daily_challenge_card
)

# ==================== SETUP ====================
st.set_page_config(
    layout="wide",
    page_title="LeetCode Team Dashboard",
    page_icon="📊",
    initial_sidebar_state="expanded"
)

# Inject modern CSS
inject_base_css()

# ==================== MODERN TITLE ====================
# OLD:
# st.markdown('<div class="header-title">👨🏼‍💻 LeetCode Team Dashboard</div>', unsafe_allow_html=True)

# NEW:
modern_title("LeetCode Team Dashboard", "👨🏼‍💻")

# ==================== AUTHENTICATION SECTION ====================
# (Authentication logic remains the same, just UI improvements)

with st.sidebar:
    st.markdown("### ⚙️ Settings")
    st.markdown(f"{badge('Connected', 'success')}", unsafe_allow_html=True)

    # Storage indicator
    storage_type = "S3" if use_s3() else "Local"
    storage_badge = badge(f"💾 Storage: {storage_type}", "info")
    st.markdown(storage_badge, unsafe_allow_html=True)

# ==================== CONTROL BUTTONS ====================
section_header("Quick Actions", "⚡")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("🔄 Refresh Data", use_container_width=True):
        bump_cache_buster()
        st.toast("✅ Data refreshed!", icon="🔄")

with col2:
    if st.button("🗂️ Record Snapshot", use_container_width=True):
        record_weekly_snapshots(username, team_data, when=date.today())
        st.toast("✅ Snapshot recorded!", icon="🗂️")

with col3:
    if st.button("📊 Export Data", use_container_width=True):
        # Export logic
        st.toast("✅ Data exported!", icon="📊")

st.divider()

# ==================== TEAM STATS OVERVIEW ====================
# NEW: Modern stat cards in grid
section_header("Team Overview", "📊")

# Calculate team stats
total_solved = sum([m.get('totalSolved', 0) for m in team_data])
total_members = len(team_data)
avg_solved = total_solved // total_members if total_members > 0 else 0
top_solver = max(team_data, key=lambda x: x.get('totalSolved', 0)) if team_data else None

metrics = [
    {
        "label": "Total Solved",
        "value": str(total_solved),
        "icon": "✅",
        "variant": "success",
        "delta": "+25 this week"  # Calculate from history
    },
    {
        "label": "Team Members",
        "value": str(total_members),
        "icon": "👥",
        "variant": "primary"
    },
    {
        "label": "Average Solved",
        "value": str(avg_solved),
        "icon": "📈",
        "variant": "info"
    },
    {
        "label": "Top Solver",
        "value": top_solver.get('name', 'N/A') if top_solver else 'N/A',
        "icon": "🏆",
        "variant": "warning"
    }
]

metric_grid(metrics, columns=4)

st.divider()

# ==================== PODIUM DISPLAY ====================
# NEW: Show top 3 in podium layout
section_header("Top Performers", "🏆")

if len(df_sorted) >= 3:
    # Convert top 3 rows to list of dicts
    top_3_members = df_sorted.head(3).to_dict('records')
    selected_user = podium_display(top_3_members, selected_user=selected_user)
else:
    st.info("🏆 Need at least 3 team members for podium display")

st.divider()

# ==================== LEADERBOARD ====================
# NEW: Modern leaderboard with animations
selected_user = leaderboard(df_sorted, selected_user_un=selected_user)

st.divider()

# ==================== MEMBER PROFILE ====================
if selected_user and selected_member_data:
    section_header("Member Profile", "👤")

    # NEW: Modern profile header
    profile_header(selected_member_data)

    # Stats in grid
    member_stats = [
        {
            "label": "Total Solved",
            "value": str(selected_member_data.get('totalSolved', 0)),
            "icon": "✅",
            "variant": "success"
        },
        {
            "label": "Global Rank",
            "value": f"#{selected_member_data.get('ranking', 'N/A')}",
            "icon": "🏅",
            "variant": "primary"
        },
        {
            "label": "Acceptance Rate",
            "value": f"{selected_member_data.get('acceptanceRate', 0)}%",
            "icon": "📊",
            "variant": "info"
        },
        {
            "label": "Total Attempted",
            "value": str(selected_member_data.get('totalAttempted', 0)),
            "icon": "📝",
            "variant": "warning"
        }
    ]

    metric_grid(member_stats, columns=4)

    st.divider()

    # Difficulty breakdown
    section_header("Difficulty Breakdown", "🎯")

    submissions = selected_member_data.get('submissions', [])
    easy_count = next((s['count'] for s in submissions if s.get('difficulty') == 'Easy'), 0)
    med_count = next((s['count'] for s in submissions if s.get('difficulty') == 'Medium'), 0)
    hard_count = next((s['count'] for s in submissions if s.get('difficulty') == 'Hard'), 0)

    col1, col2 = st.columns([1, 1])

    with col1:
        # NEW: Enhanced pie chart
        pie_difficulty(easy_count, med_count, hard_count, title=f"{selected_member_data.get('name')}'s Progress")

    with col2:
        # Additional stats or charts
        st.markdown("### 📈 Statistics")
        st.metric("Easy Problems", easy_count, delta=f"{easy_count*100//(easy_count+med_count+hard_count) if (easy_count+med_count+hard_count) > 0 else 0}%")
        st.metric("Medium Problems", med_count, delta=f"{med_count*100//(easy_count+med_count+hard_count) if (easy_count+med_count+hard_count) > 0 else 0}%")
        st.metric("Hard Problems", hard_count, delta=f"{hard_count*100//(easy_count+med_count+hard_count) if (easy_count+med_count+hard_count) > 0 else 0}%")

st.divider()

# ==================== DAILY CHALLENGE ====================
section_header("Today's Challenge", "🎯")

daily_challenge = get_daily_challenge()
daily_challenge_card(daily_challenge)

st.divider()

# ==================== RECENT ACTIVITY ====================
section_header("Recent Activity", "📅")

# Activity heatmap for selected member
if selected_user and calendar_df is not None and not calendar_df.empty:
    activity_heatmap(calendar_df, selected_user)
else:
    st.info("📅 Select a member to view their activity heatmap")

st.divider()

# ==================== TEAM PERFORMANCE ====================
section_header("Team Performance", "📊")

if not df_sorted.empty:
    # NEW: Enhanced bar chart with gradients
    team_bar(df_sorted, title="Team Leaderboard - Total Accepted Challenges")
else:
    st.info("📊 No team data available")

st.divider()

# ==================== PROGRESS TRENDS ====================
section_header("Progress Trends", "📈")

# Prepare trend data
if history_data and len(history_data) > 0:
    # Convert history to trend dataframe
    trend_df = pd.DataFrame(history_data)

    # NEW: Modern trend chart with area fill
    trend_chart(trend_df, title="Weekly Progress - Last 12 Weeks")
else:
    st.info("📈 No historical data available. Record snapshots to see trends.")

st.divider()

# ==================== WEEKLY COMPARISON ====================
section_header("Week-over-Week Changes", "📊")

if weekly_comparison_df is not None and not weekly_comparison_df.empty:
    # Enhanced table with styling
    st.dataframe(
        weekly_comparison_df,
        use_container_width=True,
        height=400,
        column_config={
            "Member": st.column_config.TextColumn("Member", width="medium"),
            "Change": st.column_config.NumberColumn("Change", format="%+d"),
            "This Week": st.column_config.NumberColumn("This Week"),
            "Last Week": st.column_config.NumberColumn("Last Week"),
        }
    )
else:
    st.info("📊 Week-over-week comparison will appear after recording multiple snapshots")

st.divider()

# ==================== TEAM MANAGEMENT ====================
section_header("Team Management", "⚙️")

with st.expander("➕ Add Team Member"):
    col1, col2 = st.columns(2)

    with col1:
        new_username = st.text_input("LeetCode Username", key="new_username")

    with col2:
        new_display_name = st.text_input("Display Name (optional)", key="new_display")

    if st.button("➕ Add Member", use_container_width=True):
        if new_username:
            with st.spinner("Fetching user data..."):
                user_data = fetch_user_data(new_username)

                if user_data:
                    members_list.append({
                        "username": new_username,
                        "name": new_display_name or user_data.get('realName', new_username)
                    })
                    save_members(current_user, members_list)
                    st.success(f"✅ Added {new_username} to the team!")
                    st.rerun()
                else:
                    st.error(f"❌ Failed to fetch data for {new_username}. Please check the username.")

with st.expander("🗑️ Remove Team Member"):
    if members_list:
        member_to_remove = st.selectbox(
            "Select member to remove",
            options=[m.get('username') for m in members_list],
            format_func=lambda x: next((m.get('name', x) for m in members_list if m.get('username') == x), x)
        )

        if st.button("🗑️ Remove Member", use_container_width=True, type="primary"):
            members_list = [m for m in members_list if m.get('username') != member_to_remove]
            save_members(current_user, members_list)
            st.success(f"✅ Removed {member_to_remove} from the team!")
            st.rerun()
    else:
        st.info("👥 No team members to remove")

# ==================== FOOTER ====================
st.divider()
st.markdown(
    f"""
    <div style="text-align: center; color: var(--text-tertiary); padding: 2rem 0;">
        <p>Built with ❤️ using Streamlit • {badge('Modern UI 2.0', 'primary')}</p>
        <p style="font-size: 0.875rem;">© 2025 LeetCode Team Dashboard</p>
    </div>
    """,
    unsafe_allow_html=True
)

# ==================== KEY IMPROVEMENTS ====================
"""
BEFORE vs AFTER Comparison:

1. TITLE:
   Before: st.markdown('<div class="header-title">...</div>', unsafe_allow_html=True)
   After:  modern_title("LeetCode Team Dashboard", "👨🏼‍💻")

2. STATS:
   Before: Manual column layout with custom HTML/CSS
   After:  metric_grid(metrics, columns=4)

3. LEADERBOARD:
   Before: Basic list with progress bars
   After:  leaderboard(df_sorted, selected_user) - with animations & hover effects

4. PROFILE:
   Before: Simple image + text
   After:  profile_header(data) - gradient background, animated, badges

5. CHARTS:
   Before: Basic plotly charts
   After:  Enhanced charts with custom colors, animations, better tooltips

6. PODIUM:
   Before: Not available
   After:  podium_display(top_3) - Medal display for top 3

7. LOADING:
   Before: st.spinner only
   After:  loading_skeleton() + spinner

8. DAILY CHALLENGE:
   Before: Simple text display
   After:  daily_challenge_card() - Glass card with badges

9. ACTIVITY:
   Before: Basic calendar display
   After:  activity_heatmap() - GitHub-style heatmap

10. TRENDS:
    Before: Line chart
    After:  trend_chart() - Area chart with gradients & unified hover
"""
