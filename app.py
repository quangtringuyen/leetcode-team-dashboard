import streamlit as st
import json
from utils.leetcodeapi import fetch_user_data
import os
import pandas as pd
import plotly.express as px
from utils.auth import login, register, get_current_user

# Constants
DATA_PATH = "data/members.json"

# Load all teams/members data
def load_all_members():
    if not os.path.exists(DATA_PATH):
        return {}
    with open(DATA_PATH, "r") as f:
        return json.load(f)

# Save all teams/members data
def save_all_members(all_members):
    with open(DATA_PATH, "w") as f:
        json.dump(all_members, f, indent=4)

# Get current user's members
def load_members(user):
    all_members = load_all_members()
    return all_members.get(user, [])

def save_members(user, members):
    all_members = load_all_members()
    all_members[user] = members
    save_all_members(all_members)

# Fetch all members data
@st.cache_data
def fetch_all_data(members):
    data = []
    for member in members:
        user_data = fetch_user_data(member["username"])
        if user_data:
            user_data["name"] = member.get("name", member["username"])
            data.append(user_data)
    return data

# Streamlit page setup
st.set_page_config(
    layout="wide",
    page_title="LeetCode Team Dashboard",
    page_icon="📊"
)

# Dynamic theme-aware CSS
st.markdown("""
    <style>
    /* Use Streamlit theme variables for backgrounds and text */
    .stApp {
        background-color: var(--background-color) !important;
        color: var(--text-color) !important;
    }
    .header-title {
        color: #FFA116 !important;
        font-weight: 700;
        font-size: 2.5rem;
        padding-bottom: 0.5rem;
        border-bottom: 3px solid #FFA116;
        margin-bottom: 1.5rem;
        text-align: center;
    }
    .leetcode-card, .profile-header, .stat-card, .login-card {
        background: var(--secondary-background-color) !important;
        color: var(--text-color) !important;
        border-radius: 12px;
        border: 1px solid var(--block-border-color, #E0E0E0);
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .profile-header {
        background: linear-gradient(135deg, var(--secondary-background-color) 0%, var(--background-color) 100%);
        color: var(--text-color) !important;
    }
    .rank-badge {
        background: #FFA116;
        color: #fff;
        border-radius: 20px;
        padding: 4px 12px;
        font-weight: 600;
        display: inline-block;
        font-size: 0.9rem;
    }
    .solved-badge {
        background: #34A853;
        color: #fff;
        border-radius: 20px;
        padding: 4px 12px;
        font-weight: 600;
        display: inline-block;
        font-size: 0.9rem;
    }
    .leaderboard-item {
        transition: all 0.3s ease;
        border-radius: 8px;
        padding: 12px;
        margin-bottom: 8px;
        background: var(--secondary-background-color) !important;
        color: var(--text-color) !important;
        border: 1px solid var(--block-border-color, #E0E0E0);
        cursor: pointer;
    }
    .leaderboard-item:hover {
        background: var(--background-color) !important;
        transform: translateX(5px);
        box-shadow: 0 2px 8px rgba(0,0,0,0.15);
    }
    .leaderboard-item.selected {
        background: rgba(255, 161, 22, 0.15) !important;
        border-left: 4px solid #FFA116;
    }
    .stat-card {
        background: var(--secondary-background-color) !important;
        color: var(--text-color) !important;
        border-radius: 10px;
        padding: 1.2rem;
        text-align: center;
        flex: 1;
        min-width: 120px;
        border: 1px solid var(--block-border-color, #E0E0E0);
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        transition: transform 0.2s ease;
    }
    .stat-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.15);
    }
    .stat-value {
        font-size: 1.8rem;
        font-weight: 700;
        margin: 0.5rem 0;
        color: var(--text-color) !important;
    }
    .stat-label {
        color: var(--text-color) !important;
        font-size: 0.9rem;
        font-weight: 500;
    }
    .difficulty-easy { color: #34A853 !important; font-weight: 700; }
    .difficulty-medium { color: #FFA116 !important; font-weight: 700; }
    .difficulty-hard { color: #EF4743 !important; font-weight: 700; }
    .stMarkdown, .stText, .welcome-message {
        color: var(--text-color) !important;
    }
    .stButton > button {
        background-color: #FFA116 !important;
        color: #fff !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        padding: 8px 16px !important;
        transition: all 0.3s ease !important;
    }
    .stButton > button:hover {
        background-color: #e69115 !important;
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    .stTextInput > div > div > input,
    .stSelectbox > div > div > div {
        background-color: var(--secondary-background-color) !important;
        color: var(--text-color) !important;
        border: 1px solid var(--block-border-color, #E0E0E0) !important;
        border-radius: 8px !important;
    }
    .streamlit-expanderHeader,
    .streamlit-expanderContent {
        background-color: var(--secondary-background-color) !important;
        color: var(--text-color) !important;
        border: 1px solid var(--block-border-color, #E0E0E0) !important;
    }
    .stProgress > div > div > div {
        background-color: #FFA116 !important;
    }
    .welcome-message {
        color: var(--text-color) !important;
        font-size: 1.2rem;
        margin-bottom: 1rem;
    }
    .welcome-username {
        color: #34A853 !important;
        font-weight: 600;
    }
    .login-card {
        background: var(--secondary-background-color) !important;
        color: var(--text-color) !important;
        border-radius: 12px;
        border: 1px solid var(--block-border-color, #E0E0E0);
        padding: 2rem;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }
    .login-title {
        text-align: center;
        color: #FFA116 !important;
        margin-bottom: 2rem;
        font-size: 1.5rem;
        font-weight: 600;
    }
    /* Hide Streamlit elements */
    footer {visibility: hidden;}
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    @media (max-width: 768px) {
        .header-title { font-size: 2rem; }
        .stats-container { flex-direction: column; }
        .stat-card { min-width: 100%; }
    }
    </style>
""", unsafe_allow_html=True)

