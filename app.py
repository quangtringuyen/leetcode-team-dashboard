import streamlit as st
import json
import os
import io
import zipfile
import shutil
import time
import requests
import pandas as pd
import plotly.express as px
from pathlib import Path
from datetime import datetime, date, timedelta

from utils.leetcodeapi import fetch_user_data
from utils.auth import login, register, get_current_user

# =========================================
# Constants & paths
# =========================================
DATA_DIR = "data"
DATA_PATH = f"{DATA_DIR}/members.json"
HISTORY_PATH = f"{DATA_DIR}/history.json"  # stores daily + weekly snapshots (cumulative totals)

LEETCODE_GRAPHQL = "https://leetcode.com/graphql/"

# =========================================
# Persistence: members
# =========================================
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

# =========================================
# Persistence: snapshots history
# =========================================
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
    """Idempotently append weekly cumulative totals per member."""
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
    """Idempotently append daily cumulative totals per member."""
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

# =========================================
# Streamlit cache-buster
# =========================================
def bump_cache_buster():
    st.session_state.cache_buster = time.time()

# =========================================
# Fetch all members data (cached)
# =========================================
@st.cache_data(show_spinner=False)
def fetch_all_data(members, cache_key: float = 0.0):
    """Fetch basic profile stats for each member (utils.leetcodeapi)."""
    data = []
    for member in members:
        user_data = fetch_user_data(member["username"])
        if user_data:
            user_data["name"] = member.get("name", member["username"])
            data.append(user_data)
    return data

# =========================================
# LeetCode Calendar: Daily AC (Accepted) counts
# =========================================
CALENDAR_QUERY_A = """
query userProfileCalendar($username: String!, $year: Int) {
  userProfileCalendar(username: $username, year: $year) {
    submissionCalendar
  }
}
"""

CALENDAR_QUERY_B = """
query userCalendar($username: String!, $year: Int) {
  userCalendar(username: $username, year: $year) {
    submissionCalendar
  }
}
"""

def _calendar_request(payload):
    try:
        resp = requests.post(
            LEETCODE_GRAPHQL,
            json=payload,
            headers={
                "Content-Type": "application/json",
                "Referer": "https://leetcode.com",
                "User-Agent": "Mozilla/5.0",
            },
            timeout=12,
        )
        if resp.status_code != 200:
            return None
        return resp.json()
    except requests.RequestException:
        return None

# ---- REST fallback + GraphQL for reliability ----
def fetch_user_submission_calendar(username: str, year: int | None = None) -> dict[date, int]:
    """
    Returns {date: AC_count} for a given user.
    Tries GraphQL (two schemas), then falls back to public REST endpoint.
    """
    if not username:
        return {}

    # 1) Try GraphQL (A then B)
    def _graphql_try():
        payload = {"query": CALENDAR_QUERY_A, "variables": {"username": username}}
        if year is not None:
            payload["variables"]["year"] = year
        data = _calendar_request(payload)

        calendar_str = None
        if data and data.get("data", {}).get("userProfileCalendar", {}):
            calendar_str = data["data"]["userProfileCalendar"].get("submissionCalendar")

        if not calendar_str:
            payload_b = {"query": CALENDAR_QUERY_B, "variables": {"username": username}}
            if year is not None:
                payload_b["variables"]["year"] = year
            data_b = _calendar_request(payload_b)
            if data_b and data_b.get("data", {}).get("userCalendar", {}):
                calendar_str = data_b["data"]["userCalendar"].get("submissionCalendar")
        return calendar_str

    calendar_str = _graphql_try()

    # 2) Fallback: public REST
    if not calendar_str:
        try:
            url = f"https://leetcode.com/api/user-calendar/?username={username}"
            if year is not None:
                url += f"&year={year}"
            r = requests.get(
                url,
                headers={
                    "User-Agent": "Mozilla/5.0",
                    "Referer": "https://leetcode.com",
                    "Accept": "application/json",
                },
                timeout=12,
            )
            if r.status_code == 200:
                js = r.json()
                calendar_str = js.get("submission_calendar") or js.get("submissionCalendar")
        except requests.RequestException:
            pass

    if not calendar_str:
        return {}

    # Parse the JSON string mapping of unix timestamps -> counts
    try:
        raw_map = json.loads(calendar_str)
    except Exception:
        return {}

    out: dict[date, int] = {}
    for ts_str, cnt in raw_map.items():
        try:
            ts = int(ts_str)
            d = datetime.utcfromtimestamp(ts).date()
            out[d] = int(cnt)
        except Exception:
            continue
    return out

@st.cache_data(show_spinner=False)
def fetch_team_daily_ac_calendars(usernames: list[str], year: int | None = None) -> dict[str, dict]:
    """Cache per-user calendar maps: { username: {date: count, ...}, ... }."""
    result = {}
    for u in usernames:
        result[u] = fetch_user_submission_calendar(u, year=year)
    return result

