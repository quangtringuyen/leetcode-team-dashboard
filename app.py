import streamlit as st
import json
import os
import time
from datetime import date, timedelta

import pandas as pd
import plotly.express as px

from utils.leetcodeapi import fetch_user_data
from utils.auth import login, register

# -----------------------------
# Constants & paths
# -----------------------------
DATA_PATH = "data/members.json"
HISTORY_PATH = "data/history.json"  # weekly snapshots

# -----------------------------
# Persistence: members
# -----------------------------
def load_all_members():
    if not os.path.exists(DATA_PATH):
        return {}
    with open(DATA_PATH, "r") as f:
        return json.load(f)

def save_all_members(all_members):
    os.makedirs(os.path.dirname(DATA_PATH), exist_ok=True)
    with open(DATA_PATH, "w") as f:
        json.dump(all_members, f, indent=4)

def load_members(user):
    all_members = load_all_members()
    return all_members.get(user, [])

def save_members(user, members):
    all_members = load_all_members()
    all_members[user] = members
    save_all_members(all_members)

# -----------------------------
# Persistence: history (weekly)
# -----------------------------
def load_history():
    if not os.path.exists(HISTORY_PATH):
        return {}
    with open(HISTORY_PATH, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}

def save_history(history):
    os.makedirs(os.path.dirname(HISTORY_PATH), exist_ok=True)
    with open(HISTORY_PATH, "w") as f:
        json.dump(history, f, indent=4)

def iso_week_start(d: date) -> date:
    """Return Monday (ISO week start) for a given date."""
    return d - timedelta(days=d.weekday())

def record_weekly_snapshots(team_owner: str, team_data: list, when: date | None = None):
    """
    Append a weekly snapshot per member if not already recorded this week.
    Snapshot fields:
      week_start, username, name, totalSolved(AC), Easy, Medium, Hard
    Stored under history[team_owner][username] = [snapshots...]
    """
    history = load_history()
    if team_owner not in history:
        history[team_owner] = {}

    the_date = when or date.today()
    week_start_str = iso_week_start(the_date).isoformat()
    changed = False

    for member in team_data:
        username = member["username"]
        name = member.get("name", username)
        total = int(member.get("totalSolved", 0))  # total accepted (as reported by API)

        easy = medium = hard = 0
        for s in member.get("submissions", []):
            if s.get("difficulty") == "Easy":
                easy = int(s.get("count", 0))
            elif s.get("difficulty") == "Medium":
                medium = int(s.get("count", 0))
            elif s.get("difficulty") == "Hard":
                hard = int(s.get("count", 0))

        if username not in history[team_owner]:
            history[team_owner][username] = []

        user_hist = history[team_owner][username]
        if not any(snap.get("week_start") == week_start_str for snap in user_hist):
            user_hist.append({
                "week_start": week_start_str,
                "username": username,
                "name": name,
                "totalSolved": total,  # reference only; charts use E+M+H sum
                "Easy": easy,
                "Medium": medium,
                "Hard": hard,
            })
            changed = True

    if changed:
        save_history(history)

    return history

# -----------------------------
# Cache busting
# -----------------------------
def bump_cache_buster():
    st.session_state.cache_buster = time.time()

# -----------------------------
# Fetch all members data (cached)
# -----------------------------
@st.cache_data(show_spinner=False)
def fetch_all_data(members, cache_key: float = 0.0):
    """
    cache_key is unused in logic, but included solely to control Streamlit caching.
    Change cache_key to force a refetch.
    """
    data = []
    for member in members:
        user_data = fetch_user_data(member["username"])
        if user_data:
            user_data["name"] = member.get("name", member["username"])
            user_data["username"] = member["username"]  # ensure username present
            data.append(user_data)
    return data

# -----------------------------
# Helpers
# -----------------------------
def sum_accepted_from_submissions(subs):
    if not isinstance(subs, list):
        return 0
    return sum(int(item.get("count", 0)) for item in subs
               if item.get("difficulty") in ("Easy", "Medium", "Hard"))

# -----------------------------
# Streamlit page setup & CSS
# -----------------------------
st.set_page_config(layout="wide", page_title="LeetCode Team Dashboard", page_icon="📊")

