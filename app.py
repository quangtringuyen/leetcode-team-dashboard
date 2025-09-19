import streamlit as st
import json
import os
import io
import time
from datetime import date, timedelta, datetime

import pandas as pd
import plotly.express as px
import requests
import streamlit_authenticator as stauth

from utils.leetcodeapi import fetch_user_data
from utils.auth import register as auth_register, credentials_for_authenticator

# ============================================================
# S3-aware JSON storage adapter (quiet: no UI captions)
# ============================================================
def _use_s3() -> bool:
    try:
        return "aws" in st.secrets and all(
            k in st.secrets["aws"]
            for k in ("AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_DEFAULT_REGION", "S3_BUCKET", "S3_PREFIX")
        )
    except Exception:
        return False

@st.cache_resource(show_spinner=False)
def _s3_client():
    import boto3
    return boto3.client(
        "s3",
        aws_access_key_id=st.secrets["aws"]["AWS_ACCESS_KEY_ID"],
        aws_secret_access_key=st.secrets["aws"]["AWS_SECRET_ACCESS_KEY"],
        region_name=st.secrets["aws"]["AWS_DEFAULT_REGION"],
    )

def _s3_bucket_key(local_path: str):
    bucket = st.secrets["aws"]["S3_BUCKET"]
    prefix = st.secrets["aws"]["S3_PREFIX"].rstrip("/")
    key = f"{prefix}/{local_path.lstrip('/')}"  # mirror local structure
    return bucket, key

def storage_read_json(local_path: str, default):
    if _use_s3():
        try:
            bucket, key = _s3_bucket_key(local_path)
            obj = _s3_client().get_object(Bucket=bucket, Key=key)
            return json.loads(obj["Body"].read().decode("utf-8"))
        except Exception:
            return default
    else:
        if not os.path.exists(local_path):
            return default
        with open(local_path, "r", encoding="utf-8") as f:
            return json.load(f)