# =========================================
# Backup & Import helpers (with password gate)
# =========================================
def _zip_folder_bytes(folder_path: str) -> bytes:
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
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    fn = f"leetcode_dashboard_backup_{ts}.zip"
    zip_bytes = _zip_folder_bytes(DATA_DIR)
    return zip_bytes, fn

def restore_from_zip_filelike(file_like, do_backup_existing: bool = True) -> str:
    target_dir = Path(DATA_DIR)
    target_dir.mkdir(parents=True, exist_ok=True)

    backup_msg = ""
    if do_backup_existing and any(target_dir.iterdir()):
        backup_bytes, backup_name = create_backup_zip_bytes()
        backup_path = target_dir / backup_name
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

# =========================================
# Streamlit page setup & CSS
# =========================================
st.set_page_config(layout="wide", page_title="LeetCode Team Dashboard", page_icon="📊")

st.markdown("""
<style>
:root {
    --leetcode-orange: #FFA116;
    --leetcode-green: #34A853;
    --leetcode-red: #EF4743;
    --leetcode-blue: #1E88E5;
    --card-radius: 14px;
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
.main .block-container { padding-top: 1.2rem; padding-bottom: 2rem; }

/* Header */
.header-title {
    color: var(--leetcode-orange) !important; font-weight: 800; font-size: 2.3rem;
    padding-bottom: .4rem; border-bottom: 3px solid #FFA116; margin-bottom: 1rem; text-align: center;
}

/* Cards */
.leetcode-card {
    background: var(--bg-card) !important; border-radius: var(--card-radius);
    border: 1px solid var(--border-color); padding: 1.1rem; box-shadow: 0 2px 6px rgba(0,0,0,0.08);
}

/* New Leaderboard styles */
.lb-card {
    background: linear-gradient(160deg, var(--bg-card), var(--bg-secondary));
    border-radius: var(--card-radius); border: 1px solid var(--border-color);
    padding: 0.8rem 0.9rem; margin-bottom: 10px; transition: transform .12s ease, box-shadow .12s ease;
}
.lb-card:hover { transform: translateY(-2px); box-shadow: 0 6px 12px rgba(0,0,0,0.18); }
.lb-row { display: grid; grid-template-columns: 52px 1fr auto; gap: 12px; align-items: center; }
.lb-rank {
    width: 44px; height: 44px; display:flex; align-items:center; justify-content:center;
    border-radius: 50%; font-weight: 800; color: #fff;
    background: var(--leetcode-orange);
}
.lb-rank.gold { background: linear-gradient(135deg,#f6d365,#fda085); }
.lb-rank.silver { background: linear-gradient(135deg,#bdc3c7,#2c3e50); }
.lb-rank.bronze { background: linear-gradient(135deg,#d1913c,#ffd194); }

.lb-name { font-weight: 700; color: var(--text-primary); }
.lb-sub { color: var(--text-secondary); font-size: .9rem; }
.lb-chip {
    background: rgba(52,168,83, .15); color: var(--leetcode-green);
    padding: 3px 10px; border-radius: 14px; font-size: .8rem; font-weight: 700; border: 1px solid rgba(52,168,83,.35);
}
.lb-btn { width: 100%; text-align:left; background: transparent; border: none; color: var(--text-primary); }
.lb-btn:hover { cursor: pointer; }

/* Badges */
.rank-badge { background: var(--leetcode-orange); color: #fff; border-radius: 18px; padding: 5px 12px; font-weight: 700; display: inline-block; font-size: .9rem; }
.solved-badge { background: var(--leetcode-green); color: #fff; border-radius: 18px; padding: 5px 12px; font-weight: 700; display: inline-block; font-size: .9rem; }

/* Profile */
.profile-header {
    background: linear-gradient(135deg, var(--bg-card) 0%, var(--bg-secondary) 100%);
    border-radius: var(--card-radius); padding: 1.2rem; color: var(--text-primary);
    margin-bottom: 1rem; border: 1px solid var(--border-color);
}

/* Misc */
.stProgress > div > div > div { background-color: var(--leetcode-orange) !important; }
.welcome-message { color: var(--text-primary) !important; font-size: 1.05rem; margin-bottom: .6rem; }
.welcome-username { color: var(--leetcode-green) !important; font-weight: 700; }
footer {visibility: hidden;} #MainMenu {visibility: hidden;} header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# =========================================
# Header
# =========================================
st.markdown('<div class="header-title">👨🏼‍💻 LeetCode Team Dashboard</div>', unsafe_allow_html=True)

# =========================================
# Authentication & session state
# =========================================
if "user" not in st.session_state:
    st.session_state.user = None
if "cache_buster" not in st.session_state:
    st.session_state.cache_buster = 0.0

if st.session_state.user is None:
    st.markdown("<br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.markdown('<div class="leetcode-card">', unsafe_allow_html=True)
        st.subheader("🔐 Login or Register")
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
                st.error("❌ Invalid credentials or missing fields.")
        if b2.button("📝 Register", use_container_width=True):
            if username and password and register(username, password):
                st.session_state.user = username
                bump_cache_buster()
                st.success("✅ Registered and logged in!")
                st.rerun()
            else:
                st.error("❌ Registration failed (maybe username exists?)")
        st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

user = st.session_state.user

# =========================================
# Welcome & top controls
# =========================================
st.markdown(f'<div class="welcome-message">👋 Welcome, <span class="welcome-username">{user}</span>!</div>', unsafe_allow_html=True)
tc1, tc2, tc3, tc4 = st.columns([6, 1.2, 1.6, 1.2])
with tc2:
    if st.button("🔄 Refresh data"):
        bump_cache_buster()
        st.toast("Refreshing team data…")
        st.rerun()
with tc3:
    if st.button("🗂️ Record snapshot now"):
        bump_cache_buster()
        st.session_state.force_snapshot = True
        st.rerun()
with tc4:
    if st.button("🚪 Logout"):
        st.session_state.user = None
        st.session_state.selected_user = None
        st.rerun()

# =========================================
# Members management
# =========================================
members = load_members(user)
if not members:
    st.warning("⚠️ No members found for your team.")

with st.expander("📝 Manage Team Members", expanded=False):
    mc1, mc2 = st.columns(2)
    with mc1:
        st.markdown('<div class="leetcode-card">', unsafe_allow_html=True)
        st.markdown("### ➕ Add Member")
        new_name = st.text_input("Full Name", placeholder="Enter member's full name")
        new_username = st.text_input("LeetCode Username", placeholder="Enter LeetCode username")
        if st.button("➕ Add Member", use_container_width=True, key="add_member_btn"):
            if not new_name or not new_username:
                st.warning("⚠️ Please enter both name and username")
            elif any(m["username"] == new_username for m in members):
                st.warning("⚠️ Member already exists.")
            else:
                with st.spinner("🔍 Verifying LeetCode user..."):
                    try:
                        ud = fetch_user_data(new_username)
                    except Exception:
                        ud = None
                    if ud:
                        members.append({"name": new_name, "username": new_username})
                        save_members(user, members)
                        bump_cache_buster()
                        st.success(f"✅ Member '{new_name}' added successfully!")
                        st.rerun()
                    else:
                        st.error("❌ User not found on LeetCode or the API response was invalid.")
        st.markdown('</div>', unsafe_allow_html=True)

    with mc2:
        st.markdown('<div class="leetcode-card">', unsafe_allow_html=True)
        st.markdown("### ➖ Remove Member")
        name_to_username = {m["name"]: m["username"] for m in members}
        if name_to_username:
            selected_name_rm = st.selectbox("Select a member to remove", list(name_to_username.keys()))
            if st.button("🗑️ Remove Member", use_container_width=True, key="remove_member_btn"):
                selected_username = name_to_username[selected_name_rm]
                members = [m for m in members if m["username"] != selected_username]
                save_members(user, members)
                bump_cache_buster()
                st.success(f"✅ Member '{selected_name_rm}' removed successfully!")
                st.rerun()
        else:
            st.info("ℹ️ No members to remove.")
        st.markdown('</div>', unsafe_allow_html=True)

# =========================================
# 📦 Backup & Import (password required)
# =========================================
with st.expander("📦 Backup & Import (requires password)", expanded=False):
    st.markdown("Create a full backup of the **data/** folder or restore from a backup zip.")
    pw = st.text_input("Enter password to enable backup/restore", type="password", placeholder="••••••")
    is_ok = (pw == "1337code")

    if not is_ok:
        st.info("🔒 Actions are disabled until you enter the correct password.")

    # Prepare + Download backup
    col_b1, col_b2 = st.columns([1, 2])
    with col_b1:
        if st.button("🧷 Prepare backup (.zip)", disabled=not is_ok):
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
                use_container_width=True,
                disabled=not is_ok
            )

    st.divider()

    uploaded_zip = st.file_uploader(
        "Upload a backup .zip to restore your data folder",
        type=["zip"],
        accept_multiple_files=False,
        help="This will replace the contents of the data/ folder."
    )
    ic1, ic2 = st.columns([2, 1])
    with ic1:
        overwrite_ok = st.checkbox("I understand this will overwrite existing data/", value=False, disabled=not is_ok)
        backup_existing = st.checkbox("Backup current data/ before import (recommended)", value=True, disabled=not is_ok)
    with ic2:
        import_clicked = st.button("♻️ Import backup", use_container_width=True, disabled=not is_ok)

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

# =========================================
# Stop if no members
# =========================================
if not members:
    st.stop()

# =========================================
# Fetch & snapshots
# =========================================
with st.spinner("🔄 Fetching team data from LeetCode..."):
    data = fetch_all_data(members, cache_key=st.session_state.cache_buster)

if not data:
    st.error("❌ Failed to fetch data for team members")
    st.stop()

# Idempotent snapshots (cumulative totals)
record_daily_snapshots(user, data)
record_weekly_snapshots(user, data)
if st.session_state.pop("force_snapshot", False):
    record_daily_snapshots(user, data)
    record_weekly_snapshots(user, data)

# Also fetch Daily AC calendars (for “Solved (AC)” time-series)
usernames = [m["username"] for m in members]
calendars_map = fetch_team_daily_ac_calendars(usernames, year=None)  # {username: {date: count}}

# =========================================
# Leaderboard by Rank — Redesigned
# =========================================
def _rank_sort_value(r):
    try:
        return int(str(r).replace(",", "").strip())
    except Exception:
        return 10**12  # push N/A last

df = pd.DataFrame(data)
df["__rank_val"] = df["ranking"].apply(_rank_sort_value)
df_sorted = df.sort_values(by=["__rank_val", "totalSolved"], ascending=[True, False]).drop(columns=["__rank_val"])

# ---------- WoW helpers & robust computation ----------

def _weekify_date(ts: pd.Timestamp) -> pd.Timestamp:
    return ts.to_period("W-MON").start_time

def _weekly_totals_from_daily_snaps(history_for_owner: dict) -> dict[str, pd.DataFrame]:
    """
    Per user, take DAILY cumulative snapshots and reduce to weekly cumulative
    by selecting the LAST daily value in each ISO week.
    Returns { username: DataFrame[week_start, Total] }.
    """
    out = {}
    for uname, snaps in history_for_owner.items():
        rows = [s for s in snaps if s.get("date")]
        if not rows:
            continue
        df_ = pd.DataFrame(rows)
        if df_.empty:
            continue
        df_["date"] = pd.to_datetime(df_["date"], errors="coerce")
        df_ = df_.dropna(subset=["date"])
        if df_.empty:
            continue
        df_["week_start"] = df_["date"].apply(lambda d: _weekify_date(pd.Timestamp(d)))
        df_ = df_.sort_values(["week_start", "date"])
        weekly_last = df_.groupby("week_start", as_index=False).last()[["week_start", "totalSolved"]]
        out[uname] = weekly_last.rename(columns={"totalSolved": "Total"})
    return out

def _weekly_totals_from_calendars(cal_map: dict[str, dict]) -> dict[str, pd.DataFrame]:
    """
    From calendar AC data (per-day accepted counts), build per-user weekly sums.
    Returns { username: DataFrame[week_start, Total] } where 'Total' is weekly AC sum.
    (Not cumulative; perfect fallback for a WoW delta.)
    """
    out = {}
    for uname, daymap in cal_map.items():
        if not daymap:
            continue
        rows = [{"date": pd.to_datetime(d), "ac": int(c)} for d, c in daymap.items()]
        df_ = pd.DataFrame(rows)
        if df_.empty:
            continue
        df_["week_start"] = df_["date"].apply(lambda d: _weekify_date(pd.Timestamp(d)))
        w = df_.groupby("week_start", as_index=False)["ac"].sum().rename(columns={"ac": "Total"})
        out[uname] = w
    return out

def compute_weekly_delta_map(owner: str, cal_map: dict[str, dict]) -> tuple[dict[str, int], pd.DataFrame]:
    """
    Compute WoW delta per user using the best available source, and return a per-user debug table:
      1) Weekly snapshots (cumulative totalSolved)
      2) Derived from DAILY snapshots (last value per week)
      3) Calendar AC sums per week (non-cumulative)
    Returns: (delta_map, debug_df)
    """
    hist_all = load_history()
    hist_owner = hist_all.get(owner, {})

    # Fallback precomputations
    daily_derived = _weekly_totals_from_daily_snaps(hist_owner)
    cal_weekly = _weekly_totals_from_calendars(cal_map)

    def _delta_from_df(wdf: pd.DataFrame):
        """
        Returns (delta, last_two_pairs) where last_two_pairs = [(week1, val1), (week2, val2)]
        """
        if wdf is None or wdf.empty:
            return None, []
        wdf = wdf.dropna(subset=["week_start", "Total"]).copy()
        if wdf.empty:
            return None, []
        wdf["week_start"] = pd.to_datetime(wdf["week_start"], errors="coerce")
        wdf = wdf.dropna(subset=["week_start"]).sort_values("week_start")
        if wdf["week_start"].nunique() < 2:
            return None, []
        last_two = wdf.drop_duplicates("week_start", keep="last").tail(2)
        v1 = int(last_two.iloc[0]["Total"])
        v2 = int(last_two.iloc[-1]["Total"])
        return v2 - v1, [(last_two.iloc[0]["week_start"].date(), v1), (last_two.iloc[-1]["week_start"].date(), v2)]

    delta_map: dict[str, int] = {}
    debug_rows = []

    all_usernames = set(hist_owner.keys()) | set(cal_map.keys())

    for uname in all_usernames:
        source = None
        pair_vals = []

        # 1) weekly snapshots (cumulative)
        weekly_rows = [s for s in hist_owner.get(uname, []) if s.get("week_start")]
        weekly_df = None
        if weekly_rows:
            weekly_df = pd.DataFrame(weekly_rows)[["week_start", "totalSolved"]].rename(columns={"totalSolved": "Total"})
        delta, pair_vals = _delta_from_df(weekly_df)
        if delta is not None:
            source = "weekly_snapshots"
        else:
            # 2) derived from daily snapshots
            delta, pair_vals = _delta_from_df(daily_derived.get(uname))
            if delta is not None:
                source = "derived_daily"
            else:
                # 3) calendar weekly sums (non-cumulative)
                delta, pair_vals = _delta_from_df(cal_weekly.get(uname))
                if delta is not None:
                    source = "calendar_weekly"

        delta_map[uname] = int(delta) if delta is not None else 0

        if pair_vals:
            (w1, v1), (w2, v2) = pair_vals
        else:
            w1 = w2 = v1 = v2 = None
        debug_rows.append({
            "username": uname, "source": source or "none",
            "week1": w1, "value1": v1,
            "week2": w2, "value2": v2,
            "delta": delta_map[uname],
        })

    debug_df = pd.DataFrame(debug_rows).sort_values(["source", "username"])
    return delta_map, debug_df

# compute weekly delta (robust) + diagnostics
weekly_delta, wow_debug_df = compute_weekly_delta_map(user, calendars_map)
selected_user_un = st.session_state.get("selected_user", df_sorted.iloc[0]["username"])

lc1, lc2 = st.columns([1.1, 1.9])

with lc1:
    st.markdown("### 🏆 Leaderboard (by Rank)")
    st.markdown('<div class="leetcode-card">', unsafe_allow_html=True)

    max_total = max(df_sorted["totalSolved"]) if len(df_sorted) else 0
    for i, row in enumerate(df_sorted.itertuples(index=False), start=1):
        medal_class = ""
        if i == 1: medal_class = "gold"
        elif i == 2: medal_class = "silver"
        elif i == 3: medal_class = "bronze"

        rank_label = f"{row.ranking}" if str(row.ranking).strip() not in ("", "None", "N/A") else "—"
        delta_val = weekly_delta.get(row.username, 0)
        delta_text = f"+{delta_val}" if delta_val > 0 else (f"{delta_val}" if delta_val < 0 else "±0")

        st.markdown('<div class="lb-card">', unsafe_allow_html=True)
        col_a, col_b, col_c = st.columns([0.2, 0.62, 0.18])
        with col_a:
            st.markdown(f'<div class="lb-rank {medal_class}">{i}</div>', unsafe_allow_html=True)
        with col_b:
            if st.button(label=f"{row.name}", key=f"lb_btn_{row.username}", use_container_width=True):
                st.session_state.selected_user = row.username
                st.rerun()
            st.caption(f"Rank #{rank_label} • {row.username}")
            progress = (row.totalSolved / max_total) if max_total > 0 else 0
            st.progress(progress, text=f"🎯 {row.totalSolved} total")
        with col_c:
            st.image(row.avatar, width=42)
            st.markdown(f'<div class="lb-chip" style="text-align:center;margin-top:6px;">WoW {delta_text}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

# Diagnostics for WoW
with st.expander("🛠 WoW Diagnostics (why is my WoW zero?)", expanded=False):
    st.write("""
    This table shows which data source was used per user to compute **Week-over-Week (WoW)**,
    and the last two weekly values that were compared.
    Sources (order): **weekly_snapshots** → **derived_daily** → **calendar_weekly** → none.
    """)
    if wow_debug_df is not None and not wow_debug_df.empty:
        st.dataframe(wow_debug_df, use_container_width=True)
    else:
        st.info("No diagnostic data available yet.")

# =========================================
# Right column: Profile of selected user
# =========================================
selected_data = next((item for item in data if item["username"] == selected_user_un), None)

with lc2:
    if selected_data:
        st.markdown(f"""
            <div class="profile-header">
                <div style="display:flex; align-items:center; gap: 16px;">
                    <img src="{selected_data['avatar']}" width="74" style="border-radius:50%; border: 3px solid var(--leetcode-orange);">
                    <div>
                        <h3 style="margin:0; color: var(--text-primary);">{selected_data['name']}</h3>
                        <div style="display:flex; gap:10px; margin-top:6px; flex-wrap: wrap;">
                            <div class="rank-badge">🏅 Rank: {selected_data['ranking']}</div>
                            <div class="solved-badge">✅ Total: {selected_data['totalSolved']}</div>
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

        sc1, sc2, sc3, sc4 = st.columns(4)
        with sc1: st.metric("Total", selected_data["totalSolved"])
        with sc2: st.metric("Easy", easy_count)
        with sc3: st.metric("Medium", medium_count)
        with sc4: st.metric("Hard", hard_count)

        st.markdown("#### 🎯 Difficulty Distribution")
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
                    showlegend=True, margin=dict(l=10, r=10, t=10, b=0),
                    legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5, font=dict(size=12)),
                    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(size=12), height=300
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("📊 No difficulty distribution data available.")
        else:
            st.info("🎯 No problems solved yet!")

