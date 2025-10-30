# app.py
import streamlit as st
import json
import os
import io
import time
from datetime import date, timedelta, datetime

import pandas as pd
import plotly.express as px
import requests

# Try authenticator (cookie-based sessions). Falls back if unavailable.
try:
    import streamlit_authenticator as stauth
    ST_AUTH_AVAILABLE = True
except Exception:
    ST_AUTH_AVAILABLE = False

from utils.leetcodeapi import fetch_user_data, fetch_recent_submissions, fetch_daily_challenge
from utils.auth import (
    register as auth_register,
    credentials_for_authenticator,
    verify_login,
)

# ===================== Base page & CSS =====================
st.set_page_config(layout="wide", page_title="LeetCode Team Dashboard", page_icon="📊")
st.markdown("""
    <style>
    :root { --leetcode-orange:#FFA116; --leetcode-green:#34A853; --leetcode-red:#EF4743; --leetcode-blue:#1E88E5; }
    [data-theme="dark"] {
        --bg-primary:#0E1117; --bg-secondary:#262730; --bg-card:#1E1E1E;
        --text-primary:#FAFAFA; --text-secondary:#A0A0A0; --border-color:#333; --hover-bg:#2A2A2A;
    }
    [data-theme="light"] {
        --bg-primary:#FFFFFF; --bg-secondary:#F0F2F6; --bg-card:#FFFFFF;
        --text-primary:#262730; --text-secondary:#6C757D; --border-color:#E0E0E0; --hover-bg:#F8F9FA;
    }
    .stApp { background-color: var(--bg-primary) !important; }
    .main .block-container { padding-top: 2rem; padding-bottom: 2rem; }
    .header-title { color: var(--leetcode-orange)!important; font-weight:700; font-size:2.5rem; padding-bottom:.5rem; border-bottom:3px solid #FFA116; margin-bottom:1.5rem; text-align:center; }
    .leetcode-card { background: var(--bg-card)!important; border-radius: 12px; border: 1px solid var(--border-color); padding: 1.5rem; margin-bottom: 1.5rem; }
    .profile-header { background: linear-gradient(135deg, var(--bg-card), var(--bg-secondary)); border-radius: 12px; padding: 1.5rem; color: var(--text-primary); margin-bottom: 1.5rem; border: 1px solid var(--border-color); }
    .rank-badge, .solved-badge { background: var(--leetcode-orange); color:#fff; border-radius: 20px; padding: 4px 12px; font-weight: 600; display: inline-block; font-size: .9rem; }
    .solved-badge { background: var(--leetcode-green); }
    .leaderboard-item { transition: all .3s ease; border-radius: 8px; padding: 12px; margin-bottom: 8px; background: var(--bg-card); border:1px solid var(--border-color); cursor:pointer; }
    .leaderboard-item:hover { background: var(--hover-bg); transform: translateX(5px); }
    .leaderboard-item.selected { background: rgba(255,161,22,.15); border-left: 4px solid var(--leetcode-orange); }
    .stat-card { background:var(--bg-card); border-radius:10px; padding:1.2rem; text-align:center; border:1px solid var(--border-color); }
    .stat-label { color: var(--text-secondary); font-size:.9rem; font-weight:500; }
    .stat-value { font-size:1.8rem; font-weight:700; margin:.5rem 0; color:var(--text-primary); }
    .stProgress>div>div>div { background-color: var(--leetcode-orange)!important; }
    footer, #MainMenu, header { visibility:hidden; }
    @media (max-width: 768px) { .header-title { font-size: 2rem; } .stat-card { min-width: 100%; } }
    </style>
""", unsafe_allow_html=True)
st.markdown('<div class="header-title">👨🏼‍💻 LeetCode Team Dashboard</div>', unsafe_allow_html=True)

# ===================== S3-or-Local storage adapter =====================
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
    key = f"{prefix}/{local_path.lstrip('/')}"
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

# ===================== Paths / Persistence =====================
DATA_PATH = "data/members.json"
HISTORY_PATH = "data/history.json"

def load_all_members():
    return storage_read_json(DATA_PATH, default={})

def save_all_members(all_members):
    storage_write_json(DATA_PATH, all_members)

def load_members(user):
    return load_all_members().get(user, [])

def save_members(user, members):
    all_members = load_all_members()
    all_members[user] = members
    save_all_members(all_members)

def load_history():
    return storage_read_json(HISTORY_PATH, default={})

def save_history(history):
    storage_write_json(HISTORY_PATH, history)

def iso_week_start(d: date) -> date:
    return d - timedelta(days=d.weekday())

