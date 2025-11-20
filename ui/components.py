# ui/components.py
"""
Modern UI Components for LeetCode Team Dashboard
Provides reusable, attractive components with animations and interactivity
"""
from __future__ import annotations
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from typing import List, Dict, Any, Optional

# Import modern styles
from ui.modern_styles import inject_modern_styles

def inject_base_css():
    """Inject modern design system CSS"""
    inject_modern_styles()

def modern_title(text: str, icon: str = "👨🏼‍💻"):
    """Render modern gradient title with animation"""
    st.markdown(
        f'<div class="modern-title animate-fade-in-down">{icon} {text}</div>',
        unsafe_allow_html=True
    )

def section_header(text: str, icon: str = ""):
    """Render section header with decorative line"""
    st.markdown(
        f'<div class="section-title animate-fade-in">{icon} {text}</div>',
        unsafe_allow_html=True
    )

def glass_card(content_html: str, variant: str = "default"):
    """Render glassmorphism card"""
    card_class = f"glass-card glass-card-{variant}" if variant != "default" else "glass-card"
    st.markdown(f'<div class="{card_class} animate-fade-in-up">{content_html}</div>', unsafe_allow_html=True)

def stat_card(label: str, value: str, icon: str = "📊", variant: str = "default", delta: Optional[str] = None):
    """Render modern stat card with icon and optional delta"""
    card_class = f"stat-card stat-card-{variant}" if variant != "default" else "stat-card"
    delta_html = ""
    if delta:
        delta_class = "positive" if "+" in delta else "negative"
        delta_html = f'<div class="stat-delta {delta_class}">{delta}</div>'

    st.markdown(f"""
        <div class="{card_class} animate-scale-in">
            <div class="stat-icon">{icon}</div>
            <div class="stat-value">{value}</div>
            <div class="stat-label">{label}</div>
            {delta_html}
        </div>
    """, unsafe_allow_html=True)

def badge(text: str, variant: str = "primary", outline: bool = False):
    """Render badge component"""
    badge_class = f"badge badge-{variant}"
    if outline:
        badge_class += " badge-outline"
    return f'<span class="{badge_class}">{text}</span>'

def podium_display(top_members: List[Dict[str, Any]], selected_user: Optional[str] = None):
    """
    Display top 3 members in a podium layout
    Args:
        top_members: List of member dicts with keys: username, name, avatar, totalSolved
        selected_user: Currently selected username
    """
    if len(top_members) < 3:
        st.info("🏆 Need at least 3 members for podium display")
        return None

    # Rearrange for podium: 2nd, 1st, 3rd
    podium_order = [top_members[1], top_members[0], top_members[2]] if len(top_members) >= 3 else top_members
    places = ["2️⃣", "🥇", "🥉"]
    place_classes = ["podium-place-2", "podium-place-1", "podium-place-3"]

    st.markdown('<div class="podium-container animate-fade-in-up">', unsafe_allow_html=True)

    cols = st.columns(3)
    ret_selected = selected_user

    for idx, (col, member, medal, place_class) in enumerate(zip(cols, podium_order, places, place_classes)):
        with col:
            is_selected = member.get("username") == selected_user
            st.markdown(f'<div class="podium-place {place_class}">', unsafe_allow_html=True)

            # Avatar with medal
            st.markdown(f"""
                <div style="position: relative; width: fit-content; margin: 0 auto;">
                    <img src="{member.get('avatar', '')}" class="podium-avatar" style="width: 100%; height: auto; display: block;" />
                    <div class="podium-medal">{medal}</div>
                </div>
            """, unsafe_allow_html=True)

            # Name and stats
            st.markdown(f"**{member.get('name', member.get('username'))}**")
            st.markdown(f"{badge(f'{member.get(\"totalSolved\", 0)} Solved', 'success')}", unsafe_allow_html=True)

            # Click to select
            if st.button(f"View Profile", key=f"podium_{member.get('username')}", use_container_width=True):
                ret_selected = member.get("username")

            st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)
    return ret_selected