# =========================================
# 📅 Progress Over Time (Daily / Weekly) — includes Solved(AC)
# =========================================
st.divider()
st.markdown("### 📅 Progress Over Time (Daily / Weekly)")

def calendars_to_df(cal_maps: dict[str, dict]) -> pd.DataFrame:
    rows = []
    for uname, daymap in cal_maps.items():
        for d, cnt in daymap.items():
            rows.append({"username": uname, "date": pd.to_datetime(d), "SolvedAC": int(cnt)})
    if not rows:
        return pd.DataFrame(columns=["username", "date", "SolvedAC"])
    dfc = pd.DataFrame(rows)
    return dfc

cal_df = calendars_to_df(calendars_map)  # may be empty for users with no data

# Load historical cumulative snapshots
raw_hist = load_history()
team_hist = raw_hist.get(user, {})

snap_rows = []
for uname, snaps in team_hist.items():
    for s in snaps:
        snap_rows.append({
            "username": uname,
            "name": s.get("name", uname),
            "date": s.get("date"),
            "week_start": s.get("week_start"),
            "Total": int(s.get("totalSolved", 0)),
            "Easy": int(s.get("Easy", 0)),
            "Medium": int(s.get("Medium", 0)),
            "Hard": int(s.get("Hard", 0)),
        })