st.markdown("""
    <style>
    :root {
        --leetcode-orange: #FFA116;
        --leetcode-green: #34A853;
        --leetcode-red: #EF4743;
        --leetcode-blue: #1E88E5;
    }
    [data-theme="dark"] {
        --bg-primary: #0E1117; --bg-secondary: #262730; --bg-card: #1E1E1E;
        --text-primary: #FAFAFA; --text-secondary: #A0A0A0; --border-color: #333333; --hover-bg: #2A2A2A;
    }
    [data-theme="light"] {
        --bg-primary: #FFFFFF; --bg-secondary: #F0F2F6; --bg-card: #FFFFFF;
        --text-primary: #262730; --text-secondary: #6C757D; --border-color: #E0E0E0; --hover-bg: #F8F9FA;
    }
    .stApp { background-color: var(--bg-primary) !important; }
    .main .block-container { padding-top: 2rem; padding-bottom: 2rem; }
    .header-title { color: var(--leetcode-orange) !important; font-weight: 700; font-size: 2.5rem; padding-bottom: .5rem; border-bottom: 3px solid #FFA116; margin-bottom: 1.5rem; text-align: center; }
    .leetcode-card { background: var(--bg-card) !important; border-radius: 12px; border: 1px solid var(--border-color); padding: 1.5rem; margin-bottom: 1.5rem; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
    .profile-header { background: linear-gradient(135deg, var(--bg-card) 0%, var(--bg-secondary) 100%); border-radius: 12px; padding: 1.5rem; color: var(--text-primary); margin-bottom: 1.5rem; border: 1px solid var(--border-color); box-shadow: 0 4px 8px rgba(0,0,0,0.1); }
    .rank-badge { background: var(--leetcode-orange); color: #fff; border-radius: 20px; padding: 4px 12px; font-weight: 600; display: inline-block; font-size: .9rem; }
    .solved-badge { background: var(--leetcode-green); color: #fff; border-radius: 20px; padding: 4px 12px; font-weight: 600; display: inline-block; font-size: .9rem; }
    .leaderboard-item { transition: all .3s ease; border-radius: 8px; padding: 12px; margin-bottom: 8px; background: var(--bg-card); border: 1px solid var(--border-color); cursor: pointer; }
    .leaderboard-item:hover { background: var(--hover-bg); transform: translateX(5px); box-shadow: 0 2px 8px rgba(0,0,0,0.15); }
    .leaderboard-item.selected { background: rgba(255, 161, 22, .15); border-left: 4px solid var(--leetcode-orange); }
    .stat-card { background: var(--bg-card); border-radius: 10px; padding: 1.2rem; text-align: center; flex: 1; min-width: 120px; border: 1px solid var(--border-color); box-shadow: 0 2px 4px rgba(0,0,0,0.05); transition: transform .2s ease; }
    .stat-value { font-size: 1.8rem; font-weight: 700; margin: .5rem 0; color: var(--text-primary); }
    .stat-label { color: var(--text-secondary); font-size: .9rem; font-weight: 500; }
    .stProgress > div > div > div { background-color: var(--leetcode-orange) !important; }
    footer {visibility: hidden;} #MainMenu {visibility: hidden;} header {visibility: hidden;}
    @media (max-width: 768px) { .header-title { font-size: 2rem; } .stat-card { min-width: 100%; } }
    </style>
""", unsafe_allow_html=True)

# --- Page Header ---
st.markdown('<div class="header-title">👨🏼‍💻 LeetCode Team Dashboard</div>', unsafe_allow_html=True)

# --- Authentication & session state ---
if "user" not in st.session_state:
    st.session_state.user = None
if "cache_buster" not in st.session_state:
    st.session_state.cache_buster = 0.0