def record_weekly_snapshots(team_owner: str, team_data: list, when: date | None = None):
    """
    Save weekly snapshot per member (Accepted = Easy+Medium+Hard).
    Stored as history[owner][username] = [ {week_start, username, name, totalSolved, Easy, Medium, Hard}, ... ]
    Idempotent per (owner, username, week).
    """
    history = load_history()
    history.setdefault(team_owner, {})
    week_start_str = iso_week_start(when or date.today()).isoformat()
    changed = False

    for member in team_data:
        uname = member["username"]
        name = member.get("name", uname)
        total = int(member.get("totalSolved", 0))
        easy = medium = hard = 0
        for s in member.get("submissions", []):
            if s.get("difficulty") == "Easy": easy = int(s.get("count", 0))
            elif s.get("difficulty") == "Medium": medium = int(s.get("count", 0))
            elif s.get("difficulty") == "Hard": hard = int(s.get("count", 0))

        history[team_owner].setdefault(uname, [])
        user_hist = history[team_owner][uname]
        if not any(s.get("week_start") == week_start_str for s in user_hist):
            user_hist.append({
                "week_start": week_start_str,
                "username": uname,
                "name": name,
                "totalSolved": total,
                "Easy": easy, "Medium": medium, "Hard": hard
            })
            changed = True

    if changed:
        save_history(history)
    return history

# ===================== Cache utils & fetch helpers =====================
def bump_cache_buster():
    st.session_state.cache_buster = time.time()

@st.cache_data(show_spinner=False)
def fetch_all_data(members, cache_key: float = 0.0):
    data = []
    for member in members:
        user_data = fetch_user_data(member["username"])
        if user_data:
            user_data["name"] = member.get("name", member["username"])
            user_data["username"] = member["username"]
            data.append(user_data)
    return data

def sum_accepted_from_submissions(subs):
    if not isinstance(subs, list):
        return 0
    return sum(int(item.get("count", 0)) for item in subs if item.get("difficulty") in ("Easy", "Medium", "Hard"))

@st.cache_data(show_spinner=False)
def fetch_submission_calendar(username: str):
    """
    LeetCode calendar: https://leetcode.com/api/user_submission_calendar/?username=<user>
    Returns dict[date -> count]
    """
    url = f"https://leetcode.com/api/user_submission_calendar/?username={username}"
    try:
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        payload = r.json()
        raw = payload.get("submission_calendar", "{}")
        data = json.loads(raw)
        out = {}
        for ts_str, cnt in data.items():
            ts = int(ts_str)
            day = datetime.utcfromtimestamp(ts).date()
            out[day] = int(cnt)
        return out
    except Exception:
        return {}

@st.cache_data(show_spinner=False)
def fetch_all_recent_submissions(members_list, cache_key: float = 0.0):
    """
    Fetch recent submissions for all members.
    Returns dict[username] -> list of recent submissions
    """
    result = {}
    for m in members_list:
        uname = m["username"]
        submissions = fetch_recent_submissions(uname, limit=30)
        result[uname] = submissions
    return result

@st.cache_data(show_spinner=False, ttl=3600)
def get_daily_challenge():
    """Get today's daily challenge (cached for 1 hour)"""
    return fetch_daily_challenge()