snap_df = pd.DataFrame(snap_rows) if snap_rows else pd.DataFrame(
    columns=["username", "name", "date", "week_start", "Total", "Easy", "Medium", "Hard"]
)
if not snap_df.empty:
    if "date" in snap_df.columns:
        snap_df["date"] = pd.to_datetime(snap_df["date"], errors="coerce")
    if "week_start" in snap_df.columns:
        snap_df["week_start"] = pd.to_datetime(snap_df["week_start"], errors="coerce")

# Controls
ctrl_top = st.columns([2, 2, 5, 3])
with ctrl_top[0]:
    granularity = st.radio("Granularity", ["Daily", "Weekly"], horizontal=True, index=0)
with ctrl_top[1]:
    metric = st.selectbox("Metric", ["Solved (AC)", "Total", "Easy", "Medium", "Hard"], index=0)

# Member mappings
name_to_username = {m.get("name", m["username"]): m["username"] for m in members}
username_to_name = {v: k for k, v in name_to_username.items()}

all_names = sorted(set(m.get("name", m["username"]) for m in members))
with ctrl_top[3]:
    selected_people = st.multiselect("Members", options=all_names, default=all_names)

# DAILY view
if granularity == "Daily":
    if metric == "Solved (AC)":
        gdf = cal_df.copy()
        if gdf.empty:
            st.info("No daily AC calendar data returned yet. It will accumulate on subsequent fetches.")
        else:
            gdf["name"] = gdf["username"].map(username_to_name).fillna(gdf["username"])
            gdf = gdf[gdf["name"].isin(selected_people)]
            if gdf.empty:
                st.info("No data for the selected members.")
            else:
                min_date = gdf["date"].min().date()
                max_date = gdf["date"].max().date()
                this_year = date.today().year
                proposed_start = date(this_year, 9, 1)

                def clamp(d: date, lo: date, hi: date) -> date:
                    if d < lo: return lo
                    if d > hi: return hi
                    return d
                default_start = clamp(proposed_start, min_date, max_date)

                dcol = st.columns([2, 8])
                with dcol[0]:
                    start_date = st.date_input(
                        "From date",
                        value=default_start,
                        min_value=min_date,
                        max_value=max_date,
                    )

                fdf = gdf[gdf["date"] >= pd.Timestamp(start_date)]
                if fdf.empty:
                    st.info("No data for the selected date range.")
                else:
                    fig = px.line(
                        fdf, x="date", y="SolvedAC", color="name", markers=True,
                        labels={"date": "Date", "SolvedAC": "Solved (AC)", "name": "Member"},
                        title="Daily Solved (AC)"
                    )
                    fig.update_layout(
                        plot_bgcolor='rgba(0,0,0,0)',
                        paper_bgcolor='rgba(0,0,0,0)',
                        margin=dict(l=20, r=20, t=50, b=20),
                        height=420
                    )
                    st.plotly_chart(fig, use_container_width=True)

                    show_tbl = st.checkbox("Show daily table", value=False)
                    if show_tbl:
                        tbl = fdf.sort_values(["name", "date"])[["date", "name", "SolvedAC"]]
                        tbl["date"] = tbl["date"].dt.date
                        st.dataframe(tbl, use_container_width=True)
    else:
        gdf = snap_df.dropna(subset=["date"]).copy()
        if gdf.empty:
            st.info("No daily cumulative snapshots yet.")
        else:
            gdf.sort_values(["username", "date"], inplace=True)
            gdf["name"] = gdf["name"].fillna(gdf["username"])
            gdf = gdf[gdf["name"].isin(selected_people)]
            if gdf.empty:
                st.info("No data for the selected members.")
            else:
                min_date = gdf["date"].min().date()
                max_date = gdf["date"].max().date()
                this_year = date.today().year
                proposed_start = date(this_year, 9, 1)

                def clamp(d: date, lo: date, hi: date) -> date:
                    if d < lo: return lo
                    if d > hi: return hi
                    return d
                default_start = clamp(proposed_start, min_date, max_date)

                start_date = st.date_input(
                    "From date",
                    value=default_start,
                    min_value=min_date,
                    max_value=max_date,
                )
                fdf = gdf[gdf["date"] >= pd.Timestamp(start_date)]
                if fdf.empty:
                    st.info("No data for the selected date range.")
                else:
                    chart_df = fdf[["name", "date", metric]].rename(columns={metric: "value"})
                    fig = px.line(
                        chart_df, x="date", y="value", color="name", markers=True,
                        labels={"date": "Date", "value": metric, "name": "Member"},
                        title=f"Daily {metric} (cumulative)"
                    )
                    fig.update_layout(
                        plot_bgcolor='rgba(0,0,0,0)',
                        paper_bgcolor='rgba(0,0,0,0)',
                        margin=dict(l=20, r=20, t=50, b=20),
                        height=420
                    )
                    st.plotly_chart(fig, use_container_width=True)

