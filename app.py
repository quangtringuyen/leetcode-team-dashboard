import streamlit as st
import json
from utils.leetcodeapi import fetch_user_data
import os
import pandas as pd
import matplotlib.pyplot as plt

# Constants
DATA_PATH = "data/members.json"

# Load Members
def load_members():
    if not os.path.exists(DATA_PATH):
        return []
    with open(DATA_PATH, "r") as f:
        return json.load(f)

# Save Members
def save_members(members):
    with open(DATA_PATH, "w") as f:
        json.dump(members, f, indent=4)

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

# Load member list
members = load_members()
if not members:
    st.warning("No members found in members.json")

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
                save_members(members)
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
            save_members(members)
            st.success(f"Member '{selected_name}' removed. Please refresh.")
    else:
        st.info("No members to remove.")

# Stop if no members
if not members:
    st.stop()

# Fetch and process team data
data = fetch_all_data(members)
df = pd.DataFrame(data)
df_sorted = df.sort_values(by="totalSolved", ascending=True)

# Layout: Leaderboard (left) | Profile (right)
left_col, right_col = st.columns([1, 2])

with left_col:
    st.subheader("🏅 Leaderboard")
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
        st.image(selected_data["avatar"], width=100)
        st.write(f"**Username:** {selected_data['username']}")
        st.write(f"**Ranking:** {selected_data['ranking']}")
        st.write(f"**Total Solved:** {selected_data['totalSolved']}")

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
bar_df = df_sorted[["name", "totalSolved"]].set_index("name")
st.bar_chart(bar_df)