# --- Page Header ---
st.markdown('<div class="header-title">👨🏼‍💻 LeetCode Team Dashboard</div>', unsafe_allow_html=True)

# --- Authentication Section ---
if "user" not in st.session_state:
    st.session_state.user = None

if st.session_state.user is None:
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown('<div class="login-card">', unsafe_allow_html=True)
        st.markdown('<div class="login-title">🔐 Login or Register</div>', unsafe_allow_html=True)
        
        username = st.text_input("Username", placeholder="Enter your username")
        password = st.text_input("Password", type="password", placeholder="Enter your password")
        
        btn_col1, btn_col2 = st.columns([1, 1])
        login_clicked = btn_col1.button("🚀 Login", key="login_btn", use_container_width=True)
        register_clicked = btn_col2.button("📝 Register", key="register_btn", use_container_width=True)
        
        if login_clicked:
            if username and password:
                if login(username, password):
                    st.session_state.user = username
                    st.success("✅ Logged in successfully!")
                    st.rerun()
                else:
                    st.error("❌ Invalid credentials.")
            else:
                st.warning("⚠️ Please enter both username and password.")
                
        if register_clicked:
            if username and password:
                if register(username, password):
                    st.session_state.user = username
                    st.success("✅ Registered and logged in!")
                    st.rerun()
                else:
                    st.error("❌ Username already exists.")
            else:
                st.warning("⚠️ Please enter both username and password.")
        
        st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

user = st.session_state.user

# --- Welcome Message ---
st.markdown(
    f'<div class="welcome-message">👋 Welcome, <span class="welcome-username">{user}</span>!</div>',
    unsafe_allow_html=True
)

# --- Logout Button (Top Right) ---
top_cols = st.columns([8, 1])
with top_cols[1]:
    if st.button("🚪 Logout", key="logout_btn"):
        st.session_state.user = None
        st.session_state.selected_user = None
        st.rerun()

# Load member list for current user/team
members = load_members(user)
if not members:
    st.warning("⚠️ No members found for your team.")

