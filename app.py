import streamlit as st
import json
import os
from utils.leetcodeapi import fetch_user_data
from utils.auth import login

MEMBER_FILE = "data/members.json"

# Load/save member list
def load_members():
    if os.path.exists(MEMBER_FILE):
        with open(MEMBER_FILE, "r") as f:
            return json.load(f)
    return []

def save_members(members):
    with open(MEMBER_FILE, "w") as f:
        json.dump(members, f, indent=2)

# Login check
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("🔐 Login")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if login(email, password):
            st.session_state.logged_in = True
            st.success("Logged in!")
            st.rerun()
        else:
            st.error("Invalid credentials")
    st.stop()

# Load members from file on first run
if "members" not in st.session_state:
    st.session_state.members = load_members()

# Sidebar: Add new member
st.sidebar.header("👥 Team Settings")
new_username = st.sidebar.text_input("Add LeetCode Username")
new_name = st.sidebar.text_input("Member Name")

if st.sidebar.button("Add Member"):
    if not new_username or not new_name:
        st.sidebar.warning("Both fields are required.")
    elif any(m["username"].lower() == new_username.lower() for m in st.session_state.members):
        st.sidebar.warning("Username already exists.")
    else:
        new_member = {"username": new_username, "name": new_name}
        st.session_state.members.append(new_member)
        save_members(st.session_state.members)
        st.sidebar.success("Member added successfully!")
        st.rerun()

# Main dashboard
st.title("📊 Team LeetCode Dashboard")

data = []
for member in st.session_state.members:
    try:
        user_data = fetch_user_data(member["username"])
        stats = user_data["stats"]

        data.append({
            "username": member["username"],
            "name": user_data["real_name"] or member["name"],
            "avatar": user_data["avatar"],
            "ranking": user_data["ranking"],
            "easy": stats.get("Easy", 0),
            "medium": stats.get("Medium", 0),
            "hard": stats.get("Hard", 0),
            "total": stats.get("Total", 0),
            "submission_history": user_data["submission_history"]
        })
    except Exception as e:
        st.error(f"Error fetching data for {member['username']}: {str(e)}")

# 🏆 Leaderboard
st.subheader("🏆 Leaderboard")
data_sorted = sorted(data, key=lambda x: x['total'], reverse=True)

for i, d in enumerate(data_sorted):
    cols = st.columns([1, 1, 4, 2])
    cols[0].markdown(f"**#{i+1}**")
    cols[1].image(d["avatar"], width=50)
    cols[2].markdown(f"**{d['name']}** (`{d['username']}`)")
    cols[3].markdown(f"✅ **{d['total']}** accepted submissions • 🌍 Rank: {d['ranking']}")

# ⚔️ Compare Two Members
st.subheader("⚔️ Compare Two Members")
if len(data) >= 2:
    usernames = [m["username"] for m in st.session_state.members]
    col1, col2 = st.columns(2)
    member1 = col1.selectbox("Member 1", usernames, key="m1")
    member2 = col2.selectbox("Member 2", usernames, key="m2")

    if member1 and member2 and member1 != member2:
        u1 = next(x for x in data if x["username"] == member1)
        u2 = next(x for x in data if x["username"] == member2)

        st.markdown("### 📊 Comparison")
        c1, c2 = st.columns(2)
        c1.image(u1["avatar"], width=60)
        c2.image(u2["avatar"], width=60)
        c1.metric("Total Solved", u1["total"])
        c2.metric("Total Solved", u2["total"])
        c1.metric("Easy", u1["easy"])
        c2.metric("Easy", u2["easy"])
        c1.metric("Medium", u1["medium"])
        c2.metric("Medium", u2["medium"])
        c1.metric("Hard", u1["hard"])
        c2.metric("Hard", u2["hard"])
        c1.metric("Global Rank", u1["ranking"])
        c2.metric("Global Rank", u2["ranking"])