def leaderboard(df_sorted: pd.DataFrame, selected_user_un: Optional[str] = None):
    """
    Render modern leaderboard with interactive selection
    Args:
        df_sorted: DataFrame with columns: name, username, avatar, Accepted
        selected_user_un: Currently selected username
    Returns:
        Selected username (may change if user clicks)
    """
    section_header("Leaderboard", "🏆")

    if df_sorted.empty:
        st.info("📊 No team members yet. Add members to see the leaderboard!")
        return selected_user_un

    max_ac = int(df_sorted["Accepted"].max())
    ret_selected = selected_user_un

    st.markdown('<div class="leaderboard-container">', unsafe_allow_html=True)

    for i, row in enumerate(df_sorted.itertuples(index=False), start=1):
        is_sel = (row.username == selected_user_un)
        item_class = "leaderboard-item selected" if is_sel else "leaderboard-item"

        st.markdown(f'<div class="{item_class} animate-fade-in" style="animation-delay: {i*50}ms;">', unsafe_allow_html=True)

        c1, c2 = st.columns([0.15, 0.85])

        with c1:
            # Rank badge for top 3
            if i == 1:
                st.markdown("🥇")
            elif i == 2:
                st.markdown("🥈")
            elif i == 3:
                st.markdown("🥉")
            else:
                st.markdown(f"**#{i}**")
            st.image(row.avatar, width=50)

        with c2:
            # Member name button
            if st.button(f"{row.name}", key=f"lb_{row.username}", use_container_width=True):
                ret_selected = row.username

            # Progress bar with stats
            progress = (row.Accepted / max_ac) if max_ac > 0 else 0
            col_stat1, col_stat2 = st.columns([0.7, 0.3])
            with col_stat1:
                st.progress(progress)
            with col_stat2:
                st.markdown(f"**{row.Accepted}** solved", unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)
    return ret_selected