def calendars_to_frame(members_list):
    """
    Primary data source: daily calendar API.
    Returns rows even if some users have empty calendars (we'll fill zeros for the shared date span).
    If absolutely no calendars have data, returns empty DF (fallback added elsewhere).
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
            rows.append({"name": nm, "username": uname, "date": pd.to_datetime(d), "accepted": int(cal.get(d, 0))})
    return pd.DataFrame(rows)

def trend_frame_with_fallback(members_list, owner_username: str):
    """
    Build 'Accepted Trend by Date' data with fallback:
    - Try daily calendars (primary).
    - If entirely empty (or for users with empty calendars), use weekly snapshot diffs to synthesize daily points
      (placing weekly gains on the week's Monday).
    - Combine both where applicable.
    """
    cal_df = calendars_to_frame(members_list)
    need_fallback = cal_df.empty
    if not need_fallback:
        users_with_calendar = set(cal_df["username"].unique())
    else:
        users_with_calendar = set()

    history = load_history().get(owner_username, {})
    rows = []
    for m in members_list:
        uname = m["username"]
        nm = m.get("name", uname)
        snaps = history.get(uname, [])
        if not snaps:
            continue
        h = pd.DataFrame(snaps)
        if h.empty or "week_start" not in h:
            continue
        h["week_start"] = pd.to_datetime(h["week_start"])
        h = h.sort_values("week_start")
        h["Accepted"] = h[["Easy","Medium","Hard"]].fillna(0).astype(int).sum(axis=1)
        h["prev"] = h["Accepted"].shift(1)
        h["gain"] = (h["Accepted"] - h["prev"]).fillna(h["Accepted"]).astype(int)
        h["date"] = h["week_start"].dt.date
        for r in h.itertuples(index=False):
            rows.append({"name": nm, "username": uname, "date": pd.to_datetime(r.date), "accepted": int(r.gain)})

    hist_daily = pd.DataFrame(rows)

    if need_fallback:
        return hist_daily

    if not hist_daily.empty:
        if users_with_calendar:
            missing_users = set(u["username"] for u in members_list) - users_with_calendar
            add_from_hist = hist_daily[hist_daily["username"].isin(missing_users)]
            cal_df = pd.concat([cal_df, add_from_hist], ignore_index=True)
        else:
            cal_df = pd.concat([cal_df, hist_daily], ignore_index=True)

    return cal_df

# ===================== AUTH SECTION (read session_state) =====================
def _build_authenticator():
    return stauth.Authenticate(
        credentials=credentials_for_authenticator(),
        cookie_name=st.secrets.get("auth", {}).get("COOKIE_NAME", "leetdash_auth"),
        key=st.secrets.get("auth", {}).get("COOKIE_KEY", "change-me"),
        cookie_expiry_days=int(st.secrets.get("auth", {}).get("COOKIE_EXPIRY_DAYS", 14)),
    )

def _login_compat(authenticator):
    try:
        res = authenticator.login(location="main")  # new API
        if isinstance(res, tuple) and len(res) == 3:
            return res
        return (None, None, None) if res is None else res
    except TypeError:
        return authenticator.login("Login", "main")  # old API

def ensure_authenticated_user():
    """Return username when logged in; otherwise halt UI until login happens."""
    # Cookie-based sessions (preferred)
    if ST_AUTH_AVAILABLE:
        if "authenticator" not in st.session_state:
            st.session_state.authenticator = _build_authenticator()
        authenticator = st.session_state.authenticator

        name, auth_status, username = _login_compat(authenticator)

        ss_status = st.session_state.get("authentication_status", None)
        ss_user = st.session_state.get("username", None)
        ss_name = st.session_state.get("name", None)

        if ss_status is not None:
            auth_status = ss_status
        if ss_user:
            username = ss_user
        if ss_name:
            name = ss_name

        if auth_status is None:
            with st.expander("📝 New here? Register", expanded=False):
                col1, col2 = st.columns(2)
                with col1:
                    reg_user = st.text_input("Choose a username", key="reg_user")
                    reg_name = st.text_input("Display name (optional)", key="reg_name")
                with col2:
                    reg_email = st.text_input("Email (optional)", key="reg_email")
                    reg_pw = st.text_input("Choose a password", type="password", key="reg_pw")
                if st.button("Create account", type="primary", key="reg_btn"):
                    if not reg_user or not reg_pw:
                        st.warning("Please enter username and password.")
                    else:
                        ok = auth_register(reg_user, reg_pw, name=reg_name, email=reg_email)
                        if ok:
                            st.session_state.authenticator = _build_authenticator()
                            st.success("Account created. Please log in.")
                            st.experimental_rerun()
                        else:
                            st.error("Username already exists.")

        if auth_status is False:
            st.error("Invalid username or password.")
            return None

        if auth_status is True and username:
            try:
                authenticator.logout("🚪 Logout", location="sidebar")
            except TypeError:
                authenticator.logout("🚪 Logout", "sidebar")
            st.sidebar.success(f"Logged in as {username}")
            return username

        st.info("Please log in to continue.")
        st.stop()

    # Fallback: simple session login
    if "user" not in st.session_state:
        st.session_state.user = None

    if st.session_state.user is None:
        st.subheader("🔐 Login")
        c1, c2 = st.columns(2)
        with c1:
            u = st.text_input("Username", key="fb_user")
        with c2:
            p = st.text_input("Password", type="password", key="fb_pw")
        b1, b2 = st.columns(2)
        with b1:
            if st.button("🚀 Login", key="fb_login"):
                if verify_login(u, p):
                    st.session_state.user = u
                    st.success("Logged in!")
                    st.experimental_rerun()
                else:
                    st.error("Invalid credentials.")
        with b2:
            if st.button("📝 Register", key="fb_register"):
                if not u or not p:
                    st.warning("Enter username & password.")
                else:
                    ok = auth_register(u, p, name=u)
                    st.success("Registered. Click Login.") if ok else st.error("Username already exists.")
        st.stop()

    st.sidebar.success(f"Logged in as {st.session_state.user}")
    if st.sidebar.button("🚪 Logout", key="fb_logout"):
        st.session_state.user = None
        st.experimental_rerun()
    return st.session_state.user

# ===================== Authenticate =====================
user = ensure_authenticated_user()
st.caption("Storage: **{}**".format("S3" if _use_s3() else "Local files"))

# ===================== Top controls =====================
if "cache_buster" not in st.session_state:
    st.session_state.cache_buster = 0.0

def bump_cache_buster():
    st.session_state.cache_buster = time.time()

tc = st.columns([8, 1.2, 1.6])
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

# ===================== Load members & fetch data =====================
def load_members_safe():
    try:
        return load_members(user)
    except Exception:
        return []

members = load_members_safe()
if not members:
    st.warning("⚠️ No members found for your team.")

with st.spinner("🔄 Fetching team data from LeetCode..."):
    data = fetch_all_data(members, cache_key=st.session_state.cache_buster)

if not data:
    st.error("❌ Failed to fetch data for team members")
    st.stop()

# Save weekly snapshot (idempotent) and force if requested
record_weekly_snapshots(user, data)
if st.session_state.pop("force_snapshot", False):
    record_weekly_snapshots(user, data)

# Current DataFrame
df = pd.DataFrame(data)
df["Accepted"] = df["submissions"].apply(sum_accepted_from_submissions)
df_sorted = df.sort_values(by="Accepted", ascending=False)

# ===================== Consistent Colors per Member =====================
def build_member_color_map(member_names: list[str]) -> dict:
    # Stitch multiple qualitative palettes to have many distinct colors
    palettes = (
        px.colors.qualitative.Plotly
        + px.colors.qualitative.Set3
        + px.colors.qualitative.D3
        + px.colors.qualitative.Pastel1
        + px.colors.qualitative.Dark24
    )
    # Deduplicate while preserving order
    seen = set()
    palette = [c for c in palettes if not (c in seen or seen.add(c))]
    # Assign colors deterministically by sorted name order
    mapping = {}
    for i, name in enumerate(sorted(member_names)):
        mapping[name] = palette[i % len(palette)]
    return mapping

ALL_MEMBER_NAMES = sorted([m.get("name", m["username"]) for m in members])
MEMBER_COLORS = build_member_color_map(ALL_MEMBER_NAMES)

# ===================== Leaderboard & Profile =====================
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

with right_col:
    selected_data = next((item for item in data if item["username"] == st.session_state.get("selected_user", df_sorted.iloc[0]["username"])), None)
    if selected_data:
        sel_accepted = sum_accepted_from_submissions(selected_data.get("submissions", []))
        st.markdown(f"""
            <div class="profile-header">
                <div style="display:flex; align-items:center; gap:20px;">
                    <img src="{selected_data['avatar']}" width="80" style="border-radius:50%; border:3px solid var(--leetcode-orange);">
                    <div>
                        <h2 style="margin:0;">{selected_data['name']}</h2>
                        <div style="display:flex; gap:10px; margin-top:8px; flex-wrap:wrap;">
                            <div class="rank-badge">🏅 Rank: {selected_data['ranking']}</div>
                            <div class="solved-badge">✅ Accepted (Total): {sel_accepted}</div>
                        </div>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)

        def diff_count(diff):
            for d in selected_data["submissions"]:
                if d.get("difficulty") == diff:
                    return int(d.get("count", 0))
            return 0

        easy_c, med_c, hard_c = diff_count("Easy"), diff_count("Medium"), diff_count("Hard")
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
                color_discrete_map={'Easy': '#34A853','Medium':'#FFA116','Hard':'#EF4743'},
                hole=0.4,
            )
            fig.update_layout(height=520, showlegend=True, margin=dict(l=20, r=20, t=30, b=0),
                              legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5, font=dict(size=13)),
                              paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(size=13))
            fig.update_traces(textposition='inside', textinfo='percent+label',
                              hovertemplate="<b>%{label}</b><br>Accepted: %{value}<br>Percentage: %{percent}",
                              textfont=dict(color='#FFFFFF', size=13))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("🎯 No accepted challenges yet!")

