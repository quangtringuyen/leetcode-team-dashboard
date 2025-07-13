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
    page_icon=":bar_chart:"
)

# --- LeetCode Dark Theme CSS ---
st.markdown("""
    <style>
    :root {
        --leetcode-dark: #121212;
        --leetcode-darker: #0A0A0A;
        --leetcode-orange: #FFA116;
        --leetcode-green: #34A853;
        --leetcode-red: #EF4743;
        --leetcode-blue: #1E88E5;
        --leetcode-text: #E0E0E0;
        --leetcode-text-light: #FFFFFF;
        --leetcode-card: #1E1E1E;
        --leetcode-card-border: #333333;
    }
    
    body {
        background-color: var(--leetcode-dark);
        color: var(--leetcode-text);
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    
    .stApp {
        background: var(--leetcode-dark);
    }
    
    .header-title {
        color: var(--leetcode-orange);
        font-weight: 700;
        font-size: 2.5rem;
        padding-bottom: 0.5rem;
        border-bottom: 3px solid var(--leetcode-orange);
        margin-bottom: 1.5rem;
    }
    
    .leetcode-btn {
        background-color: var(--leetcode-orange) !important;
        color: var(--leetcode-text-light) !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        padding: 8px 16px !important;
        transition: all 0.3s !important;
    }
    
    .leetcode-btn:hover {
        background-color: #e69115 !important;
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    
    .leetcode-card {
        background: var(--leetcode-card);
        border-radius: 12px;
        border: 1px solid var(--leetcode-card-border);
        padding: 1.5rem;
        margin-bottom: 1.5rem;
    }
    
    .profile-header {
        background: linear-gradient(135deg, #1A1A1A 0%, #2D2D2D 100%);
        border-radius: 12px;
        padding: 1.5rem;
        color: var(--leetcode-text-light);
        margin-bottom: 1.5rem;
        border: 1px solid var(--leetcode-card-border);
    }
    
    .rank-badge {
        background: var(--leetcode-orange);
        color: var(--leetcode-text-light);
        border-radius: 20px;
        padding: 4px 12px;
        font-weight: 600;
        display: inline-block;
    }
    
    .solved-badge {
        background: var(--leetcode-green);
        color: var(--leetcode-text-light);
        border-radius: 20px;
        padding: 4px 12px;
        font-weight: 600;
        display: inline-block;
    }
    
    .leetcode-tag {
        background: #2A3F54;
        color: var(--leetcode-blue);
        border-radius: 4px;
        padding: 2px 8px;
        font-size: 0.85rem;
        font-weight: 500;
        display: inline-block;
        margin-right: 6px;
        margin-bottom: 6px;
    }
    
    .difficulty-easy { color: var(--leetcode-green); font-weight: 700; }
    .difficulty-medium { color: var(--leetcode-orange); font-weight: 700; }
    .difficulty-hard { color: var(--leetcode-red); font-weight: 700; }
    
    .logout-btn {
        background: transparent !important;
        color: var(--leetcode-orange) !important;
        border: 2px solid var(--leetcode-orange) !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        padding: 6px 12px !important;
        transition: all 0.3s !important;
    }
    
    .logout-btn:hover {
        background: rgba(255, 161, 22, 0.1) !important;
        transform: translateY(-2px);
    }
    
    .leaderboard-item {
        transition: all 0.3s;
        border-radius: 8px;
        padding: 10px;
        margin-bottom: 8px;
        background: var(--leetcode-card);
        border: 1px solid var(--leetcode-card-border);
    }
    
    .leaderboard-item:hover {
        background: #2A2A2A;
        transform: translateX(5px);
    }
    
    .leaderboard-item.selected {
        background: rgba(255, 161, 22, 0.15);
        border-left: 3px solid var(--leetcode-orange);
    }
    
    .stats-container {
        display: flex;
        justify-content: space-between;
        flex-wrap: wrap;
        gap: 1rem;
        margin-bottom: 1.5rem;
    }
    
    .stat-card {
        background: #252525;
        border-radius: 10px;
        padding: 1rem;
        text-align: center;
        flex: 1;
        min-width: 120px;
        border: 1px solid var(--leetcode-card-border);
    }
    
    .stat-value {
        font-size: 1.8rem;
        font-weight: 700;
        margin: 0.5rem 0;
        color: var(--leetcode-text-light);
    }
    
    .stat-label {
        color: #A0A0A0;
        font-size: 0.9rem;
    }
    
    /* Override Streamlit components */
    .stTextInput>div>div>input {
        background: #252525 !important;
        color: var(--leetcode-text) !important;
        border: 1px solid #333 !important;
    }
    
    .stSelectbox>div>div>div>div {
        background: #252525 !important;
        color: var(--leetcode-text) !important;
        border: 1px solid #333 !important;
    }
    
    .stExpander {
        background: var(--leetcode-card) !important;
        border: 1px solid var(--leetcode-card-border) !important;
    }
    
    .stExpander label {
        color: var(--leetcode-text) !important;
        font-weight: 600 !important;
    }
    
    .stMarkdown, .stSubheader, .stText, .stAlert {
        color: var(--leetcode-text) !important;
    }
    
    /* Charts */
    .stProgress>div>div>div {
        background-color: var(--leetcode-orange) !important;
    }
    
    /* Hide footer and menu */
    footer {visibility: hidden;}
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# --- Page Header ---
st.markdown('<div class="header-title">👨🏼‍💻 LeetCode Team Dashboard</div>', unsafe_allow_html=True)

# --- Authentication Section ---
if "user" not in st.session_state:
    st.session_state.user = None

if st.session_state.user is None:
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown('<h2 style="text-align:center;color:#FFA116;margin-bottom:2rem;">Login or Register</h2>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.container():
            st.markdown('<div class="leetcode-card">', unsafe_allow_html=True)
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            btn_col1, btn_col2 = st.columns([1, 1])
            login_clicked = btn_col1.button("Login", key="login_btn")
            register_clicked = btn_col2.button("Register", key="register_btn")
            
            if login_clicked:
                if login(username, password):
                    st.session_state.user = username
                    st.success("Logged in successfully!")
                    st.rerun()
                else:
                    st.error("Invalid credentials.")
                    
            if register_clicked:
                if register(username, password):
                    st.session_state.user = username
                    st.success("Registered and logged in!")
                    st.rerun()
                else:
                    st.error("Username already exists.")
            st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

user = st.session_state.user

# --- Logout Button (Top Right) ---
top_cols = st.columns([8, 1])
with top_cols[1]:
    if st.button("Logout", key="logout_btn"):
        st.session_state.user = None
        st.session_state.selected_user = None
        st.rerun()

# Load member list for current user/team
members = load_members(user)
if not members:
    st.warning("No members found for your team.")

# ➕➖ Add / Remove Members
with st.expander("📝 Manage Team Members", expanded=False):
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div class="leetcode-card">', unsafe_allow_html=True)
        st.markdown("### ➕ Add Member")
        new_name = st.text_input("Full Name")
        new_username = st.text_input("LeetCode Username")
        
        if st.button("Add Member", key="add_member_btn"):
            if not new_name or not new_username:
                st.warning("Please enter both name and username")
            elif any(m["username"] == new_username for m in members):
                st.warning("Member already exists.")
            else:
                user_data = fetch_user_data(new_username)
                if user_data:
                    members.append({"name": new_name, "username": new_username})
                    save_members(user, members)
                    st.success(f"Member '{new_name}' added successfully!")
                else:
                    st.error("User not found on LeetCode.")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="leetcode-card">', unsafe_allow_html=True)
        st.markdown("### ➖ Remove Member")
        name_to_username = {m["name"]: m["username"] for m in members}
        if name_to_username:
            selected_name = st.selectbox("Select a member to remove", list(name_to_username.keys()))
            if st.button("Remove Member", key="remove_member_btn"):
                selected_username = name_to_username[selected_name]
                members = [m for m in members if m["username"] != selected_username]
                save_members(user, members)
                st.success(f"Member '{selected_name}' removed successfully!")
        else:
            st.info("No members to remove.")
        st.markdown('</div>', unsafe_allow_html=True)

# Stop if no members
if not members:
    st.stop()

# Fetch and process team data
with st.spinner("Fetching team data from LeetCode..."):
    data = fetch_all_data(members)
    
if not data:
    st.error("Failed to fetch data for team members")
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
            st.progress(progress, text=f"{row.totalSolved} problems solved")
            
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
                    <img src="{selected_data['avatar']}" width="80" style="border-radius:50%;">
                    <div>
                        <h2 style="margin:0;">{selected_data['name']}</h2>
                        <div style="display:flex; gap:10px; margin-top:8px;">
                            <div class="rank-badge">Rank: {selected_data['ranking']}</div>
                            <div class="solved-badge">Solved: {selected_data['totalSolved']}</div>
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
            st.markdown("""
                <div class="stat-card">
                    <div class="stat-label">Total Solved</div>
                    <div class="stat-value">{totalSolved}</div>
                </div>
            """.format(totalSolved=selected_data['totalSolved']), unsafe_allow_html=True)
            
        with col2:
            st.markdown(f"""
                <div class="stat-card">
                    <div class="stat-label">Easy</div>
                    <div class="stat-value" style="color:#34A853;">{easy_count}</div>
                </div>
            """, unsafe_allow_html=True)
            
        with col3:
            st.markdown(f"""
                <div class="stat-card">
                    <div class="stat-label">Medium</div>
                    <div class="stat-value" style="color:#FFA116;">{medium_count}</div>
                </div>
            """, unsafe_allow_html=True)
            
        with col4:
            st.markdown(f"""
                <div class="stat-card">
                    <div class="stat-label">Hard</div>
                    <div class="stat-value" style="color:#EF4743;">{hard_count}</div>
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
                    x=0.5
                ),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#E0E0E0')
            )
            
            fig.update_traces(
                textposition='inside',
                textinfo='percent+label',
                hovertemplate="<b>%{label}</b><br>Solved: %{value}",
                textfont=dict(color='#FFFFFF')
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No problems solved yet!")

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
    labels={'name': 'Member', 'totalSolved': 'Problems Solved'}
)

fig.update_layout(
    xaxis_title="Team Members",
    yaxis_title="Problems Solved",
    plot_bgcolor='rgba(0,0,0,0)',
    paper_bgcolor='rgba(0,0,0,0)',
    margin=dict(l=20, r=20, t=30, b=20),
    xaxis=dict(tickangle=-45, color='#E0E0E0'),
    yaxis=dict(color='#E0E0E0'),
    showlegend=False,
    height=400,
    font=dict(color='#E0E0E0')
)

fig.update_traces(
    texttemplate='%{text}',
    textposition='outside',
    marker_line_color='rgba(0,0,0,0.1)',
    marker_line_width=1,
    textfont=dict(color='#FFFFFF')
)

st.plotly_chart(fig, use_container_width=True)
st.markdown('</div>', unsafe_allow_html=True)