if st.session_state.user is None:
    st.markdown("<br><br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.markdown('<div class="leetcode-card">', unsafe_allow_html=True)
        st.markdown('<h3 style="text-align:center;color:#FFA116;margin-top:0">🔐 Login or Register</h3>', unsafe_allow_html=True)
        username = st.text_input("Username", placeholder="Enter your username")
        password = st.text_input("Password", type="password", placeholder="Enter your password")
        b1, b2 = st.columns(2)
        if b1.button("🚀 Login", use_container_width=True):
            if username and password and login(username, password):
                st.session_state.user = username
                bump_cache_buster()
                st.success("✅ Logged in successfully!")
                st.rerun()
            else:
                st.error("❌ Invalid credentials or missing input.")
        if b2.button("📝 Register", use_container_width=True):
            if username and password and register(username, password):
                st.session_state.user = username
                bump_cache_buster()
                st.success("✅ Registered and logged in!")
                st.rerun()
            else:
                st.error("❌ Username exists or missing input.")
        st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

user = st.session_state.user

st.write(f"👋 **Welcome, _{user}_!**")

# --- Top controls: refresh, snapshot, logout ---
tc = st.columns([6, 1.2, 1.2, 1.2])
with tc[1]:
    if st.button("🔄 Refresh data"):
        bump_cache_buster()
        st.toast("Refreshing team data…")
        st.rerun()
with tc[2]:
    if st.button("🗂️ Record snapshot now"):
        bump_cache_buster()
        st.session_state.force_snapshot = True
        st.rerun()
with tc[3]:
    if st.button("🚪 Logout"):
        st.session_state.user = None
        st.session_state.selected_user = None
        st.rerun()

# --- Load members ---
members = load_members(user)
if not members:
    st.warning("⚠️ No members found for your team.")

# --- Fetch & (idempotently) record weekly snapshot ---
with st.spinner("🔄 Fetching team data from LeetCode..."):
    data = fetch_all_data(members, cache_key=st.session_state.cache_buster)

if not data:
    st.error("❌ Failed to fetch data for team members")
    st.stop()

force_snapshot = st.session_state.pop("force_snapshot", False) if "force_snapshot" in st.session_state else False
history = record_weekly_snapshots(user, data)  # idempotent per week
if force_snapshot:
    history = record_weekly_snapshots(user, data)

# -----------------------------
# DataFrame + Accepted column (Easy+Medium+Hard)
# -----------------------------
df = pd.DataFrame(data)
df["Accepted"] = df["submissions"].apply(sum_accepted_from_submissions)
df_sorted = df.sort_values(by="Accepted", ascending=False)

# -----------------------------
# Leaderboard & profile
# -----------------------------
left_col, right_col = st.columns([1, 2])
with left_col:
    st.markdown("### 🏆 Leaderboard")
    st.markdown('<div class="leetcode-card">', unsafe_allow_html=True)

    selected_user_un = st.session_state.get("selected_user", df_sorted.iloc[0]["username"])
    max_ac = int(df["Accepted"].max()) if not df.empty else 0

    for i, row in enumerate(df_sorted.itertuples(index=False), start=1):
        is_selected = (row.username == selected_user_un)
        item_class = "leaderboard-item selected" if is_selected else "leaderboard-item"
        st.markdown(f'<div class="{item_class}">', unsafe_allow_html=True)
        c1, c2 = st.columns([0.2, 0.8])
        with c1:
            st.image(row.avatar, width=40)
        with c2:
            if st.button(f"#{i} {row.name}", key=f"lb_{row.username}", use_container_width=True):
                st.session_state.selected_user = row.username
                st.rerun()
            progress = (row.Accepted / max_ac) if max_ac > 0 else 0
            st.progress(progress, text=f"🎯 {row.Accepted} Accepted")
        st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

selected_data = next((item for item in data if item["username"] == selected_user_un), None)

with right_col:
    if selected_data:
        sel_accepted = sum_accepted_from_submissions(selected_data.get("submissions", []))

        st.markdown(f"""
            <div class="profile-header">
                <div style="display:flex; align-items:center; gap: 20px;">
                    <img src="{selected_data['avatar']}" width="80" style="border-radius:50%; border: 3px solid var(--leetcode-orange);">
                    <div>
                        <h2 style="margin:0;">{selected_data['name']}</h2>
                        <div style="display:flex; gap:10px; margin-top:8px; flex-wrap: wrap;">
                            <div class="rank-badge">🏅 Rank: {selected_data['ranking']}</div>
                            <div class="solved-badge">✅ Accepted (Total): {sel_accepted}</div>
                        </div>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)

        def diff_count(diff):
            for d in selected_data["submissions"]:
                if d["difficulty"] == diff:
                    return d.get("count", 0)
            return 0

        easy_c = diff_count("Easy")
        med_c = diff_count("Medium")
        hard_c = diff_count("Hard")

        st.markdown("### 📊 Accepted by Difficulty")
        c1, c2, c3, c4 = st.columns(4)
        with c1: st.markdown(f'<div class="stat-card"><div class="stat-label">Accepted (Total)</div><div class="stat-value">{sel_accepted}</div></div>', unsafe_allow_html=True)
        with c2: st.markdown(f'<div class="stat-card"><div class="stat-label">Easy</div><div class="stat-value" style="color:#34A853">{easy_c}</div></div>', unsafe_allow_html=True)
        with c3: st.markdown(f'<div class="stat-card"><div class="stat-label">Medium</div><div class="stat-value" style="color:#FFA116">{med_c}</div></div>', unsafe_allow_html=True)
        with c4: st.markdown(f'<div class="stat-card"><div class="stat-label">Hard</div><div class="stat-value" style="color:#EF4743">{hard_c}</div></div>', unsafe_allow_html=True)

        if sel_accepted > 0:
            fig = px.pie(
                [{"difficulty":"Easy","count":easy_c},{"difficulty":"Medium","count":med_c},{"difficulty":"Hard","count":hard_c}],
                values="count", names="difficulty",
                color="difficulty",
                color_discrete_map={'Easy': '#34A853', 'Medium': '#FFA116', 'Hard': '#EF4743'},
                hole=0.4,
            )
            fig.update_layout(
                height=520,  # bigger donut
                showlegend=True, margin=dict(l=20, r=20, t=30, b=0),
                legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5, font=dict(size=13)),
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(size=13)
            )
            fig.update_traces(
                textposition='inside',
                textinfo='percent+label',
                hovertemplate="<b>%{label}</b><br>Accepted: %{value}<br>Percentage: %{percent}",
                textfont=dict(color='#FFFFFF', size=13)
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("🎯 No accepted challenges yet!")

# -----------------------------
# 📅 Weekly Progress (since September) — full roster & clamped date
# -----------------------------
st.divider()
st.markdown("### 📅 Weekly Progress (since September)")

raw_hist = load_history()
team_hist = raw_hist.get(user, {})

# 🔧 If history is empty or a member is missing, initialize/repair now
known_unames = set(team_hist.keys())
current_unames = {m["username"] for m in members}
if not team_hist or (current_unames - known_unames):
    try:
        # 'data' is the current fetch result; ensure usernames/names
        record_weekly_snapshots(user, data)
        raw_hist = load_history()
        team_hist = raw_hist.get(user, {})
    except Exception:
        pass  # render continues with roster-backed grid anyway

# Roster map (ensures people with no history appear)
member_name_by_username = {m["username"]: m.get("name", m["username"]) for m in members}
all_member_names = sorted(member_name_by_username.values())

if not team_hist:
    st.info("No weekly snapshots yet. Use **Refresh data** or **Record snapshot now** to create the first one.")
else:
    # Flatten snapshots
    rows = []
    for uname, snaps in team_hist.items():
        for s in snaps:
            rows.append({
                "username": uname,
                "name": member_name_by_username.get(uname, s.get("name", uname)),
                "week_start": s.get("week_start"),
                "Easy": int(s.get("Easy", 0)),
                "Medium": int(s.get("Medium", 0)),
                "Hard": int(s.get("Hard", 0)),
            })
    hist_df = pd.DataFrame(rows)

    if hist_df.empty:
        st.info("No weekly snapshots yet for any member. Once you record a snapshot, progress will appear here.")
    else:
        # Parse & sort, and build Accepted = Easy + Medium + Hard
        hist_df["week_start"] = pd.to_datetime(hist_df["week_start"])
        hist_df.sort_values(["username", "week_start"], inplace=True)
        hist_df["Accepted"] = hist_df["Easy"] + hist_df["Medium"] + hist_df["Hard"]

        # Controls (clamp default date to [min, max])
        this_year = date.today().year
        proposed_start = iso_week_start(date(this_year, 9, 1))
        min_date = hist_df["week_start"].min().date()
        max_date = hist_df["week_start"].max().date()

        def clamp(d: date, lo: date, hi: date) -> date:
            if d < lo: return lo
            if d > hi: return hi
            return d

        default_start = clamp(proposed_start, min_date, max_date)

        cc = st.columns([2, 2, 2, 2])
        with cc[0]:
            metric = st.selectbox("Chart metric", ["Accepted", "Easy", "Medium", "Hard"], index=0)
        with cc[1]:
            start_date = st.date_input("From week starting", value=default_start, min_value=min_date, max_value=max_date)
        with cc[2]:
            selected_people = st.multiselect("Members", options=all_member_names, default=all_member_names)
        with cc[3]:
            show_deltas = st.checkbox("Show Week-over-Week Changes (Accepted)", value=True)

        # Filter by start date
        f_hist = hist_df[hist_df["week_start"] >= pd.Timestamp(start_date)].copy()
        if f_hist.empty:
            st.info("No data for the selected start date yet.")
        else:
            # Build weekly grid (Mon) and full roster projection
            start_monday = pd.Timestamp(start_date) - pd.Timedelta(days=pd.Timestamp(start_date).weekday())
            end_monday = f_hist["week_start"].max()
            weeks = pd.date_range(start=start_monday, end=end_monday, freq="W-MON")
            full_index = pd.MultiIndex.from_product([selected_people, weeks], names=["name", "week_start"])

            # --- Cumulative chart for chosen metric (with ffill & zeros) ---
            chart_df = f_hist[["name", "week_start", metric]].set_index(["name", "week_start"]).sort_index()
            chart_df = chart_df.reindex(full_index)
            chart_df = chart_df.groupby(level=0)[metric].ffill().fillna(0.0).to_frame("value").reset_index()

            fig = px.line(
                chart_df, x="week_start", y="value", color="name", markers=True,
                labels={"week_start": "Week Start", "value": metric, "name": "Member"},
                title=f"Weekly {metric} Progress (Cumulative)"
            )
            fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                              margin=dict(l=20, r=20, t=50, b=20), height=420)
            st.plotly_chart(fig, use_container_width=True)

            # --- Week-over-Week Changes (ALWAYS on Accepted = E+M+H) ---
            if show_deltas:
                ac_df = f_hist[["name", "week_start", "Accepted"]].set_index(["name", "week_start"]).sort_index()
                ac_df = ac_df.reindex(full_index)
                ac_df = ac_df.groupby(level=0)["Accepted"].ffill().fillna(0.0).to_frame("Accepted").reset_index()

                # Rank by week (1 = best)
                ac_df_sorted = ac_df.sort_values(["week_start", "Accepted"], ascending=[True, False])
                ac_df_sorted["rank"] = ac_df_sorted.groupby("week_start")["Accepted"].rank(method="min", ascending=False)

                # Prev week values
                ac_df_sorted["prev_total"] = ac_df_sorted.groupby("name")["Accepted"].shift(1)
                ac_df_sorted["prev_rank"] = ac_df_sorted.groupby("name")["rank"].shift(1)

                ac_df_sorted["delta"] = ac_df_sorted["Accepted"] - ac_df_sorted["prev_total"]
                ac_df_sorted["pct_change"] = (ac_df_sorted["delta"] / ac_df_sorted["prev_total"].replace(0, pd.NA)) * 100
                ac_df_sorted["rank_delta"] = ac_df_sorted["prev_rank"] - ac_df_sorted["rank"]

                # Keep only rows where there is a previous week to compare
                deltas = ac_df_sorted.dropna(subset=["prev_total"]).copy()

                # Pretty columns
                deltas["week_start"] = pd.to_datetime(deltas["week_start"]).dt.date

                def arrowize(x):
                    if pd.isna(x) or x == 0: return "➖ 0"
                    return f"🔼 {int(x)}" if x > 0 else f"🔽 {int(x)}"

                def pctfmt(x):
                    if pd.isna(x): return "—"
                    sign = "+" if x >= 0 else ""
                    return f"{sign}{x:.1f}%"

                def rankfmt(x):
                    if pd.isna(x) or x == 0: return "—"
                    arrow = "⬆️" if x > 0 else "⬇️"
                    return f"{arrow} {int(abs(x))}"

                out = deltas[["week_start", "name", "prev_total", "Accepted", "delta", "pct_change", "prev_rank", "rank", "rank_delta"]].copy()
                out = out.rename(columns={
                    "prev_total": "Prev (Accepted)",
                    "Accepted": "Accepted",
                    "delta": "Δ Accepted",
                    "pct_change": "% Change",
                    "prev_rank": "Prev Rank",
                    "rank": "Rank",
                    "rank_delta": "Δ Rank"
                })
                # Stringify indicators
                out["Δ Accepted"] = out["Δ Accepted"].apply(arrowize)
                out["% Change"] = out["% Change"].apply(pctfmt)
                out["Δ Rank"] = out["Δ Rank"].apply(rankfmt)
                out = out.sort_values(["week_start", "Rank", "name"])

                st.markdown("#### Week-over-Week Changes (Accepted challenges)")
                st.dataframe(out, use_container_width=True)

                # “Top gainers” in the latest completed week
                latest_week = deltas["week_start"].max()
                latest = deltas[deltas["week_start"] == latest_week].copy()
                if not latest.empty:
                    latest["gain"] = latest["delta"]  # numeric
                    top = latest.sort_values("gain", ascending=False).head(3).reset_index(drop=True)

                    medals = []
                    if len(top) >= 1:
                        medals.append(f"🥇 {top.iloc[0]['name']}: +{int(top.iloc[0]['gain'])}")
                    if len(top) >= 2:
                        medals.append(f"🥈 {top.iloc[1]['name']}: +{int(top.iloc[1]['gain'])}")
                    if len(top) >= 3:
                        medals.append(f"🥉 {top.iloc[2]['name']}: +{int(top.iloc[2]['gain'])}")

                    if medals:
                        st.caption(f"**Top gainers — week of {latest_week}**: " + "  •  ".join(medals))

        # Let user know who has no snapshots yet
        names_with_hist = sorted(hist_df["name"].unique().tolist())
        missing_hist = sorted(set(all_member_names) - set(names_with_hist))
        if missing_hist:
            st.caption("ℹ️ No snapshots yet for: " + ", ".join(missing_hist) + ". They show as a flat 0 line until recorded.")

# -----------------------------
# 📈 Team Performance (Accepted challenges)
# -----------------------------
st.divider()
st.markdown("### 📈 Team Performance (Accepted challenges)")
st.markdown('<div class="leetcode-card">', unsafe_allow_html=True)

perf_df = df[["name", "Accepted"]].sort_values(by="Accepted", ascending=False)

fig = px.bar(
    perf_df,
    x="name",
    y="Accepted",
    color="Accepted",
    color_continuous_scale=[(0, "#FFA116"), (1, "#34A853")],
    text="Accepted",
    labels={"name": "Team Members", "Accepted": "Accepted Challenges"},
    title="Team Members — Total Accepted Challenges (Easy + Medium + Hard)"
)
fig.update_layout(
    xaxis_title="Team Members",
    yaxis_title="Accepted Challenges",
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    margin=dict(l=20, r=20, t=50, b=20),
    xaxis=dict(tickangle=-45),
    showlegend=False,
    height=400,
    title=dict(font=dict(size=16), x=0.5, xanchor="center")
)
fig.update_traces(
    texttemplate="%{text}",
    textposition="outside",
    marker_line_color="rgba(0,0,0,0.1)",
    marker_line_width=1,
    textfont=dict(size=12, color="#FFFFFF")
)
st.plotly_chart(fig, use_container_width=True)
st.markdown('</div>', unsafe_allow_html=True)

# =========================================
# ⬇️ Bottom Section: Manage + Backup/Restore
# =========================================
st.divider()
colA, colB = st.columns([1, 1])

# ---- Manage Team Members (bottom) ----
with colA:
    with st.expander("📝 Manage Team Members", expanded=False):
        st.markdown('<div class="leetcode-card">', unsafe_allow_html=True)
        st.markdown("### ➕ Add Member")
        new_name = st.text_input("Full Name", placeholder="Enter member's full name", key="add_name")
        new_username = st.text_input("LeetCode Username", placeholder="Enter LeetCode username", key="add_username")
        if st.button("➕ Add Member", key="add_member_btn_bottom", use_container_width=True):
            if not new_name or not new_username:
                st.warning("⚠️ Please enter both name and username")
            elif any(m["username"] == new_username for m in members):
                st.warning("⚠️ Member already exists.")
            else:
                with st.spinner("🔍 Verifying LeetCode user..."):
                    try:
                        user_data = fetch_user_data(new_username)
                    except Exception:
                        user_data = None
                    if user_data:
                        # 1) Save the member
                        members.append({"name": new_name, "username": new_username})
                        save_members(user, members)
                        # 2) Immediately seed a snapshot so charts show them right away
                        try:
                            user_data["name"] = new_name
                            user_data["username"] = new_username
                            record_weekly_snapshots(user, [user_data])
                        except Exception:
                            pass
                        bump_cache_buster()
                        st.success(f"✅ Member '{new_name}' added successfully!")
                        st.rerun()
                    else:
                        st.error("❌ User not found on LeetCode or the API response was invalid.")
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="leetcode-card">', unsafe_allow_html=True)
        st.markdown("### ➖ Remove Member")
        name_to_username = {m["name"]: m["username"] for m in members}
        if name_to_username:
            selected_name_rm = st.selectbox("Select a member to remove", list(name_to_username.keys()), key="rm_select")
            if st.button("🗑️ Remove Member", key="remove_member_btn_bottom", use_container_width=True):
                selected_username = name_to_username[selected_name_rm]
                members = [m for m in members if m["username"] != selected_username]
                save_members(user, members)
                bump_cache_buster()
                st.success(f"✅ Member '{selected_name_rm}' removed successfully!")
                st.rerun()
        else:
            st.info("ℹ️ No members to remove.")
        st.markdown('</div>', unsafe_allow_html=True)

# ---- Backup & Restore (bottom) ----
with colB:
    with st.expander("🧰 Backup & Restore", expanded=False):
        st.markdown('<div class="leetcode-card">', unsafe_allow_html=True)
        st.markdown("### 💾 Backup")
        # Build per-user payloads
        members_payload = json.dumps({user: members}, indent=2)
        history_payload = json.dumps({user: load_history().get(user, {})}, indent=2)
        st.download_button("⬇️ Download Members JSON", data=members_payload, file_name=f"{user}_members_backup.json", mime="application/json", use_container_width=True)
        st.download_button("⬇️ Download History JSON", data=history_payload, file_name=f"{user}_history_backup.json", mime="application/json", use_container_width=True)
        st.caption("Backups are scoped to your team (this logged-in user).")

        st.markdown("### ♻️ Restore")
        merge_mode = st.checkbox("Merge instead of replace (recommended)", value=True, help="If unchecked, will replace your current data.")
        up_members = st.file_uploader("Upload Members JSON", type=["json"], key="up_mem")
        up_history = st.file_uploader("Upload History JSON", type=["json"], key="up_hist")

        if st.button("Restore", type="primary", use_container_width=True):
            try:
                if up_members is not None:
                    uploaded_members = json.load(up_members)
                    uploaded_list = uploaded_members.get(user, uploaded_members.get("members", uploaded_members.get("data", [])))
                    if not isinstance(uploaded_list, list):
                        raise ValueError("Members JSON must contain a list under your username.")
                    if merge_mode:
                        current = {m["username"]: m for m in load_members(user)}
                        for m in uploaded_list:
                            current[m["username"]] = {"username": m["username"], "name": m.get("name", m["username"])}
                        save_members(user, list(current.values()))
                    else:
                        save_members(user, [{"username": m["username"], "name": m.get("name", m["username"])} for m in uploaded_list])

                if up_history is not None:
                    uploaded_history = json.load(up_history)
                    current_hist = load_history()
                    incoming = uploaded_history.get(user, uploaded_history.get("history", {}))
                    if not isinstance(incoming, dict):
                        raise ValueError("History JSON must contain an object under your username.")
                    if merge_mode:
                        cur_user_hist = current_hist.get(user, {})
                        # merge by username and week_start uniqueness
                        for uname, snaps in incoming.items():
                            cur_user_hist.setdefault(uname, [])
                            existing_weeks = {s["week_start"] for s in cur_user_hist[uname] if "week_start" in s}
                            for s in snaps:
                                if s.get("week_start") not in existing_weeks:
                                    cur_user_hist[uname].append(s)
                        current_hist[user] = cur_user_hist
                    else:
                        current_hist[user] = incoming
                    save_history(current_hist)

                st.success("✅ Restore completed.")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Restore failed: {e}")
        st.markdown('</div>', unsafe_allow_html=True)

# -----------------------------
# Footer
# -----------------------------
st.markdown("---")
st.markdown(
    '<div style="text-align: center; color: var(--text-secondary); font-size: 0.9rem; padding: 1rem 0;">'
    '🚀 Built with Streamlit • 💻 Developed By Laya • 📊 Team Dashboard'
    '</div>',
    unsafe_allow_html=True
)