# ===================== Daily Challenge & Recent Accepted Problems =====================
st.divider()
st.markdown("### 🌟 Today's LeetCode Daily Challenge")

daily_challenge = get_daily_challenge()
if daily_challenge:
    diff_colors = {"Easy": "#34A853", "Medium": "#FFA116", "Hard": "#EF4743"}
    diff_color = diff_colors.get(daily_challenge.get("difficulty", ""), "#999")

    st.markdown(f"""
        <div class="leetcode-card" style="background: linear-gradient(135deg, var(--bg-card), var(--bg-secondary));">
            <div style="display:flex; align-items:center; justify-content:space-between; flex-wrap:wrap;">
                <div style="flex:1; min-width:250px;">
                    <h3 style="margin:0; color:var(--text-primary);">{daily_challenge.get('title', 'Unknown')}</h3>
                    <div style="margin-top:8px;">
                        <span style="background:{diff_color}; color:#fff; padding:4px 12px; border-radius:12px; font-weight:600; font-size:0.85rem;">
                            {daily_challenge.get('difficulty', 'Unknown')}
                        </span>
                    </div>
                </div>
                <div>
                    <a href="{daily_challenge.get('link', '')}" target="_blank" style="text-decoration:none;">
                        <button style="background:var(--leetcode-orange); color:#fff; border:none; padding:10px 20px; border-radius:8px; font-weight:600; cursor:pointer; font-size:1rem;">
                            Solve Today's Challenge →
                        </button>
                    </a>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)
else:
    st.info("Could not fetch today's daily challenge.")

st.markdown("### 📅 Recent Accepted Problems (Last 7 Days)")

with st.spinner("Fetching recent submissions..."):
    all_recent = fetch_all_recent_submissions(members, cache_key=st.session_state.cache_buster)

# Filter to last 7 days and group by date and member
today = date.today()
seven_days_ago = today - timedelta(days=7)

recent_by_date = {}
for member in members:
    uname = member["username"]
    name = member.get("name", uname)
    submissions = all_recent.get(uname, [])

    for sub in submissions:
        sub_date = sub["date"]
        if seven_days_ago <= sub_date <= today:
            if sub_date not in recent_by_date:
                recent_by_date[sub_date] = []
            recent_by_date[sub_date].append({
                "name": name,
                "username": uname,
                "title": sub["title"],
                "titleSlug": sub["titleSlug"]
            })

if recent_by_date:
    # Build chart data
    chart_data = []
    all_dates = pd.date_range(start=seven_days_ago, end=today, freq='D').date

    for member in members:
        member_name = member.get("name", member["username"])
        for day in all_dates:
            count = 0
            if day in recent_by_date:
                count = sum(1 for sub in recent_by_date[day] if sub["name"] == member_name)
            chart_data.append({
                "date": pd.to_datetime(day),
                "name": member_name,
                "problems_solved": count
            })

    chart_df = pd.DataFrame(chart_data)

    # Visualization selector
    viz_type = st.selectbox(
        "Visualization",
        ["Stacked Bar Chart", "Heatmap", "Area Chart"],
        key="recent_viz",
        help="Choose how to visualize the last 7 days of activity"
    )

    if viz_type == "Stacked Bar Chart":
        # Stacked bar chart - shows individual contributions AND team total
        fig = px.bar(
            chart_df, x="date", y="problems_solved", color="name",
            color_discrete_map=MEMBER_COLORS,
            labels={"date": "Date", "problems_solved": "Problems Solved", "name": "Member"},
            title="Daily Accepted Problems - Last 7 Days",
            text="problems_solved"
        )
        fig.update_traces(
            textposition="inside",
            texttemplate="%{text}",
            textfont=dict(color='white', size=11),
            hovertemplate="<b>%{fullData.name}</b><br>Date: %{x|%b %d}<br>Problems: %{y}<extra></extra>"
        )
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=20, r=20, t=50, b=80),
            height=420,
            xaxis=dict(tickformat="%b %d", title="Date"),
            yaxis=dict(title="Problems Solved"),
            barmode='stack',
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.35,
                xanchor="center",
                x=0.5,
                title=None
            )
        )
        st.plotly_chart(fig, use_container_width=True)

    elif viz_type == "Heatmap":
        # Heatmap - great for spotting patterns
        pivot_df = chart_df.pivot(index="name", columns="date", values="problems_solved")
        pivot_df.columns = [d.strftime("%b %d") for d in pivot_df.columns]

        fig = px.imshow(
            pivot_df,
            labels=dict(x="Date", y="Member", color="Problems"),
            color_continuous_scale=[
                [0, '#1a1a1a'],      # Dark for 0
                [0.2, '#2d5a2d'],    # Dark green
                [0.4, '#34A853'],    # LeetCode green
                [0.6, '#FFA116'],    # LeetCode orange
                [1, '#EF4743']       # LeetCode red for high activity
            ],
            aspect="auto",
            title="Activity Heatmap - Last 7 Days"
        )
        fig.update_traces(
            text=pivot_df.values,
            texttemplate="%{text}",
            textfont=dict(size=12),
            hovertemplate="<b>%{y}</b><br>%{x}<br>Problems: %{z}<extra></extra>"
        )
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=20, r=20, t=50, b=20),
            height=max(300, len(members) * 60),  # Dynamic height based on members
            xaxis=dict(side="bottom"),
            coloraxis_colorbar=dict(title="Problems")
        )
        st.plotly_chart(fig, use_container_width=True)

    else:  # Area Chart
        # Stacked area chart - shows accumulation over time
        fig = px.area(
            chart_df, x="date", y="problems_solved", color="name",
            color_discrete_map=MEMBER_COLORS,
            labels={"date": "Date", "problems_solved": "Problems Solved", "name": "Member"},
            title="Daily Accepted Problems - Last 7 Days",
        )
        fig.update_traces(
            hovertemplate="<b>%{fullData.name}</b><br>Date: %{x|%b %d}<br>Problems: %{y}<extra></extra>"
        )
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=20, r=20, t=50, b=80),
            height=420,
            xaxis=dict(tickformat="%b %d", title="Date"),
            yaxis=dict(title="Problems Solved"),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.35,
                xanchor="center",
                x=0.5,
                title=None
            )
        )
        st.plotly_chart(fig, use_container_width=True)

    # Show summary stats
    total_problems = sum(len(subs) for subs in recent_by_date.values())
    most_active_day = max(recent_by_date.items(), key=lambda x: len(x[1]))

    stat_cols = st.columns(3)
    with stat_cols[0]:
        st.metric("Total Problems Solved", total_problems, delta=f"{len(recent_by_date[today])} today" if today in recent_by_date else None)
    with stat_cols[1]:
        avg_per_day = total_problems / 7
        st.metric("Average Per Day", f"{avg_per_day:.1f}")
    with stat_cols[2]:
        st.metric("Most Active Day", most_active_day[0].strftime("%b %d"), delta=f"{len(most_active_day[1])} problems")

    st.markdown("---")
    st.markdown("#### 📋 Detailed Breakdown")

    # Sort dates in descending order (most recent first)
    sorted_dates = sorted(recent_by_date.keys(), reverse=True)

    for day in sorted_dates:
        day_submissions = recent_by_date[day]
        day_str = day.strftime("%A, %B %d, %Y")

        with st.expander(f"📆 {day_str} — {len(day_submissions)} problem(s) solved", expanded=(day == today)):
            # Group by member for better display
            by_member = {}
            for sub in day_submissions:
                member_name = sub["name"]
                if member_name not in by_member:
                    by_member[member_name] = []
                by_member[member_name].append(sub)

            for member_name, subs in by_member.items():
                st.markdown(f"**{member_name}** ({len(subs)} problem{'s' if len(subs) > 1 else ''})")
                for sub in subs:
                    problem_url = f"https://leetcode.com/problems/{sub['titleSlug']}/"
                    st.markdown(f"- [{sub['title']}]({problem_url})")
                st.markdown("")
else:
    st.info("No accepted problems in the last 7 days. Keep coding!")

# ===================== Weekly Progress (full roster + ffill + labels + colors) =====================
st.divider()
st.markdown("### 📅 Weekly Accepted Progress (Cumulative)")

raw_hist = load_history()
team_hist = raw_hist.get(user, {})

# Seed missing members so everyone appears
known_unames = set(team_hist.keys())
current_unames = {m["username"] for m in load_members(user)}
if not team_hist or (current_unames - known_unames):
    team_hist = record_weekly_snapshots(user, data).get(user, {})

member_name_by_username = {m["username"]: m.get("name", m["username"]) for m in load_members(user)}
all_member_names = sorted(member_name_by_username.values())

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
    st.info("No weekly snapshots yet. Use **Record snapshot now**.")
else:
    hist_df["week_start"] = pd.to_datetime(hist_df["week_start"])
    hist_df.sort_values(["username", "week_start"], inplace=True)
    hist_df["Accepted"] = hist_df["Easy"] + hist_df["Medium"] + hist_df["Hard"]

    # Controls
    this_year = date.today().year
    proposed_start = iso_week_start(date(this_year, 9, 1))
    min_date = hist_df["week_start"].min().date()
    max_date = hist_df["week_start"].max().date()
    def clamp(d, lo, hi): return lo if d < lo else (hi if d > hi else d)
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

    f_hist = hist_df[hist_df["week_start"] >= pd.Timestamp(start_date)].copy()
    if f_hist.empty:
        st.info("No data for the selected start date yet.")
    else:
        start_monday = pd.Timestamp(start_date) - pd.Timedelta(days=pd.Timestamp(start_date).weekday())
        end_monday = f_hist["week_start"].max()
        weeks = pd.date_range(start=start_monday, end=end_monday, freq="W-MON")
        full_index = pd.MultiIndex.from_product([selected_people, weeks], names=["name", "week_start"])

        chart_df = f_hist[["name", "week_start", metric]].set_index(["name", "week_start"]).sort_index()
        chart_df = chart_df.reindex(full_index)
        chart_df = chart_df.groupby(level=0)[metric].ffill().fillna(0.0).to_frame("value").reset_index()

        # Distinct colors per member + value labels
        fig = px.line(
            chart_df, x="week_start", y="value", color="name", markers=True,
            text="value",
            color_discrete_map=MEMBER_COLORS,
            labels={"week_start":"Week Start","value":metric,"name":"Member"},
            title=f"Weekly {metric} Progress (Cumulative)"
        )
        fig.update_traces(mode="lines+markers+text", textposition="top center", textfont=dict(size=11),
                          texttemplate="%{text:.0f}")
        fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                          margin=dict(l=20, r=20, t=50, b=20), height=440)
        st.plotly_chart(fig, use_container_width=True)

        if show_deltas:
            ac_df = f_hist[["name", "week_start", "Accepted"]].set_index(["name", "week_start"]).sort_index()
            ac_df = ac_df.reindex(full_index)
            ac_df = ac_df.groupby(level=0)["Accepted"].ffill().fillna(0.0).to_frame("Accepted").reset_index()

            ac_df_sorted = ac_df.sort_values(["week_start", "Accepted"], ascending=[True, False])
            ac_df_sorted["rank"] = ac_df_sorted.groupby("week_start")["Accepted"].rank(method="min", ascending=False)
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

            out = deltas[["week_start","name","prev_total","Accepted","delta","pct_change","prev_rank","rank","rank_delta"]].copy()
            out = out.rename(columns={"prev_total":"Prev (Accepted)","delta":"Δ Accepted","pct_change":"% Change","prev_rank":"Prev Rank","rank":"Rank","rank_delta":"Δ Rank"})
            out["Δ Accepted"] = out["Δ Accepted"].apply(arrowize)
            out["% Change"] = out["% Change"].apply(pctfmt)
            out["Δ Rank"] = out["Δ Rank"].apply(rankfmt)
            out = out.sort_values(["week_start","Rank","name"])

            st.markdown("#### Week-over-Week Changes (Accepted challenges)")
            st.dataframe(out, use_container_width=True)

            latest_week = deltas["week_start"].max() if not deltas.empty else None
            if latest_week:
                latest = deltas[deltas["week_start"] == latest_week].copy()
                latest["gain"] = latest["delta"]
                top = latest.sort_values("gain", ascending=False).head(3).reset_index(drop=True)
                medals = []
                if len(top) >= 1: medals.append(f"🥇 {top.iloc[0]['name']}: +{int(top.iloc[0]['gain'])}")
                if len(top) >= 2: medals.append(f"🥈 {top.iloc[1]['name']}: +{int(top.iloc[1]['gain'])}")
                if len(top) >= 3: medals.append(f"🥉 {top.iloc[2]['name']}: +{int(top.iloc[2]['gain'])}")
                if medals:
                    st.caption(f"**Top gainers — week of {latest_week}**: " + "  •  ".join(medals))

# ===================== Accepted Trend by Date (with snapshot fallback + colors + labels) =====================
st.divider()
st.markdown("### 📈 Accepted Trend by Date")
trend_members = load_members(user)
if not trend_members:
    st.info("No members to chart.")
else:
    with st.spinner("Gathering calendars…"):
        cal_df = trend_frame_with_fallback(trend_members, user)

    if cal_df.empty:
        st.info("No trend data is available yet. Record a snapshot after someone accepts challenges.")
    else:
        all_names = sorted(cal_df["name"].unique().tolist())

        # Controls in columns
        c1, c2, c3, c4, c5 = st.columns([2, 2, 2, 2, 2])
        with c1:
            trend_people = st.multiselect("Members", options=all_names, default=all_names, key="trend_people")
        with c2:
            freq = st.selectbox("Granularity", ["Daily", "Weekly", "Monthly"], index=0, key="trend_freq")
        with c3:
            cumulative = st.checkbox("Show Cumulative", value=True, key="trend_cum",
                                    help="Shows running total (cumulative sum) instead of daily/weekly/monthly counts")
        with c4:
            chart_type = st.selectbox("Chart Type", ["Line", "Bar", "Area"], index=0, key="trend_chart")
        with c5:
            mode = st.selectbox("View", ["Per member", "Team total"], index=0, key="trend_mode")

        if not trend_people:
            st.info("Select at least one member.")
        else:
            df_tr = cal_df[cal_df["name"].isin(trend_people)].copy()

            # Bucket data by granularity
            if freq == "Daily":
                df_tr["bucket"] = df_tr["date"].dt.to_period("D").dt.to_timestamp(); freq_code = "D"
            elif freq == "Weekly":
                df_tr["bucket"] = (df_tr["date"] - pd.to_timedelta(df_tr["date"].dt.dayofweek, unit="D"))
                df_tr["bucket"] = pd.to_datetime(df_tr["bucket"].dt.date); freq_code = "W-MON"
            else:
                df_tr["bucket"] = df_tr["date"].dt.to_period("M").dt.to_timestamp(); freq_code = "MS"

            if mode == "Team total":
                # Aggregate by date
                agg = df_tr.groupby(["bucket"], as_index=False)["accepted"].sum().sort_values("bucket")
                if not agg.empty:
                    full_idx = pd.date_range(agg["bucket"].min(), agg["bucket"].max(), freq=freq_code)
                    agg = agg.set_index("bucket").reindex(full_idx, fill_value=0).rename_axis("bucket").reset_index()
                    if cumulative:
                        agg["accepted"] = agg["accepted"].cumsum()

                # Create chart based on type
                if chart_type == "Bar":
                    fig = px.bar(
                        agg, x="bucket", y="accepted",
                        labels={"bucket": "Date", "accepted": "Accepted"},
                        title=f"{'Cumulative ' if cumulative else ''}Accepted Problems — Team Total ({freq})",
                        text="accepted"
                    )
                    fig.update_traces(
                        marker_color=px.colors.qualitative.Plotly[0],
                        textposition="outside",
                        texttemplate="%{text:.0f}",
                        hovertemplate="Date=%{x}<br>Accepted=%{y}<extra></extra>"
                    )
                elif chart_type == "Area":
                    fig = px.area(
                        agg, x="bucket", y="accepted",
                        labels={"bucket": "Date", "accepted": "Accepted"},
                        title=f"{'Cumulative ' if cumulative else ''}Accepted Problems — Team Total ({freq})"
                    )
                    fig.update_traces(
                        hovertemplate="Date=%{x}<br>Accepted=%{y}<extra></extra>",
                        fillcolor=px.colors.qualitative.Plotly[0]
                    )
                else:  # Line
                    fig = px.line(
                        agg, x="bucket", y="accepted", markers=True,
                        labels={"bucket": "Date", "accepted": "Accepted"},
                        title=f"{'Cumulative ' if cumulative else ''}Accepted Problems — Team Total ({freq})"
                    )
                    fig.update_traces(
                        mode="lines+markers",
                        line_color=px.colors.qualitative.Plotly[0],
                        hovertemplate="Date=%{x}<br>Accepted=%{y}<extra></extra>"
                    )

                fig.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    margin=dict(l=20, r=20, t=50, b=20),
                    height=450,
                    showlegend=False
                )
                st.plotly_chart(fig, use_container_width=True)

            else:  # Per member
                agg = df_tr.groupby(["name", "bucket"], as_index=False)["accepted"].sum()
                if not agg.empty:
                    min_b, max_b = agg["bucket"].min(), agg["bucket"].max()
                    full_buckets = pd.date_range(min_b, max_b, freq=freq_code)
                    full_index = pd.MultiIndex.from_product([trend_people, full_buckets], names=["name", "bucket"])
                    agg_full = agg.set_index(["name", "bucket"]).reindex(full_index, fill_value=0).reset_index()
                    if cumulative:
                        agg_full["accepted"] = agg_full.groupby("name")["accepted"].cumsum()
                else:
                    agg_full = agg

                # Create chart based on type
                if chart_type == "Bar":
                    fig = px.bar(
                        agg_full, x="bucket", y="accepted", color="name",
                        color_discrete_map=MEMBER_COLORS,
                        labels={"bucket": "Date", "accepted": "Accepted", "name": "Member"},
                        title=f"{'Cumulative ' if cumulative else ''}Accepted Problems — Per Member ({freq})",
                        barmode='group' if not cumulative else 'stack'
                    )
                    fig.update_traces(
                        hovertemplate="<b>%{fullData.name}</b><br>Date=%{x}<br>Accepted=%{y}<extra></extra>"
                    )
                elif chart_type == "Area":
                    fig = px.area(
                        agg_full, x="bucket", y="accepted", color="name",
                        color_discrete_map=MEMBER_COLORS,
                        labels={"bucket": "Date", "accepted": "Accepted", "name": "Member"},
                        title=f"{'Cumulative ' if cumulative else ''}Accepted Problems — Per Member ({freq})"
                    )
                    fig.update_traces(
                        hovertemplate="<b>%{fullData.name}</b><br>Date=%{x}<br>Accepted=%{y}<extra></extra>"
                    )
                else:  # Line
                    fig = px.line(
                        agg_full, x="bucket", y="accepted", color="name", markers=True,
                        color_discrete_map=MEMBER_COLORS,
                        labels={"bucket": "Date", "accepted": "Accepted", "name": "Member"},
                        title=f"{'Cumulative ' if cumulative else ''}Accepted Problems — Per Member ({freq})"
                    )
                    fig.update_traces(
                        mode="lines+markers",
                        hovertemplate="<b>%{fullData.name}</b><br>Date=%{x}<br>Accepted=%{y}<extra></extra>"
                    )

                fig.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    margin=dict(l=20, r=20, t=50, b=80),
                    height=450,
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=-0.35,
                        xanchor="center",
                        x=0.5,
                        title=None
                    )
                )
                st.plotly_chart(fig, use_container_width=True)

# ===================== Team Performance (Accepted) — per-member colors =====================
st.divider()
st.markdown("### 📈 Team Performance (Accepted challenges)")
st.markdown('<div class="leetcode-card">', unsafe_allow_html=True)
perf_df = df[["name", "Accepted"]].sort_values(by="Accepted", ascending=False)

# Use discrete colors per member to keep colors consistent with other charts
fig = px.bar(
    perf_df, x="name", y="Accepted", color="name",
    color_discrete_map=MEMBER_COLORS,
    text="Accepted",
    labels={"name": "Team Members", "Accepted": "Accepted Challenges"},
    title="Team Members — Total Accepted Challenges (Easy + Medium + Hard)"
)
fig.update_layout(
    xaxis_title="Team Members", yaxis_title="Accepted Challenges",
    plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
    margin=dict(l=20, r=20, t=50, b=20), xaxis=dict(tickangle=-45),
    showlegend=False, height=400, title=dict(font=dict(size=16), x=0.5, xanchor="center")
)
fig.update_traces(
    texttemplate="%{text}", textposition="outside",
    marker_line_color="rgba(0,0,0,0.1)", marker_line_width=1,
    textfont=dict(size=12, color="#FFFFFF")
)
st.plotly_chart(fig, use_container_width=True)
st.markdown('</div>', unsafe_allow_html=True)

# ===================== Bottom: Manage Members + Backup/Restore =====================
st.divider()
colA, colB = st.columns([1, 1])

with colA:
    with st.expander("📝 Manage Team Members", expanded=False):
        st.markdown('<div class="leetcode-card">', unsafe_allow_html=True)
        st.markdown("### ➕ Add Member")
        new_name = st.text_input("Full Name", key="add_name")
        new_username = st.text_input("LeetCode Username", key="add_username")
        if st.button("➕ Add Member", use_container_width=True):
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
                    members_now = load_members(user)
                    members_now.append({"name": new_name, "username": new_username})
                    save_members(user, members_now)
                    try:
                        user_data["name"] = new_name
                        user_data["username"] = new_username
                        record_weekly_snapshots(user, [user_data])  # seed snapshot so charts show immediately
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
            if st.button("🗑️ Remove Member", use_container_width=True):
                selected_username = name_to_username[selected_name_rm]
                new_list = [m for m in members_now if m["username"] != selected_username]
                save_members(user, new_list)
                bump_cache_buster()
                st.success(f"✅ Member '{selected_name_rm}' removed successfully!")
                st.rerun()
        else:
            st.info("ℹ️ No members to remove.")
        st.markdown('</div>', unsafe_allow_html=True)

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
        merge_mode = st.checkbox("Merge instead of replace (recommended)", value=True)
        up_members = st.file_uploader("Upload Members JSON", type=["json"], key="up_mem")
        up_history = st.file_uploader("Upload History JSON", type=["json"], key="up_hist")

        if st.button("Restore", type="primary", use_container_width=True):
            try:
                # Members restore
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

                # History restore
                if up_history is not None:
                    uploaded_history = json.load(up_history)
                    current_hist = load_history()
                    incoming = uploaded_history.get(user, uploaded_history.get("history", {}))
                    if not isinstance(incoming, dict):
                        raise ValueError("History JSON must contain an object under your username.")
                    if merge_mode:
                        cur_user_hist = current_hist.get(user, {})
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

# ===================== Footer =====================
st.markdown("---")
st.markdown(
    '<div style="text-align:center; color:var(--text-secondary); font-size:.9rem; padding:1rem 0;">'
    '🚀 Built with Streamlit • 💻 Developed by Laya • 📊 Team Dashboard'
    '</div>',
    unsafe_allow_html=True
)
