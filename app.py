import streamlit as st
import json
from utils.leetcodeapi import fetch_user_data
import os
import pandas as pd
import plotly.express as px
from utils.auth import login, register, get_current_user
import time
from datetime import datetime, date, timedelta

# Backup/Import helpers
import io
import zipfile
import shutil
from pathlib import Path

# -----------------------------
# Constants & paths
# -----------------------------
DATA_DIR = "data"                # folder to back up / restore
DATA_PATH = f"{DATA_DIR}/members.json"
HISTORY_PATH = f"{DATA_DIR}/history.json"  # snapshots (daily + weekly entries)

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
# Persistence: history (daily + weekly)
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

def _extract_counts(member: dict):
    easy = medium = hard = 0
    for s in member.get("submissions", []):
        if s.get("difficulty") == "Easy":
            easy = int(s.get("count", 0))
        elif s.get("difficulty") == "Medium":
            medium = int(s.get("count", 0))
        elif s.get("difficulty") == "Hard":
            hard = int(s.get("count", 0))
    total = int(member.get("totalSolved", 0))
    return total, easy, medium, hard

def record_weekly_snapshots(team_owner: str, team_data: list, when: date | None = None):
    """
    Append a weekly snapshot for each member if not already recorded this week.
    Entry fields: week_start, username, name, totalSolved, Easy, Medium, Hard
    Stored under history[team_owner] = { username: [snapshots...] }
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
        total, easy, medium, hard = _extract_counts(member)

        if username not in history[team_owner]:
            history[team_owner][username] = []

        user_hist = history[team_owner][username]
        if not any(snap.get("week_start") == week_start_str for snap in user_hist):
            user_hist.append({
                "week_start": week_start_str,
                "username": username,
                "name": name,
                "totalSolved": total,
                "Easy": easy,
                "Medium": medium,
                "Hard": hard,
            })
            changed = True

    if changed:
        save_history(history)
    return history

def record_daily_snapshots(team_owner: str, team_data: list, when: date | None = None):
    """
    Append a daily snapshot for each member if not already recorded for that date.
    Entry fields: date, username, name, totalSolved, Easy, Medium, Hard
    Stored under history[team_owner] = { username: [snapshots...] }
    """
    history = load_history()
    if team_owner not in history:
        history[team_owner] = {}

    the_date = when or date.today()
    date_str = the_date.isoformat()
    changed = False

    for member in team_data:
        username = member["username"]
        name = member.get("name", username)
        total, easy, medium, hard = _extract_counts(member)

        if username not in history[team_owner]:
            history[team_owner][username] = []

        user_hist = history[team_owner][username]
        if not any(snap.get("date") == date_str for snap in user_hist):
            user_hist.append({
                "date": date_str,
                "username": username,
                "name": name,
                "totalSolved": total,
                "Easy": easy,
                "Medium": medium,
                "Hard": hard,
            })
            changed = True

    if changed:
        save_history(history)
    return history

# -----------------------------
# Streamlit cache-buster
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
            data.append(user_data)
    return data

# -----------------------------
# Backup & Import helpers
# -----------------------------
def _zip_folder_bytes(folder_path: str) -> bytes:
    """Create an in-memory ZIP of the entire folder (recursively)."""
    buf = io.BytesIO()
    folder = Path(folder_path)
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        if not folder.exists():
            return buf.getvalue()
        for p in folder.rglob("*"):
            if p.is_file():
                zf.write(p, arcname=p.relative_to(folder))
    return buf.getvalue()

def _safe_extract_zip(zf: zipfile.ZipFile, dest_dir: Path):
    """Safely extract a ZIP to dest_dir (prevents zip-slip)."""
    dest_dir = dest_dir.resolve()
    for member in zf.infolist():
        member_path = (dest_dir / member.filename).resolve()
        if not str(member_path).startswith(str(dest_dir)):
            raise ValueError("Unsafe path detected in ZIP (zip-slip attempt).")
        if member.is_dir():
            member_path.mkdir(parents=True, exist_ok=True)
        else:
            member_path.parent.mkdir(parents=True, exist_ok=True)
            with zf.open(member, "r") as src, open(member_path, "wb") as dst:
                shutil.copyfileobj(src, dst)

def create_backup_zip_bytes() -> tuple[bytes, str]:
    """Return (zip_bytes, suggested_filename) for download_button."""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    fn = f"leetcode_dashboard_backup_{ts}.zip"
    zip_bytes = _zip_folder_bytes(DATA_DIR)
    return zip_bytes, fn

def restore_from_zip_filelike(file_like, do_backup_existing: bool = True) -> str:
    """
    Import a .zip into DATA_DIR.
    - Validates archive safely (no zip-slip).
    - Optionally backs up current DATA_DIR before overwrite.
    - Replaces DATA_DIR contents with the zip contents.
    Returns a human-readable status string.
    """
    target_dir = Path(DATA_DIR)
    target_dir.mkdir(parents=True, exist_ok=True)

    backup_msg = ""
    if do_backup_existing and any(target_dir.iterdir()):
        backup_bytes, backup_name = create_backup_zip_bytes()
        backup_path = target_dir / backup_name  # store backup inside data/
        with open(backup_path, "wb") as f:
            f.write(backup_bytes)
        backup_msg = f" (current data backed up to `{backup_path}`)"

    tmp_dir = Path(".tmp_import_data")
    if tmp_dir.exists():
        shutil.rmtree(tmp_dir)
    tmp_dir.mkdir(parents=True, exist_ok=True)

    try:
        with zipfile.ZipFile(file_like) as zf:
            _safe_extract_zip(zf, tmp_dir)

        # Replace DATA_DIR contents with extracted files
        for item in target_dir.iterdir():
            if item.is_dir():
                shutil.rmtree(item)
            else:
                item.unlink()

        for item in tmp_dir.iterdir():
            dest = target_dir / item.name
            shutil.move(str(item), str(dest))

        return "✅ Import completed successfully" + backup_msg

    finally:
        if tmp_dir.exists():
            shutil.rmtree(tmp_dir)

# -----------------------------
# Streamlit page setup & CSS
# -----------------------------
st.set_page_config(
    layout="wide",
    page_title="LeetCode Team Dashboard",
    page_icon="📊"
)

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
    .stats-container { display: flex; justify-content: space-between; flex-wrap: wrap; gap: 1rem; margin-bottom: 1.5rem; }
    .stat-card { background: var(--bg-card); border-radius: 10px; padding: 1.2rem; text-align: center; flex: 1; min-width: 120px; border: 1px solid var(--border-color); box-shadow: 0 2px 4px rgba(0,0,0,0.05); transition: transform .2s ease; }
    .stat-card:hover { transform: translateY(-2px); box-shadow: 0 4px 8px rgba(0,0,0,0.15); }
    .stat-value { font-size: 1.8rem; font-weight: 700; margin: .5rem 0; color: var(--text-primary); }
    .stat-label { color: var(--text-secondary); font-size: .9rem; font-weight: 500; }
    .difficulty-easy { color: var(--leetcode-green) !important; font-weight: 700; }
    .difficulty-medium { color: var(--leetcode-orange) !important; font-weight: 700; }
    .difficulty-hard { color: var(--leetcode-red) !important; font-weight: 700; }
    .stProgress > div > div > div { background-color: var(--leetcode-orange) !important; }
    .welcome-message { color: var(--text-primary) !important; font-size: 1.2rem; margin-bottom: 1rem; }
    .welcome-username { color: var(--leetcode-green) !important; font-weight: 600; }
    .login-card { background: var(--bg-card); border-radius: 12px; border: 1px solid var(--border-color); padding: 2rem; box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
    .login-title { text-align: center; color: var(--leetcode-orange); margin-bottom: 2rem; font-size: 1.5rem; font-weight: 600; }
    footer {visibility: hidden;} #MainMenu {visibility: hidden;} header {visibility: hidden;}
    @media (max-width: 768px) { .header-title { font-size: 2rem; } .stats-container { flex-direction: column; } .stat-card { min-width: 100%; } }
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
                    bump_cache_buster()
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
                    bump_cache_buster()
                    st.success("✅ Registered and logged in!")
                    st.rerun()
                else:
                    st.error("❌ Username already exists.")
            else:
                st.warning("⚠️ Please enter both username and password.")
        st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

user = st.session_state.user

# --- Welcome ---
st.markdown(
    f'<div class="welcome-message">👋 Welcome, <span class="welcome-username">{user}</span>!</div>',
    unsafe_allow_html=True
)

# --- Top controls: refresh, snapshot, logout ---
top_cols = st.columns([6, 1.2, 1.2, 1.2])
with top_cols[1]:
    if st.button("🔄 Refresh data", key="refresh_btn"):
        bump_cache_buster()
        st.toast("Refreshing team data…")
        st.rerun()
with top_cols[2]:
    if st.button("🗂️ Record snapshot now", key="snapshot_btn"):
        bump_cache_buster()
        st.session_state.force_snapshot = True
        st.rerun()
with top_cols[3]:
    if st.button("🚪 Logout", key="logout_btn"):
        st.session_state.user = None
        st.session_state.selected_user = None
        st.rerun()

# --- Load members ---
members = load_members(user)
if not members:
    st.warning("⚠️ No members found for your team.")

# --- Manage Team Members ---
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
                    try:
                        user_data = fetch_user_data(new_username)
                    except Exception:
                        user_data = None
                    if user_data:
                        members.append({"name": new_name, "username": new_username})
                        save_members(user, members)
                        bump_cache_buster()
                        st.success(f"✅ Member '{new_name}' added successfully!")
                        st.rerun()
                    else:
                        st.error("❌ User not found on LeetCode or the API response was invalid.")
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="leetcode-card">', unsafe_allow_html=True)
        st.markdown("### ➖ Remove Member")
        name_to_username = {m["name"]: m["username"] for m in members}
        if name_to_username:
            selected_name_rm = st.selectbox("Select a member to remove", list(name_to_username.keys()))
            if st.button("🗑️ Remove Member", key="remove_member_btn", use_container_width=True):
                selected_username = name_to_username[selected_name_rm]
                members = [m for m in members if m["username"] != selected_username]
                save_members(user, members)
                bump_cache_buster()
                st.success(f"✅ Member '{selected_name_rm}' removed successfully!")
                st.rerun()
        else:
            st.info("ℹ️ No members to remove.")
        st.markdown('</div>', unsafe_allow_html=True)

# --- 📦 Backup & Import ---
with st.expander("📦 Backup & Import", expanded=False):
    st.markdown("Create a full backup of the **data/** folder or restore from a backup zip.")

    # Prepare + Download backup
    col_b1, col_b2 = st.columns([1, 2])
    with col_b1:
        if st.button("🧷 Prepare backup (.zip)"):
            zip_bytes, fname = create_backup_zip_bytes()
            st.session_state["_backup_zip"] = zip_bytes
            st.session_state["_backup_name"] = fname
            st.success("Backup prepared. Click **Download** to save it.")
    with col_b2:
        if "_backup_zip" in st.session_state:
            st.download_button(
                "⬇️ Download backup",
                data=st.session_state["_backup_zip"],
                file_name=st.session_state["_backup_name"],
                mime="application/zip",
                use_container_width=True
            )

    st.divider()

    # Import / Restore
    uploaded_zip = st.file_uploader(
        "Upload a backup .zip to restore your data folder",
        type=["zip"],
        accept_multiple_files=False,
        help="This will replace the contents of the data/ folder."
    )
    col_i1, col_i2 = st.columns([2, 1])
    with col_i1:
        overwrite_ok = st.checkbox(
            "I understand this will overwrite existing data/",
            value=False
        )
        backup_existing = st.checkbox(
            "Backup current data/ before import (recommended)",
            value=True
        )
    with col_i2:
        import_clicked = st.button("♻️ Import backup", use_container_width=True)

    if import_clicked:
        if uploaded_zip is None:
            st.error("Please upload a .zip file first.")
        elif not overwrite_ok:
            st.warning("Please confirm overwrite by checking the box.")
        else:
            try:
                status = restore_from_zip_filelike(uploaded_zip, do_backup_existing=backup_existing)
                st.success(status)
                st.toast("Data restored. Reloading…")
                st.rerun()
            except zipfile.BadZipFile:
                st.error("❌ Not a valid ZIP archive.")
            except ValueError as e:
                st.error(f"❌ Import aborted: {e}")
            except Exception as e:
                st.error(f"❌ Unexpected error: {e}")

# --- Stop if no members ---
if not members:
    st.stop()

# --- Fetch & record snapshots ---
with st.spinner("🔄 Fetching team data from LeetCode..."):
    data = fetch_all_data(members, cache_key=st.session_state.cache_buster)

if not data:
    st.error("❌ Failed to fetch data for team members")
    st.stop()

# Always record daily + weekly (idempotent)
record_daily_snapshots(user, data)
record_weekly_snapshots(user, data)

force_snapshot = st.session_state.pop("force_snapshot", False) if "force_snapshot" in st.session_state else False
if force_snapshot:
    record_daily_snapshots(user, data)
    record_weekly_snapshots(user, data)

# -----------------------------
# Leaderboard (Rank-based) & profile
# -----------------------------
# Sort leaderboard by user Rank (ascending). Non-numeric ranks go last.
def _rank_sort_value(r):
    try:
        # allow "12345" or 12345
        return int(str(r).replace(",", "").strip())
    except Exception:
        # push "N/A" or None to the end
        return 10**12

# Build DF and order by rank, then by totalSolved desc as tiebreaker
df = pd.DataFrame(data)
df["__rank_val"] = df["ranking"].apply(_rank_sort_value)
df_sorted = df.sort_values(by=["__rank_val", "totalSolved"], ascending=[True, False]).drop(columns=["__rank_val"])

left_col, right_col = st.columns([1, 2])
with left_col:
    st.markdown("### 🏆 Leaderboard (by Rank)")
    st.markdown('<div class="leetcode-card">', unsafe_allow_html=True)

    # pick default selected user as top by rank
    selected_user_un = st.session_state.get("selected_user", df_sorted.iloc[0]["username"])

    max_total = max(df_sorted["totalSolved"]) if len(df_sorted) else 0
    for i, row in enumerate(df_sorted.itertuples(index=False), start=1):
        is_selected = (row.username == selected_user_un)
        item_class = "leaderboard-item selected" if is_selected else "leaderboard-item"
        st.markdown(f'<div class="{item_class}">', unsafe_allow_html=True)
        c1, c2 = st.columns([0.22, 0.78])
        with c1:
            st.image(row.avatar, width=42)
        with c2:
            rank_label = f"#{row.ranking}" if str(row.ranking).strip() not in ("", "None", "N/A") else "N/A"
            if st.button(f"{i}. {row.name}  •  Rank {rank_label}", key=f"lb_{row.username}", use_container_width=True):
                st.session_state.selected_user = row.username
                st.rerun()

            # Progress bar based on totalSolved for quick visual (still useful)
            progress = (row.totalSolved / max_total) if max_total > 0 else 0
            st.progress(progress, text=f"🎯 {row.totalSolved} Submissions")

        st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

selected_data = next((item for item in data if item["username"] == selected_user_un), None)

with right_col:
    if selected_data:
        st.markdown(f"""
            <div class="profile-header">
                <div style="display:flex; align-items:center; gap: 20px;">
                    <img src="{selected_data['avatar']}" width="80" style="border-radius:50%; border: 3px solid var(--leetcode-orange);">
                    <div>
                        <h2 style="margin:0; color: var(--text-primary);">{selected_data['name']}</h2>
                        <div style="display:flex; gap:10px; margin-top:8px; flex-wrap: wrap;">
                            <div class="rank-badge">🏅 Rank: {selected_data['ranking']}</div>
                            <div class="solved-badge">✅ Total Submissions: {selected_data['totalSolved']}</div>
                        </div>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)

        def get_difficulty_count(difficulty):
            for d in selected_data["submissions"]:
                if d["difficulty"] == difficulty:
                    return d.get("count", 0)
            return 0

        easy_count = get_difficulty_count("Easy")
        medium_count = get_difficulty_count("Medium")
        hard_count = get_difficulty_count("Hard")

        st.markdown("### 📊 Problems Solved")
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown(f"""<div class="stat-card"><div class="stat-label">Total Submissions</div><div class="stat-value">{selected_data['totalSolved']}</div></div>""", unsafe_allow_html=True)
        with c2:
            st.markdown(f"""<div class="stat-card"><div class="stat-label">Easy</div><div class="stat-value" style="color: var(--leetcode-green);">{easy_count}</div></div>""", unsafe_allow_html=True)
        with c3:
            st.markdown(f"""<div class="stat-card"><div class="stat-label">Medium</div><div class="stat-value" style="color: var(--leetcode-orange);">{medium_count}</div></div>""", unsafe_allow_html=True)
        with c4:
            st.markdown(f"""<div class="stat-card"><div class="stat-label">Hard</div><div class="stat-value" style="color: var(--leetcode-red);">{hard_count}</div></div>""", unsafe_allow_html=True)

        st.markdown("### 🎯 Difficulty Distribution")
        if selected_data['totalSolved'] > 0:
            diff_data = [
                {'difficulty': 'Easy', 'count': easy_count},
                {'difficulty': 'Medium', 'count': medium_count},
                {'difficulty': 'Hard', 'count': hard_count}
            ]
            diff_data = [d for d in diff_data if d['count'] > 0]
            if diff_data:
                fig = px.pie(
                    diff_data,
                    values='count',
                    names='difficulty',
                    color='difficulty',
                    color_discrete_map={'Easy': '#34A853', 'Medium': '#FFA116', 'Hard': '#EF4743'},
                    hole=0.4,
                )
                fig.update_layout(
                    showlegend=True, margin=dict(l=20, r=20, t=30, b=0),
                    legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5, font=dict(size=12)),
                    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(size=12)
                )
                fig.update_traces(textposition='inside', textinfo='percent+label',
                                  hovertemplate="<b>%{label}</b><br>Solved: %{value}<br>Percentage: %{percent}",
                                  textfont=dict(color='#FFFFFF', size=11))
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("📊 No difficulty distribution data available.")
        else:
            st.info("🎯 No problems solved yet!")