# WEEKLY view
else:
    if metric == "Solved (AC)":
        if cal_df.empty:
            st.info("No calendar data to aggregate yet.")
        else:
            cal_df["week_start"] = cal_df["date"].dt.to_period("W-MON").apply(lambda p: p.start_time)
            cal_df["name"] = cal_df["username"].map(username_to_name).fillna(cal_df["username"])
            gdf = cal_df[cal_df["name"].isin(selected_people)].copy()
            if gdf.empty:
                st.info("No data for the selected members.")
            else:
                agg = gdf.groupby(["name", "week_start"], as_index=False)["SolvedAC"].sum()
                min_date = agg["week_start"].min().date()
                max_date = agg["week_start"].max().date()
                this_year = date.today().year
                proposed_start = iso_week_start(date(this_year, 9, 1))

                def clamp(d: date, lo: date, hi: date) -> date:
                    if d < lo: return lo
                    if d > hi: return hi
                    return d
                default_start = clamp(proposed_start, min_date, max_date)

                start_date = st.date_input(
                    "From week starting",
                    value=default_start,
                    min_value=min_date,
                    max_value=max_date,
                )
                fdf = agg[agg["week_start"] >= pd.Timestamp(start_date)]
                if fdf.empty:
                    st.info("No data for the selected date range.")
                else:
                    fig = px.line(
                        fdf, x="week_start", y="SolvedAC", color="name", markers=True,
                        labels={"week_start": "Week Start", "SolvedAC": "Solved (AC)", "name": "Member"},
                        title="Weekly Solved (AC)"
                    )
                    fig.update_layout(
                        plot_bgcolor='rgba(0,0,0,0)',
                        paper_bgcolor='rgba(0,0,0,0)',
                        margin=dict(l=20, r=20, t=50, b=20),
                        height=420
                    )
                    st.plotly_chart(fig, use_container_width=True)

                    show_tbl = st.checkbox("Show weekly table", value=False)
                    if show_tbl:
                        tbl = fdf.sort_values(["name", "week_start"]).copy()
                        tbl["week_start"] = tbl["week_start"].dt.date
                        st.dataframe(tbl, use_container_width=True)
    else:
        gdf = snap_df.dropna(subset=["week_start"]).copy()
        if gdf.empty:
            st.info("No weekly cumulative snapshots yet.")
        else:
            gdf.sort_values(["username", "week_start"], inplace=True)
            gdf["name"] = gdf["name"].fillna(gdf["username"])
            gdf = gdf[gdf["name"].isin(selected_people)]
            if gdf.empty:
                st.info("No data for the selected members.")
            else:
                min_date = gdf["week_start"].min().date()
                max_date = gdf["week_start"].max().date()
                this_year = date.today().year
                proposed_start = iso_week_start(date(this_year, 9, 1))

                def clamp(d: date, lo: date, hi: date) -> date:
                    if d < lo: return lo
                    if d > hi: return hi
                    return d
                default_start = clamp(proposed_start, min_date, max_date)

                start_date = st.date_input(
                    "From week starting",
                    value=default_start,
                    min_value=min_date,
                    max_value=max_date,
                )
                fdf = gdf[gdf["week_start"] >= pd.Timestamp(start_date)]
                if fdf.empty:
                    st.info("No data for the selected date range.")
                else:
                    chart_df = fdf[["name", "week_start", metric]].rename(columns={metric: "value"})
                    fig = px.line(
                        chart_df, x="week_start", y="value", color="name", markers=True,
                        labels={"week_start": "Week Start", "value": metric, "name": "Member"},
                        title=f"Weekly {metric} (cumulative)"
                    )
                    fig.update_layout(
                        plot_bgcolor='rgba(0,0,0,0)',
                        paper_bgcolor='rgba(0,0,0,0)',
                        margin=dict(l=20, r=20, t=50, b=20),
                        height=420
                    )
                    st.plotly_chart(fig, use_container_width=True)