def profile_header(member_data: Dict[str, Any]):
    """
    Render modern profile header with gradient background
    Args:
        member_data: Dict with keys: name, username, avatar, realName, ranking, totalSolved
    """
    st.markdown(f"""
        <div class="profile-header animate-fade-in">
            <img src="{member_data.get('avatar', '')}" class="profile-avatar" />
            <div class="profile-info">
                <div class="profile-name">{member_data.get('name', member_data.get('username'))}</div>
                <div class="profile-username">@{member_data.get('username')}</div>
                <div style="display: flex; gap: 0.5rem; flex-wrap: wrap;">
                    {badge(f"🏅 Rank: {member_data.get('ranking', 'N/A')}", 'info')}
                    {badge(f"✅ {member_data.get('totalSolved', 0)} Solved", 'success')}
                    {badge(f"📝 {member_data.get('totalAttempted', 0)} Attempted", 'warning')}
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

def pie_difficulty(easy: int, med: int, hard: int, title: str = "Accepted by Difficulty"):
    """Modern pie chart for difficulty breakdown"""
    if (easy + med + hard) == 0:
        st.info("🎯 No accepted challenges yet!")
        return

    fig = go.Figure(data=[go.Pie(
        labels=['Easy', 'Medium', 'Hard'],
        values=[easy, med, hard],
        hole=0.5,
        marker=dict(
            colors=['#34A853', '#FFA116', '#EF4743'],
            line=dict(color='#1A1F2E', width=2)
        ),
        textfont=dict(size=14, color='#FFFFFF', family='sans-serif'),
        hovertemplate="<b>%{label}</b><br>Accepted: %{value}<br>Percentage: %{percent}<extra></extra>"
    )])

    fig.update_layout(
        title=dict(text=title, font=dict(size=18, color='#F5F5F5'), x=0.5, xanchor='center'),
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.15,
            xanchor="center",
            x=0.5,
            font=dict(size=13, color='#F5F5F5')
        ),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        height=450,
        margin=dict(l=20, r=20, t=60, b=20),
        font=dict(color='#F5F5F5')
    )

    # Add center annotation
    total = easy + med + hard
    fig.add_annotation(
        text=f"<b>{total}</b><br>Total",
        x=0.5, y=0.5,
        font=dict(size=24, color='#FFA116', family='sans-serif'),
        showarrow=False
    )

    st.plotly_chart(fig, use_container_width=True, key=f"pie_{title}")

def team_bar(perf_df: pd.DataFrame, title: str = "Team Performance"):
    """Modern bar chart for team comparison"""
    if perf_df.empty:
        st.info("📊 No data available for team comparison")
        return

    # Create gradient colors based on values
    colors = px.colors.sample_colorscale(
        [[0, "#EF4743"], [0.5, "#FFA116"], [1, "#34A853"]],
        [val / perf_df["Accepted"].max() for val in perf_df["Accepted"]]
    )

    fig = go.Figure(data=[go.Bar(
        x=perf_df["name"],
        y=perf_df["Accepted"],
        text=perf_df["Accepted"],
        textposition='outside',
        marker=dict(
            color=colors,
            line=dict(color='rgba(255,255,255,0.2)', width=1)
        ),
        hovertemplate="<b>%{x}</b><br>Accepted: %{y}<extra></extra>"
    )])

    fig.update_layout(
        title=dict(text=title, font=dict(size=18, color='#F5F5F5'), x=0.5, xanchor='center'),
        xaxis_title="Team Members",
        yaxis_title="Accepted Challenges",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=20, r=20, t=60, b=20),
        xaxis=dict(tickangle=-45, tickfont=dict(size=12, color='#B4B9C6')),
        yaxis=dict(tickfont=dict(size=12, color='#B4B9C6'), gridcolor='rgba(255,255,255,0.1)'),
        showlegend=False,
        height=450,
        font=dict(color='#F5F5F5')
    )

    fig.update_traces(textfont=dict(size=14, color='#F5F5F5'))

    st.plotly_chart(fig, use_container_width=True, key=f"bar_{title}")

def activity_heatmap(calendar_df: pd.DataFrame, username: str):
    """
    Create GitHub-style activity heatmap
    Args:
        calendar_df: DataFrame with columns: date, accepted
        username: Member username for title
    """
    if calendar_df.empty:
        st.info(f"📅 No activity data available for {username}")
        return

    # Prepare data for heatmap
    calendar_df['date'] = pd.to_datetime(calendar_df['date'])
    calendar_df['week'] = calendar_df['date'].dt.isocalendar().week
    calendar_df['day'] = calendar_df['date'].dt.dayofweek
    calendar_df['day_name'] = calendar_df['date'].dt.day_name()

    # Pivot for heatmap
    heatmap_data = calendar_df.pivot_table(
        values='accepted',
        index='day',
        columns='week',
        aggfunc='sum',
        fill_value=0
    )

    # Create heatmap
    fig = go.Figure(data=go.Heatmap(
        z=heatmap_data.values,
        x=heatmap_data.columns,
        y=['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
        colorscale=[
            [0, '#0A0E1A'],
            [0.2, '#1E2433'],
            [0.4, '#FFA11640'],
            [0.6, '#FFA11680'],
            [0.8, '#FFA116C0'],
            [1, '#FFA116']
        ],
        hovertemplate="Week %{x}<br>%{y}<br>Submissions: %{z}<extra></extra>",
        colorbar=dict(
            title="Submissions",
            titleside="right",
            tickfont=dict(color='#F5F5F5'),
            titlefont=dict(color='#F5F5F5')
        )
    ))

    fig.update_layout(
        title=dict(text=f"Activity Heatmap - {username}", font=dict(size=18, color='#F5F5F5'), x=0.5, xanchor='center'),
        xaxis_title="Week",
        yaxis_title="Day of Week",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        height=300,
        margin=dict(l=20, r=20, t=60, b=20),
        font=dict(color='#F5F5F5'),
        xaxis=dict(tickfont=dict(size=11, color='#B4B9C6')),
        yaxis=dict(tickfont=dict(size=11, color='#B4B9C6'))
    )

    st.plotly_chart(fig, use_container_width=True, key=f"heatmap_{username}")

def trend_chart(trend_df: pd.DataFrame, title: str = "Progress Trend"):
    """
    Create smooth area chart for trends
    Args:
        trend_df: DataFrame with columns: date/week, metric values
        title: Chart title
    """
    if trend_df.empty:
        st.info("📈 No trend data available")
        return

    # Assuming first column is x-axis, rest are metrics
    x_col = trend_df.columns[0]

    fig = go.Figure()

    # Add traces for each metric
    colors = ['#FFA116', '#34A853', '#1E88E5', '#EF4743', '#FBBC04']
    for idx, col in enumerate(trend_df.columns[1:]):
        fig.add_trace(go.Scatter(
            x=trend_df[x_col],
            y=trend_df[col],
            mode='lines+markers',
            name=col,
            line=dict(color=colors[idx % len(colors)], width=3),
            marker=dict(size=8, color=colors[idx % len(colors)], line=dict(color='#1A1F2E', width=2)),
            fill='tonexty' if idx > 0 else 'tozeroy',
            fillcolor=f"rgba({int(colors[idx % len(colors)][1:3], 16)}, {int(colors[idx % len(colors)][3:5], 16)}, {int(colors[idx % len(colors)][5:7], 16)}, 0.1)",
            hovertemplate="<b>%{x}</b><br>%{y}<extra></extra>"
        ))

    fig.update_layout(
        title=dict(text=title, font=dict(size=18, color='#F5F5F5'), x=0.5, xanchor='center'),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        height=400,
        margin=dict(l=20, r=20, t=60, b=20),
        xaxis=dict(
            tickfont=dict(size=12, color='#B4B9C6'),
            gridcolor='rgba(255,255,255,0.1)',
            showgrid=True
        ),
        yaxis=dict(
            tickfont=dict(size=12, color='#B4B9C6'),
            gridcolor='rgba(255,255,255,0.1)',
            showgrid=True
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5,
            font=dict(size=12, color='#F5F5F5')
        ),
        font=dict(color='#F5F5F5'),
        hovermode='x unified'
    )

    st.plotly_chart(fig, use_container_width=True, key=f"trend_{title}")

def loading_skeleton(type: str = "card", count: int = 1):
    """Display loading skeleton"""
    for i in range(count):
        if type == "card":
            st.markdown('<div class="skeleton skeleton-card"></div>', unsafe_allow_html=True)
        elif type == "title":
            st.markdown('<div class="skeleton skeleton-title"></div>', unsafe_allow_html=True)
        elif type == "text":
            st.markdown('<div class="skeleton skeleton-text"></div>', unsafe_allow_html=True)

def metric_grid(metrics: List[Dict[str, Any]], columns: int = 4):
    """
    Display metrics in a responsive grid
    Args:
        metrics: List of dicts with keys: label, value, icon, variant, delta (optional)
        columns: Number of columns in grid
    """
    cols = st.columns(columns)
    for idx, metric in enumerate(metrics):
        with cols[idx % columns]:
            stat_card(
                label=metric.get('label', ''),
                value=str(metric.get('value', 0)),
                icon=metric.get('icon', '📊'),
                variant=metric.get('variant', 'default'),
                delta=metric.get('delta')
            )

def daily_challenge_card(challenge_data: Dict[str, Any]):
    """Display today's daily challenge in an attractive card"""
    if not challenge_data:
        st.info("🎯 No daily challenge available")
        return

    difficulty_colors = {
        'Easy': 'success',
        'Medium': 'warning',
        'Hard': 'danger'
    }

    difficulty = challenge_data.get('difficulty', 'Medium')

    st.markdown(f"""
        <div class="glass-card glass-card-primary animate-scale-in">
            <h3 style="color: var(--primary); margin-bottom: 1rem;">🎯 Daily Challenge</h3>
            <h2 style="color: var(--text-primary); margin-bottom: 0.5rem;">{challenge_data.get('title', 'Unknown')}</h2>
            <div style="margin-bottom: 1rem;">
                {badge(difficulty, difficulty_colors.get(difficulty, 'info'))}
                {badge(f"Question #{challenge_data.get('questionId', '0')}", 'outline')}
            </div>
            <p style="color: var(--text-secondary); margin-bottom: 1rem;">
                Date: {challenge_data.get('date', 'Today')}
            </p>
        </div>
    """, unsafe_allow_html=True)

    if st.button("🚀 Solve Challenge", key="daily_challenge_btn", use_container_width=True):
        st.link_button("Open in LeetCode", challenge_data.get('link', 'https://leetcode.com'), use_container_width=True)