# -----------------------------
# 📅 Progress Over Time (Daily / Weekly)
# -----------------------------
st.divider()
st.markdown("### 📅 Progress Over Time (Daily / Weekly)")

raw_hist = load_history()
team_hist = raw_hist.get(user, {})

if not team_hist:
    st.info("No snapshots yet. Use **Refresh data** or **Record snapshot now** to create the first one.")
else:
    # Flatten all snapshots; support both daily ('date') and weekly ('week_start')
    rows = []
    for uname, snaps in team_hist.items():
        for s in snaps:
            rows.append({
                "username": uname,
                "name": s.get("name", uname),
                "date": s.get("date"),                     # may be None for old weekly-only entries
                "week_start": s.get("week_start"),         # may be None for daily-only entries
                "Total": int(s.get("totalSolved", 0)),
                "Easy": int(s.get("Easy", 0)),
                "Medium": int(s.get("Medium", 0)),
                "Hard": int(s.get("Hard", 0)),
            })

    hist_df = pd.DataFrame(rows)
    if hist_df.empty:
        st.info("No snapshots yet.")
    else:
        if "date" in hist_df.columns:
            hist_df["date"] = pd.to_datetime(hist_df["date"], errors="coerce")
        if "week_start" in hist_df.columns:
            hist_df["week_start"] = pd.to_datetime(hist_df["week_start"], errors="coerce")

        # Toggle and metric
        ctrl_cols_top = st.columns([2, 2, 6])
        with ctrl_cols_top[0]:
            granularity = st.radio("Granularity", ["Daily", "Weekly"], horizontal=True, index=0)
        with ctrl_cols_top[1]:
            metric = st.selectbox("Metric", ["Total", "Easy", "Medium", "Hard"], index=0)

        if granularity == "Daily":
            gdf = hist_df.dropna(subset=["date"]).copy()
            if gdf.empty:
                st.info("No daily snapshots yet. They will accumulate after each fetch.")
            else:
                gdf.sort_values(["name", "date"], inplace=True)

                # Clampable date picker defaults
                this_year = date.today().year
                proposed_start = date(this_year, 9, 1)
                min_date = gdf["date"].min().date()
                max_date = gdf["date"].max().date()

                def clamp(d: date, lo: date, hi: date) -> date:
                    if d < lo: return lo
                    if d > hi: return hi
                    return d

                default_start = clamp(proposed_start, min_date, max_date)

                ctrl_cols = st.columns([2, 2, 3, 2])
                with ctrl_cols[0]:
                    start_date = st.date_input(
                        "From date",
                        value=default_start,
                        min_value=min_date,
                        max_value=max_date,
                    )
                with ctrl_cols[1]:
                    people = sorted(gdf["name"].unique().tolist())
                    selected_people = st.multiselect("Members", options=people, default=people)
                with ctrl_cols[2]:
                    show_deltas = st.checkbox("Show day-over-day delta table", value=True)

                fdf = gdf[(gdf["name"].isin(selected_people)) & (gdf["date"] >= pd.Timestamp(start_date))]
                if fdf.empty:
                    st.info("No data for the selected filters.")
                else:
                    chart_df = fdf[["name", "date", metric]].rename(columns={metric: "value"})
                    fig = px.line(
                        chart_df, x="date", y="value", color="name", markers=True,
                        labels={"date": "Date", "value": metric, "name": "Member"},
                        title=f"Daily {metric} Progress"
                    )
                    fig.update_layout(
                        plot_bgcolor='rgba(0,0,0,0)',
                        paper_bgcolor='rgba(0,0,0,0)',
                        margin=dict(l=20, r=20, t=50, b=20),
                        height=420
                    )
                    st.plotly_chart(fig, use_container_width=True)

                    if show_deltas:
                        ddf = fdf.sort_values(["name", "date"]).copy()
                        ddf["prev"] = ddf.groupby("name")[metric].shift(1)
                        ddf["delta"] = ddf[metric] - ddf["prev"]
                        deltas = ddf.dropna(subset=["delta"]).copy()
                        deltas["date"] = deltas["date"].dt.date
                        deltas = deltas[["date", "name", metric, "prev", "delta"]].sort_values(["date", "name"])
                        st.markdown("#### Day-over-Day Changes")
                        st.dataframe(deltas, use_container_width=True)

        else:
            gdf = hist_df.dropna(subset=["week_start"]).copy()
            if gdf.empty:
                st.info("No weekly snapshots yet. They will accumulate after each fetch.")
            else:
                gdf.sort_values(["name", "week_start"], inplace=True)

                this_year = date.today().year
                proposed_start = iso_week_start(date(this_year, 9, 1))  # align to Monday
                min_date = gdf["week_start"].min().date()
                max_date = gdf["week_start"].max().date()

                def clamp(d: date, lo: date, hi: date) -> date:
                    if d < lo: return lo
                    if d > hi: return hi
                    return d

                default_start = clamp(proposed_start, min_date, max_date)

                ctrl_cols = st.columns([2, 2, 3, 2])
                with ctrl_cols[0]:
                    start_date = st.date_input(
                        "From week starting",
                        value=default_start,
                        min_value=min_date,
                        max_value=max_date,
                    )
                with ctrl_cols[1]:
                    people = sorted(gdf["name"].unique().tolist())
                    selected_people = st.multiselect("Members", options=people, default=people)
                with ctrl_cols[2]:
                    show_deltas = st.checkbox("Show week-over-week delta table", value=True)

                fdf = gdf[(gdf["name"].isin(selected_people)) & (gdf["week_start"] >= pd.Timestamp(start_date))]
                if fdf.empty:
                    st.info("No data for the selected filters.")
                else:
                    chart_df = fdf[["name", "week_start", metric]].rename(columns={metric: "value"})
                    fig = px.line(
                        chart_df, x="week_start", y="value", color="name", markers=True,
                        labels={"week_start": "Week Start", "value": metric, "name": "Member"},
                        title=f"Weekly {metric} Progress"
                    )
                    fig.update_layout(
                        plot_bgcolor='rgba(0,0,0,0)',
                        paper_bgcolor='rgba(0,0,0,0)',
                        margin=dict(l=20, r=20, t=50, b=20),
                        height=420
                    )
                    st.plotly_chart(fig, use_container_width=True)

                    if show_deltas:
                        wdf = fdf.sort_values(["name", "week_start"]).copy()
                        wdf["prev"] = wdf.groupby("name")[metric].shift(1)
                        wdf["delta"] = wdf[metric] - wdf["prev"]
                        deltas = wdf.dropna(subset=["delta"]).copy()
                        deltas["week_start"] = deltas["week_start"].dt.date
                        deltas = deltas[["week_start", "name", metric, "prev", "delta"]].sort_values(["week_start", "name"])
                        st.markdown("#### Week-over-Week Changes")
                        st.dataframe(deltas, use_container_width=True)

# -----------------------------
# 📈 Team Performance (still handy)
# -----------------------------
st.divider()
st.markdown("### 📈 Team Performance")
st.markdown('<div class="leetcode-card">', unsafe_allow_html=True)

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
    title=dict(font=dict(size=16), x=0.5, xanchor='center')
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