def storage_write_json(local_path: str, payload):
    if _use_s3():
        bucket, key = _s3_bucket_key(local_path)
        buf = io.BytesIO(json.dumps(payload, indent=2).encode("utf-8"))
        _s3_client().upload_fileobj(buf, bucket, key)
    else:
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        with open(local_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

# -----------------------------
# Constants & paths
# -----------------------------
DATA_PATH = "data/members.json"
HISTORY_PATH = "data/history.json"  # weekly snapshots

# -----------------------------
# Persistence: members
# -----------------------------
def load_all_members():
    return storage_read_json(DATA_PATH, default={})

def save_all_members(all_members):
    storage_write_json(DATA_PATH, all_members)

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
    return storage_read_json(HISTORY_PATH, default={})

def save_history(history):
    storage_write_json(HISTORY_PATH, history)

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
        total = int(member.get("totalSolved", 0))  # API "accepted" total (reference)
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
                "totalSolved": total,  # charts use Easy+Medium+Hard but we keep this too
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
            # Ensure these are present for snapshot seeding / charts
            user_data["name"] = member.get("name", member["username"])
            user_data["username"] = member["username"]
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

# ===== Accepted Trend by Date: LeetCode calendar API =====
@st.cache_data(show_spinner=False)
def fetch_submission_calendar(username: str):
    """
    Returns {date -> count} for accepted submissions from LeetCode's calendar API.
    Endpoint: https://leetcode.com/api/user_submission_calendar/?username=<user>
    The API returns {'submission_calendar': '{"1694304000": 2, ...}'} (JSON string inside JSON).
    """
    url = f"https://leetcode.com/api/user_submission_calendar/?username={username}"
    try:
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        payload = r.json()
        raw = payload.get("submission_calendar", "{}")
        data = json.loads(raw)
        by_date = {}
        for ts_str, cnt in data.items():
            ts = int(ts_str)  # unix seconds at 00:00:00 UTC
            day = datetime.utcfromtimestamp(ts).date()
            by_date[day] = int(cnt)
        return by_date
    except Exception:
        return {}

def calendars_to_frame(members_list):
    """
    Build a long DataFrame with columns: name, username, date, accepted (daily).
    Ensures every member has a continuous date range (missing -> 0).
    """
    rows = []
    min_d, max_d = None, None
    calendars = {}
    for m in members_list:
        uname = m["username"]
        nm = m.get("name", uname)
        cal = fetch_submission_calendar(uname)
        calendars[uname] = {"name": nm, "data": cal}
        for d in cal.keys():
            if min_d is None or d < min_d: min_d = d
            if max_d is None or d > max_d: max_d = d

    if min_d is None or max_d is None:
        return pd.DataFrame(columns=["name", "username", "date", "accepted"])

    full_days = pd.date_range(start=min_d, end=max_d, freq="D").date
    for m in members_list:
        uname = m["username"]
        nm = m.get("name", uname)
        cal = calendars.get(uname, {}).get("data", {})
        for d in full_days:
            rows.append({
                "name": nm,
                "username": uname,
                "date": pd.to_datetime(d),
                "accepted": int(cal.get(d, 0)),
            })

    return pd.DataFrame(rows)

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
st.caption("Storage: **{}**".format("S3" if _use_s3() else "Local files"))

# ============================================================
# Authentication (cookie-based, persistent)
# ============================================================
if "authenticator" not in st.session_state:
    creds = credentials_for_authenticator()
    cookie_name = st.secrets.get("auth", {}).get("COOKIE_NAME", "leetdash_auth")
    cookie_key  = st.secrets.get("auth", {}).get("COOKIE_KEY", "change-me")
    cookie_exp  = int(st.secrets.get("auth", {}).get("COOKIE_EXPIRY_DAYS", 14))

    st.session_state.authenticator = stauth.Authenticate(
        credentials=creds,
        cookie_name=cookie_name,
        key=cookie_key,
        cookie_expiry_days=cookie_exp,
    )

authenticator: stauth.Authenticate = st.session_state.authenticator
name, authentication_status, username = authenticator.login("Login", "main")

with st.expander("📝 New here? Register", expanded=False):
    reg_col1, reg_col2 = st.columns(2)
    with reg_col1:
        reg_username = st.text_input("Choose a username")
        reg_name = st.text_input("Your display name (optional)")
    with reg_col2:
        reg_email = st.text_input("Email (optional)")
        reg_password = st.text_input("Choose a password", type="password")
    if st.button("Create account", type="primary"):
        if not reg_username or not reg_password:
            st.warning("Please enter username and password.")
        else:
            ok = auth_register(reg_username, reg_password, name=reg_name, email=reg_email)
            if ok:
                st.session_state.authenticator = stauth.Authenticate(
                    credentials=credentials_for_authenticator(),
                    cookie_name=st.secrets.get("auth", {}).get("COOKIE_NAME", "leetdash_auth"),
                    key=st.secrets.get("auth", {}).get("COOKIE_KEY", "change-me"),
                    cookie_expiry_days=int(st.secrets.get("auth", {}).get("COOKIE_EXPIRY_DAYS", 14)),
                )
                st.success("Account created. Please log in.")
                st.rerun()
            else:
                st.error("Username already exists. Try another.")

if authentication_status is False:
    st.error("Invalid username or password.")
    st.stop()
elif authentication_status is None:
    st.info("Please log in to continue.")
    st.stop()

# Authenticated
user = username
st.sidebar.success(f"Logged in as {user}")
authenticator.logout("🚪 Logout", "sidebar")

# --- Session utils
if "cache_buster" not in st.session_state:
    st.session_state.cache_buster = 0.0

# --- Top controls: refresh, snapshot
tc = st.columns([8, 1.2, 1.2])
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

# 🔧 If history is empty or a member is missing, initialize/repair now using current fetch
known_unames = set(team_hist.keys())
current_unames = {m["username"] for m in load_members(user)}
if not team_hist or (current_unames - known_unames):
    try:
        record_weekly_snapshots(user, data)
        raw_hist = load_history()
        team_hist = raw_hist.get(user, {})
    except Exception:
        pass

# Roster map (ensures people with no history appear)
member_name_by_username = {m["username"]: m.get("name", m["username"]) for m in load_members(user)}
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
        # Parse, sort, build Accepted = Easy + Medium + Hard
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

                deltas = ac_df_sorted.dropna(subset=["prev_total"]).copy()
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
                    latest["gain"] = latest["delta"]
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
# 📈 Accepted Trend by Date (Daily/Weekly/Monthly)
# -----------------------------
st.divider()
st.markdown("### 📈 Accepted Trend by Date")

trend_members = load_members(user)
if not trend_members:
    st.info("No members to chart.")
else:
    with st.spinner("Gathering calendars…"):
        cal_df = calendars_to_frame(trend_members)

    if cal_df.empty:
        st.info("No calendar data available yet (LeetCode may return empty until someone has accepted problems).")
    else:
        # Controls
        all_names = sorted(cal_df["name"].unique().tolist())
        c1, c2, c3, c4 = st.columns([2, 2, 2, 2])
        with c1:
            trend_people = st.multiselect("Members", options=all_names, default=all_names, key="trend_people")
        with c2:
            freq = st.selectbox("Granularity", ["Daily", "Weekly", "Monthly"], index=1, key="trend_freq")
        with c3:
            cumulative = st.checkbox("Cumulative", value=False, key="trend_cum")
        with c4:
            mode = st.selectbox("Series", ["Per member", "Team total"], index=0, key="trend_mode")

        if not trend_people:
            st.info("Select at least one member.")
        else:
            df_tr = cal_df[cal_df["name"].isin(trend_people)].copy()

            # Resample by chosen frequency
            if freq == "Daily":
                df_tr["bucket"] = df_tr["date"].dt.to_period("D").dt.to_timestamp()
                freq_code = "D"
            elif freq == "Weekly":
                df_tr["bucket"] = (df_tr["date"] - pd.to_timedelta(df_tr["date"].dt.dayofweek, unit="D"))
                df_tr["bucket"] = pd.to_datetime(df_tr["bucket"].dt.date)
                freq_code = "W-MON"
            else:  # Monthly
                df_tr["bucket"] = df_tr["date"].dt.to_period("M").dt.to_timestamp()
                freq_code = "MS"

            if mode == "Team total":
                agg = df_tr.groupby(["bucket"], as_index=False)["accepted"].sum().sort_values("bucket")
                full_idx = pd.date_range(agg["bucket"].min(), agg["bucket"].max(), freq=freq_code)
                agg = agg.set_index("bucket").reindex(full_idx, fill_value=0).rename_axis("bucket").reset_index()
                if cumulative:
                    agg["accepted"] = agg["accepted"].cumsum()

                fig = px.line(
                    agg, x="bucket", y="accepted", markers=True,
                    labels={"bucket": "Date", "accepted": "Accepted"},
                    title=f"{'Cumulative ' if cumulative else ''}Accepted — Team ({freq.lower()})"
                )
                fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                                  margin=dict(l=20, r=20, t=50, b=20), height=420)
                st.plotly_chart(fig, use_container_width=True)

            else:
                agg = df_tr.groupby(["name", "bucket"], as_index=False)["accepted"].sum()
                min_b, max_b = agg["bucket"].min(), agg["bucket"].max()
                full_buckets = pd.date_range(min_b, max_b, freq=freq_code)
                full_index = pd.MultiIndex.from_product([trend_people, full_buckets], names=["name", "bucket"])

                agg_full = agg.set_index(["name", "bucket"]).reindex(full_index, fill_value=0).reset_index()
                if cumulative:
                    agg_full["accepted"] = agg_full.groupby("name")["accepted"].cumsum()

                fig = px.line(
                    agg_full, x="bucket", y="accepted", color="name", markers=True,
                    labels={"bucket": "Date", "accepted": "Accepted", "name": "Member"},
                    title=f"{'Cumulative ' if cumulative else ''}Accepted — Per Member ({freq.lower()})"
                )
                fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                                  margin=dict(l=20, r=20, t=50, b=20), height=420)
                st.plotly_chart(fig, use_container_width=True)

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
            elif any(m["username"] == new_username for m in load_members(user)):
                st.warning("⚠️ Member already exists.")
            else:
                with st.spinner("🔍 Verifying LeetCode user..."):
                    try:
                        user_data = fetch_user_data(new_username)
                    except Exception:
                        user_data = None
                    if user_data:
                        # 1) Save the member
                        members_now = load_members(user)  # re-read to be safe
                        members_now.append({"name": new_name, "username": new_username})
                        save_members(user, members_now)
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
        members_now = load_members(user)
        name_to_username = {m["name"]: m["username"] for m in members_now}
        if name_to_username:
            selected_name_rm = st.selectbox("Select a member to remove", list(name_to_username.keys()), key="rm_select")
            if st.button("🗑️ Remove Member", key="remove_member_btn_bottom", use_container_width=True):
                selected_username = name_to_username[selected_name_rm]
                new_members = [m for m in members_now if m["username"] != selected_username]
                save_members(user, new_members)
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
        members_payload = json.dumps({user: load_members(user)}, indent=2)
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

    # ---- Optional: S3 Self-Test (put/get/delete) ----
    with st.expander("🧪 S3 Connectivity Test", expanded=False):
        if st.button("Run S3 self-test (put/get/delete)"):
            if not _use_s3():
                st.warning("S3 mode is OFF (using local files). Add [aws] secrets to enable S3.")
            else:
                import uuid
                client = _s3_client()
                bucket, base_key = _s3_bucket_key("data/")
                test_key = base_key.rstrip("/") + f"/_selftest_{uuid.uuid4().hex}.txt"
                body = b"hello from app self-test"
                try:
                    client.put_object(Bucket=bucket, Key=test_key, Body=body)
                    obj = client.get_object(Bucket=bucket, Key=test_key)
                    got = obj["Body"].read()
                    assert got == body, "Content mismatch"
                    client.delete_object(Bucket=bucket, Key=test_key)
                    st.success("S3 self-test passed ✅")
                except Exception as e:
                    st.error(f"S3 self-test failed ❌: {e}")

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