# ➕➖ Add / Remove Members
with st.expander("📝 Manage Team Members", expanded=False):
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div class="leetcode-card">', unsafe_allow_html=True)
        st.markdown("### ➕ Add Member")
        new_name = st.text_input("Full Name", placeholder="Enter member's full name")
        new_username = st.text_input("LeetCode Username", placeholder="Enter LeetCode username")
        
        if st.button("➕ Add Member", key="add_member_btn", use_container_width=True):
            if not new_name or not new_username:
                st.warning("⚠️ Please enter both name and username")
            elif any(m["username"] == new_username for m in members):
                st.warning("⚠️ Member already exists.")
            else:
                with st.spinner("🔍 Verifying LeetCode user..."):
                    user_data = fetch_user_data(new_username)
                    if user_data:
                        members.append({"name": new_name, "username": new_username})
                        save_members(user, members)
                        st.success(f"✅ Member '{new_name}' added successfully!")
                        st.rerun()
                    else:
                        st.error("❌ User not found on LeetCode.")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="leetcode-card">', unsafe_allow_html=True)
        st.markdown("### ➖ Remove Member")
        name_to_username = {m["name"]: m["username"] for m in members}
        if name_to_username:
            selected_name = st.selectbox("Select a member to remove", list(name_to_username.keys()))
            if st.button("🗑️ Remove Member", key="remove_member_btn", use_container_width=True):
                selected_username = name_to_username[selected_name]
                members = [m for m in members if m["username"] != selected_username]
                save_members(user, members)
                st.success(f"✅ Member '{selected_name}' removed successfully!")
                st.rerun()
        else:
            st.info("ℹ️ No members to remove.")
        st.markdown('</div>', unsafe_allow_html=True)

# Stop if no members
if not members:
    st.stop()

# Fetch and process team data
with st.spinner("🔄 Fetching team data from LeetCode..."):
    data = fetch_all_data(members)
    
if not data:
    st.error("❌ Failed to fetch data for team members")
    st.stop()
    
df = pd.DataFrame(data)
df_sorted = df.sort_values(by="totalSolved", ascending=False)

# Layout: Leaderboard (left) | Profile (right)
left_col, right_col = st.columns([1, 2])

with left_col:
    st.markdown("### 🏆 Leaderboard")
    st.markdown('<div class="leetcode-card">', unsafe_allow_html=True)
    
    selected_user = st.session_state.get("selected_user", df_sorted.iloc[0]["username"])
    
    for i, row in enumerate(df_sorted.itertuples(), start=1):
        is_selected = (row.username == selected_user)
        item_class = "leaderboard-item selected" if is_selected else "leaderboard-item"
        
        st.markdown(f'<div class="{item_class}">', unsafe_allow_html=True)
        col1, col2 = st.columns([0.2, 0.8])
        with col1:
            st.image(row.avatar, width=40)
        with col2:
            if st.button(
                f"#{i} {row.name}",
                key=f"lb_{row.username}",
                use_container_width=True
            ):
                st.session_state.selected_user = row.username
                st.rerun()
            
            # Progress bar for problems solved
            max_problems = max(df['totalSolved'])
            progress = row.totalSolved / max_problems if max_problems > 0 else 0
            st.progress(progress, text=f"🎯 {row.totalSolved} problems solved")
            
        st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# Selected user logic
selected_data = next((item for item in data if item["username"] == selected_user), None)