# =========================================
# ✅ Weekly Progress (Cumulative) — per your spec
# =========================================
st.divider()
st.markdown("### ✅ Weekly Progress (Cumulative)")

# Build a weekly-only frame from snapshots
weekly_rows = []
for uname, snaps in team_hist.items():
    for s in snaps:
        if s.get("week_start"):
            weekly_rows.append({
                "username": uname,
                "name": s.get("name", uname),
                "week_start": s.get("week_start"),
                "Total": int(s.get("totalSolved", 0)),
                "Easy": int(s.get("Easy", 0)),
                "Medium": int(s.get("Medium", 0)),
                "Hard": int(s.get("Hard", 0)),
            })

weekly_df = pd.DataFrame(weekly_rows)
if weekly_df.empty:
    st.info("No weekly snapshots yet. Use **Refresh data** or **Record snapshot now** to create the first one.")
else:
    weekly_df["week_start"] = pd.to_datetime(weekly_df["week_start"], errors="coerce")
    weekly_df.sort_values(["name", "week_start"], inplace=True)

    wc1, wc2, wc3 = st.columns([2, 2, 3])
    with wc1:
        wk_metric = st.selectbox("Metric", ["Total", "Easy", "Medium", "Hard"], index=0, key="wk_metric")
    with wc2:
        this_year = date.today().year
        proposed_start = iso_week_start(date(this_year, 9, 1))
        min_date = weekly_df["week_start"].min().date()
        max_date = weekly_df["week_start"].max().date()

        def clamp(d: date, lo: date, hi: date) -> date:
            if d < lo: return lo
            if d > hi: return hi
            return d
        default_start = clamp(proposed_start, min_date, max_date)

        wk_start = st.date_input(
            "From week starting",
            value=default_start,
            min_value=min_date,
            max_value=max_date,
            key="wk_start_date"
        )
    with wc3:
        people = sorted(weekly_df["name"].unique().tolist())
        wk_people = st.multiselect("Members", options=people, default=people, key="wk_people")

    wdf = weekly_df[
        (weekly_df["name"].isin(wk_people)) &
        (weekly_df["week_start"] >= pd.Timestamp(wk_start))
    ]
    if wdf.empty:
        st.info("No data for the selected filters.")
    else:
        chart_df = wdf[["name", "week_start", wk_metric]].rename(columns={wk_metric: "value"})
        fig = px.line(
            chart_df, x="week_start", y="value", color="name", markers=True,
            labels={"week_start": "Week Start", "value": wk_metric, "name": "Member"},
            title=f"Weekly {wk_metric} (cumulative)"
        )
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=20, r=20, t=50, b=20),
            height=420
        )
        st.plotly_chart(fig, use_container_width=True)

        # Week-over-week deltas table
        wdf2 = wdf.sort_values(["name", "week_start"]).copy()
        wdf2["prev"] = wdf2.groupby("name")[wk_metric].shift(1)
        wdf2["delta"] = wdf2[wk_metric] - wdf2["prev"]
        deltas = wdf2.dropna(subset=["delta"]).copy()
        deltas["week_start"] = deltas["week_start"].dt.date
        deltas = deltas[["week_start", "name", wk_metric, "prev", "delta"]].sort_values(["week_start", "name"])
        st.markdown("#### Week-over-Week Changes")
        st.dataframe(deltas, use_container_width=True)

# =========================================
# 📈 Team Performance
# =========================================
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

# =========================================
# Footer
# =========================================
st.markdown("---")
st.markdown(
    '<div style="text-align: center; color: var(--text-secondary); font-size: 0.9rem; padding: 1rem 0;">'
    '🚀 Built with Streamlit • 💻 Developed By Laya • 📊 Team Dashboard'
    '</div>',
    unsafe_allow_html=True
)
