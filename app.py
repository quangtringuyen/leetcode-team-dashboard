import streamlit as st
import json
from utils.leetcodeapi import fetch_user_data
import os
import pandas as pd
import matplotlib.pyplot as plt
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
st.set_page_config(layout="wide")
st.title("👨🏼‍💻 LeetCode Stats of team")
# --- Custom CSS Styling ---
st.markdown("""
    <style>
    .main {background-color: #f7f9fa;}
    .stButton>button {background-color: #1a73e8; color: white; font-weight: bold; border-radius: 6px;}
    .stTextInput>div>input {border-radius: 6px;}
    .stSelectbox>div>div {border-radius: 6px;}
    .stExpander {background-color: #e3eafc;}
    .stSubheader {color: #1a73e8;}
    .stMarkdown {font-size: 1.1em;}
    .profile-box {background-color: #e3eafc; padding: 16px; border-radius: 12px;}
    </style>
""", unsafe_allow_html=True)
# --- Authentication Section ---
if "user" not in st.session_state:
    st.session_state.user = None

if st.session_state.user is None:
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown('<h2 style="text-align:center;color:#1a73e8;">Login or Register</h2>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns([2, 2, 2])
    with col2:
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        btn_col1, btn_col2 = st.columns([1, 1])
        login_clicked = btn_col1.button("Login")
        register_clicked = btn_col2.button("Register")
        if login_clicked:
            if login(username, password):
                st.session_state.user = username
                st.success("Logged in!,Ignore the error Please do click on Login again")
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
    st.stop()

user = st.session_state.user

# --- Logout Button (top right) ---
top_cols = st.columns([8, 1])
with top_cols[1]:
    if st.button("Logout"):
        st.session_state.user = None
        st.session_state.selected_user = None
        st.rerun()

# Load member list for current user/team
members = load_members(user)
if not members:
    st.warning("No members found for your team.")

# ➕➖ Add / Remove Members
with st.expander("➕➖ Manage Team Members"):
    st.markdown("### ➕ Add Member")
    new_name = st.text_input("Enter Full Name")
    new_username = st.text_input("Enter LeetCode Username")

    if st.button("Add Member"):
        if any(m["username"] == new_username for m in members):
            st.warning("Member already exists.")
        else:
            user_data = fetch_user_data(new_username)
            if user_data:
                members.append({"name": new_name, "username": new_username})
                save_members(user, members)
                st.success(f"Member '{new_name}' added successfully! Please refresh.")
            else:
                st.error("User not found on LeetCode.")

    st.markdown("### ➖ Remove Member")
    name_to_username = {m["name"]: m["username"] for m in members}
    if name_to_username:
        selected_name = st.selectbox("Select a member to remove", list(name_to_username.keys()))
        if st.button("Remove Member"):
            selected_username = name_to_username[selected_name]
            members = [m for m in members if m["username"] != selected_username]
            save_members(user, members)
            st.success(f"Member '{selected_name}' removed. Please refresh.")
    else:
        st.info("No members to remove.")

# Stop if no members
if not members:
    st.stop()

# Fetch and process team data
data = fetch_all_data(members)
df = pd.DataFrame(data)
df_sorted = df.sort_values(by="totalSolved", ascending=False)

# Layout: Leaderboard (left) | Profile (right)
left_col, right_col = st.columns([1, 2])

with left_col:
    st.subheader("🤖 Leaderboard")
    for i, row in enumerate(df_sorted.itertuples(), start=1):
        col1, col2 = st.columns([1, 3])
        with col1:
            st.image(row.avatar, width=40)
        with col2:
            if st.button(f"#{i} {row.name} ({row.totalSolved} 🧩)", key=row.username):
                st.session_state.selected_user = row.username

# Selected user logic
selected_user = st.session_state.get("selected_user", df_sorted.iloc[0]["username"])
selected_data = next((item for item in data if item["username"] == selected_user), None)

with right_col:
    if selected_data:
        st.subheader(f"👤 {selected_data['name']}'s Profile")
        # Create two columns for image and info
        img_col, info_col = st.columns([1, 3])
        with img_col:
            st.image(selected_data["avatar"], width=100)
        with info_col:
            st.markdown(
                f"""
                <div class="profile-box">
                    <span style="font-size:1.2em;font-weight:bold;color:#1a73e8;">Username:</span>
                    <span style="font-size:1.2em;font-weight:bold;">{selected_data['username']}</span><br>
                    <span style="font-size:1.2em;font-weight:bold;color:#e8711a;">Ranking:</span>
                    <span style="font-size:1.2em;font-weight:bold;">{selected_data['ranking']}</span><br>
                    <span style="font-size:1.4em;font-weight:bold;color:#34a853;">Total Solved:</span>
                    <span style="font-size:1.4em;font-weight:bold;">{selected_data['totalSolved']}</span>
                </div>
                """,
                unsafe_allow_html=True
            )

        st.markdown("### 🧩 Problems Solved by Difficulty")
        filtered_subs = [d for d in selected_data["submissions"] if d["difficulty"] in ["Easy", "Medium", "Hard"]]
        sub_df = pd.DataFrame(filtered_subs)

        fig, ax = plt.subplots()
        ax.pie(sub_df["count"], labels=sub_df["difficulty"], autopct='%1.1f%%', startangle=90)
        ax.axis("equal")
        st.pyplot(fig)


# Bottom Section
st.divider()
st.subheader("📈 Team Solving Trend")
bar_df = df_sorted[["name", "totalSolved"]].set_index("name").sort_values(by="totalSolved", ascending=False)
st.bar_chart(bar_df)