with right_col:
    if selected_data:
        # Profile Header
        st.markdown(f"""
            <div class="profile-header">
                <div style="display:flex; align-items:center; gap: 20px;">
                    <img src="{selected_data['avatar']}" width="80" style="border-radius:50%; border: 3px solid var(--leetcode-orange);">
                    <div>
                        <h2 style="margin:0; color: var(--text-primary);">{selected_data['name']}</h2>
                        <div style="display:flex; gap:10px; margin-top:8px; flex-wrap: wrap;">
                            <div class="rank-badge">🏅 Rank: {selected_data['ranking']}</div>
                            <div class="solved-badge">✅ Solved: {selected_data['totalSolved']}</div>
                        </div>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        # Get difficulty counts
        def get_difficulty_count(difficulty):
            for d in selected_data["submissions"]:
                if d["difficulty"] == difficulty:
                    return d.get("count", 0)
            return 0
        
        easy_count = get_difficulty_count("Easy")
        medium_count = get_difficulty_count("Medium")
        hard_count = get_difficulty_count("Hard")
        
        # Stats Cards - Only 4 cards: Total, Easy, Medium, Hard
        st.markdown("### 📊 Problems Solved")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown(f"""
                <div class="stat-card">
                    <div class="stat-label">Total Solved</div>
                    <div class="stat-value">{selected_data['totalSolved']}</div>
                </div>
            """, unsafe_allow_html=True)
            
        with col2:
            st.markdown(f"""
                <div class="stat-card">
                    <div class="stat-label">Easy</div>
                    <div class="stat-value" style="color: var(--leetcode-green);">{easy_count}</div>
                </div>
            """, unsafe_allow_html=True)
            
        with col3:
            st.markdown(f"""
                <div class="stat-card">
                    <div class="stat-label">Medium</div>
                    <div class="stat-value" style="color: var(--leetcode-orange);">{medium_count}</div>
                </div>
            """, unsafe_allow_html=True)
            
        with col4:
            st.markdown(f"""
                <div class="stat-card">
                    <div class="stat-label">Hard</div>
                    <div class="stat-value" style="color: var(--leetcode-red);">{hard_count}</div>
                </div>
            """, unsafe_allow_html=True)
        
        # Difficulty Distribution
        st.markdown("### 🎯 Difficulty Distribution")
        if selected_data['totalSolved'] > 0:
            # Create data for pie chart
            diff_data = [
                {'difficulty': 'Easy', 'count': easy_count},
                {'difficulty': 'Medium', 'count': medium_count},
                {'difficulty': 'Hard', 'count': hard_count}
            ]
            
            # Filter out zero counts
            diff_data = [d for d in diff_data if d['count'] > 0]
            
            if diff_data:
                # Create pie chart with LeetCode colors
                fig = px.pie(
                    diff_data,
                    values='count',
                    names='difficulty',
                    color='difficulty',
                    color_discrete_map={
                        'Easy': '#34A853',
                        'Medium': '#FFA116',
                        'Hard': '#EF4743'
                    },
                    hole=0.4,
                )
                
                fig.update_layout(
                    showlegend=True,
                    margin=dict(l=20, r=20, t=30, b=0),
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=-0.2,
                        xanchor="center",
                        x=0.5,
                        font=dict(size=12)
                    ),
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(size=12)
                )
                
                fig.update_traces(
                    textposition='inside',
                    textinfo='percent+label',
                    hovertemplate="<b>%{label}</b><br>Solved: %{value}<br>Percentage: %{percent}",
                    textfont=dict(color='#FFFFFF', size=11)
                )
                
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("📊 No difficulty distribution data available.")
        else:
            st.info("🎯 No problems solved yet!")

# Bottom Section
st.divider()
st.markdown("### 📈 Team Performance")
st.markdown('<div class="leetcode-card">', unsafe_allow_html=True)

# Create bar chart with LeetCode colors
fig = px.bar(
    df_sorted,
    x='name',
    y='totalSolved',
    color='totalSolved',
    color_continuous_scale=[(0, "#FFA116"), (1, "#34A853")],
    text='totalSolved',
    labels={'name': 'Team Members', 'totalSolved': 'Problems Solved'},
    title="Team Members Performance Comparison"
)

fig.update_layout(
    xaxis_title="Team Members",
    yaxis_title="Problems Solved",
    plot_bgcolor='rgba(0,0,0,0)',
    paper_bgcolor='rgba(0,0,0,0)',
    margin=dict(l=20, r=20, t=50, b=20),
    xaxis=dict(tickangle=-45),
    showlegend=False,
    height=400,
    title=dict(
        font=dict(size=16),
        x=0.5,
        xanchor='center'
    )
)

fig.update_traces(
    texttemplate='%{text}',
    textposition='outside',
    marker_line_color='rgba(0,0,0,0.1)',
    marker_line_width=1,
    textfont=dict(size=12, color='#FFFFFF')
)

st.plotly_chart(fig, use_container_width=True)
st.markdown('</div>', unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown(
    '<div style="text-align: center; color: var(--text-secondary); font-size: 0.9rem; padding: 1rem 0;">'
    '🚀 Built with Streamlit  • 💻 Saralaufeyson • 📊 Team Dashboard'
    '</div>',
    unsafe_allow_html=True
)