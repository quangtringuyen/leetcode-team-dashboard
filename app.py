import streamlit as st
import pandas as pd
from datetime import date, timedelta
import plotly.express as px

from core.storage import choose_storage
from services.auth_service import AuthManager
from services.members_service import MembersService
from services.history_service import HistoryService, iso_week_start
from services.leetcode_service import LeetCodeService
from ui.components import inject_base_css, leaderboard, pie_difficulty, team_bar

st.set_page_config(layout="wide", page_title="LeetCode Team Dashboard", page_icon="📊")
inject_base_css()
st.markdown('<div class="header-title">👨🏼‍💻 LeetCode Team Dashboard</div>', unsafe_allow_html=True)

# ----------------- init services -----------------
storage = choose_storage()
auth = AuthManager()
members_svc = MembersService(storage)
history_svc = HistoryService(storage)
leet = LeetCodeService()

st.caption(f"Storage: **{'S3' if storage.__class__.__name__=='S3Storage' else 'Local files'}**")

# Diagnostics block (migrate and view users)
auth.render_users_diagnostics()

# Authenticate
user, ok = auth.authenticate()
if not ok:
    st.stop()

# Session cache-buster
if "cache_buster" not in st.session_state:
    st.session_state.cache_buster = 0.0
def bump_cache():
    st.session_state.cache_buster = st.session_state.get("cache_buster", 0.0) + 1.0

# Top controls
tc = st.columns([8, 1.2, 1.6])
with tc[1]:
    if st.button("🔄 Refresh data"):
        bump_cache()
        st.rerun()
with tc[2]:
    if st.button("🗂️ Record snapshot now"):
        st.session_state.force_snapshot = True
        st.rerun()

# Load members & fetch data
members = members_svc.load_members(user)
if not members:
    st.warning("⚠️ No members found for your team.")

with st.spinner("🔄 Fetching team data from LeetCode..."):
    data = leet.fetch_all(members, cache_key=st.session_state.cache_buster)

if not data:
    st.error("❌ Failed to fetch data for team members")
    st.stop()

# Record weekly snapshots (idempotent), optional forced snapshot
history_svc.record_weekly(user, data)
if st.session_state.pop("force_snapshot", False):
    history_svc.record_weekly(user, data)

# Build current DF
df = pd.DataFrame(data)
df["Accepted"] = df["submissions"].apply(leet.sum_accepted)
df_sorted = df.sort_values(by="Accepted", ascending=False)

# Left: leaderboard | Right: profile
left, right = st.columns([1, 2])
with left:
    selected_user = st.session_state.get("selected_user", df_sorted.iloc[0]["username"])
    new_sel = leaderboard(df_sorted, selected_user)
    if new_sel != selected_user:
        st.session_state.selected_user = new_sel
        st.rerun()

with right:
    selected_user = st.session_state.get("selected_user", df_sorted.iloc[0]["username"])
    sel = df[df["username"] == selected_user].iloc[0] if not df.empty else None
    if sel is not None:
        # header
        sel_ac = int(sel["Accepted"])
        st.markdown(f"""
            <div class="leetcode-card" style="background:linear-gradient(135deg, var(--bg-card), var(--bg-secondary));">
              <div style="display:flex; align-items:center; gap:20px;">
                <img src="{sel['avatar']}" width="80" style="border-radius:50%; border:3px solid var(--leetcode-orange);">
                <div>
                  <h2 style="margin:0;">{sel['name']}</h2>
                  <div style="display:flex; gap:10px; margin-top:8px; flex-wrap:wrap;">
                    <div class="stat-card"><div class="stat-label">Rank</div><div class="stat-value">{sel['ranking']}</div></div>
                    <div class="stat-card"><div class="stat-label">Accepted (Total)</div><div class="stat-value">{sel_ac}</div></div>
                  </div>
                </div>
              </div>
            </div>
        """, unsafe_allow_html=True)

        def dcount(diff):
            for s in sel["submissions"]:
                if s.get("difficulty") == diff:
                    return int(s.get("count", 0))
            return 0

        easy, med, hard = dcount("Easy"), dcount("Medium"), dcount("Hard")
        c1, c2, c3, c4 = st.columns(4)
        with c1: st.markdown(f'<div class="stat-card"><div class="stat-label">Accepted (Total)</div><div class="stat-value">{sel_ac}</div></div>', unsafe_allow_html=True)
        with c2: st.markdown(f'<div class="stat-card"><div class="stat-label">Easy</div><div class="stat-value" style="color:#34A853">{easy}</div></div>', unsafe_allow_html=True)
        with c3: st.markdown(f'<div class="stat-card"><div class="stat-label">Medium</div><div class="stat-value" style="color:#FFA116">{med}</div></div>', unsafe_allow_html=True)
        with c4: st.markdown(f'<div class="stat-card"><div class="stat-label">Hard</div><div class="stat-value" style="color:#EF4743">{hard}</div></div>', unsafe_allow_html=True)
        pie_difficulty(easy, med, hard)

# ---------------- Weekly Progress ----------------
st.divider()
st.markdown("### 📅 Weekly Progress (since September)")

# ensure everyone appears in roster (seed on miss)
hist = history_svc.load_history().get(user, {})
known_unames = set(hist.keys())
current_unames = {m["username"] for m in members}
if not hist or (current_unames - known_unames):
    hist = history_svc.record_weekly(user, data).get(user, {})

name_by_un = {m["username"]: m.get("name", m["username"]) for m in members}
all_names = sorted(name_by_un.values())

rows = []
for uname, snaps in hist.items():
    for s in snaps:
        rows.append({
            "username": uname,
            "name": name_by_un.get(uname, s.get("name", uname)),
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
        selected_people = st.multiselect("Members", options=all_names, default=all_names)
    with cc[3]:
        show_deltas = st.checkbox("Show Week-over-Week Changes (Accepted)", value=True)

    f_hist = hist_df[hist_df["week_start"] >= pd.Timestamp(start_date)].copy()
    if f_hist.empty:
        st.info("No data for the selected start date yet.")
    else:
        start_mon = pd.Timestamp(start_date) - pd.Timedelta(days=pd.Timestamp(start_date).weekday())
        end_mon = f_hist["week_start"].max()
        weeks = pd.date_range(start=start_mon, end=end_mon, freq="W-MON")
        full_index = pd.MultiIndex.from_product([selected_people, weeks], names=["name", "week_start"])

        chart_df = f_hist[["name", "week_start", metric]].set_index(["name", "week_start"]).sortIndex()
        # fix typo: Streamlit safe
        chart_df = chart_df.sort_index()
        chart_df = chart_df.reindex(full_index)
        chart_df = chart_df.groupby(level=0)[metric].ffill().fillna(0.0).to_frame("value").reset_index()

        fig = px.line(chart_df, x="week_start", y="value", color="name", markers=True,
                      labels={"week_start":"Week Start","value":metric,"name":"Member"},
                      title=f"Weekly {metric} Progress (Cumulative)")
        fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                          margin=dict(l=20, r=20, t=50, b=20), height=420)
        st.plotly_chart(fig, use_container_width=True)

        if show_deltas:
            ac_df = f_hist[["name","week_start","Accepted"]].set_index(["name","week_start"]).sort_index()
            ac_df = ac_df.reindex(full_index)
            ac_df = ac_df.groupby(level=0)["Accepted"].ffill().fillna(0.0).to_frame("Accepted").reset_index()

            ac_df_sorted = ac_df.sort_values(["week_start","Accepted"], ascending=[True, False])
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

# ---------------- Accepted trend by date ----------------
st.divider()
st.markdown("### 📈 Accepted Trend by Date")
if not members:
    st.info("No members to chart.")
else:
    with st.spinner("Gathering calendars…"):
        cal_df = leet.calendars_to_frame(members)
    if cal_df.empty:
        st.info("No calendar data available yet.")
    else:
        all_names = sorted(cal_df["name"].unique().tolist())
        c1, c2, c3, c4 = st.columns([2,2,2,2])
        with c1:
            trend_people = st.multiselect("Members", options=all_names, default=all_names, key="trend_people")
        with c2:
            freq = st.selectbox("Granularity", ["Daily","Weekly","Monthly"], index=1, key="trend_freq")
        with c3:
            cumulative = st.checkbox("Cumulative", value=False, key="trend_cum")
        with c4:
            mode = st.selectbox("Series", ["Per member","Team total"], index=0, key="trend_mode")

        if trend_people:
            df_tr = cal_df[cal_df["name"].isin(trend_people)].copy()
            if freq == "Daily":
                df_tr["bucket"] = df_tr["date"].dt.to_period("D").dt.to_timestamp(); freq_code="D"
            elif freq == "Weekly":
                df_tr["bucket"] = (df_tr["date"] - pd.to_timedelta(df_tr["date"].dt.dayofweek, unit="D"))
                df_tr["bucket"] = pd.to_datetime(df_tr["bucket"].dt.date); freq_code="W-MON"
            else:
                df_tr["bucket"] = df_tr["date"].dt.to_period("M").dt.to_timestamp(); freq_code="MS"

            if mode == "Team total":
                agg = df_tr.groupby(["bucket"], as_index=False)["accepted"].sum().sort_values("bucket")
                full_idx = pd.date_range(agg["bucket"].min(), agg["bucket"].max(), freq=freq_code)
                agg = agg.set_index("bucket").reindex(full_idx, fill_value=0).rename_axis("bucket").reset_index()
                if cumulative: agg["accepted"] = agg["accepted"].cumsum()
                fig = px.line(agg, x="bucket", y="accepted", markers=True,
                              labels={"bucket":"Date","accepted":"Accepted"},
                              title=f"{'Cumulative ' if cumulative else ''}Accepted — Team ({freq.lower()})")
                fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                                  margin=dict(l=20, r=20, t=50, b=20), height=420)
                st.plotly_chart(fig, use_container_width=True)
            else:
                agg = df_tr.groupby(["name","bucket"], as_index=False)["accepted"].sum()
                min_b, max_b = agg["bucket"].min(), agg["bucket"].max()
                full_b = pd.date_range(min_b, max_b, freq=freq_code)
                full_index = pd.MultiIndex.from_product([trend_people, full_b], names=["name","bucket"])
                agg_full = agg.set_index(["name","bucket"]).reindex(full_index, fill_value=0).reset_index()
                if cumulative: agg_full["accepted"] = agg_full.groupby("name")["accepted"].cumsum()
                fig = px.line(agg_full, x="bucket", y="accepted", color="name", markers=True,
                              labels={"bucket":"Date","accepted":"Accepted","name":"Member"},
                              title=f"{'Cumulative ' if cumulative else ''}Accepted — Per Member ({freq.lower()})")
                fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                                  margin=dict(l=20, r=20, t=50, b=20), height=420)
                st.plotly_chart(fig, use_container_width=True)

# ---------------- Team Performance ----------------
st.divider()
st.markdown("### 📈 Team Performance (Accepted challenges)")
st.markdown('<div class="leetcode-card">', unsafe_allow_html=True)
team_bar(df[["name","Accepted"]].sort_values(by="Accepted", ascending=False))
st.markdown('</div>', unsafe_allow_html=True)

# ---------------- Manage + Backup/Restore ----------------
st.divider()
colA, colB = st.columns([1,1])

with colA:
    with st.expander("📝 Manage Team Members", expanded=False):
        st.markdown('<div class="leetcode-card">', unsafe_allow_html=True)
        new_name = st.text_input("Full Name", key="add_name")
        new_username = st.text_input("LeetCode Username", key="add_username")
        if st.button("➕ Add Member", use_container_width=True):
            if not new_name or not new_username:
                st.warning("Enter both name and username.")
            elif any(m["username"] == new_username for m in members):
                st.warning("Member already exists.")
            else:
                from utils.leetcodeapi import fetch_user_data
                with st.spinner("Verifying LeetCode user..."):
                    ud = fetch_user_data(new_username)
                if ud:
                    ok = members_svc.add_member(user, new_name, new_username)
                    if ok:
                        # seed snapshot so charts show immediately
                        ud["name"] = new_name; ud["username"] = new_username
                        history_svc.record_weekly(user, [ud])
                        st.success("Member added."); st.rerun()
                    else:
                        st.warning("Member already exists.")
                else:
                    st.error("User not found on LeetCode.")
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="leetcode-card">', unsafe_allow_html=True)
        st.markdown("### ➖ Remove Member")
        members_now = members_svc.load_members(user)
        name_to_username = {m["name"]: m["username"] for m in members_now}
        if name_to_username:
            rm_name = st.selectbox("Select a member to remove", list(name_to_username.keys()))
            if st.button("🗑️ Remove Member", use_container_width=True):
                members_svc.remove_member(user, name_to_username[rm_name])
                st.success("Removed."); st.rerun()
        else:
            st.info("No members to remove.")
        st.markdown('</div>', unsafe_allow_html=True)

with colB:
    with st.expander("🧰 Backup & Restore", expanded=False):
        st.markdown('<div class="leetcode-card">', unsafe_allow_html=True)
        # backup
        members_payload = pd.io.json.dumps({user: members_svc.load_members(user)}, indent=2)
        history_payload = pd.io.json.dumps({user: history_svc.load_history().get(user, {})}, indent=2)
        st.download_button("⬇️ Download Members JSON", data=members_payload, file_name=f"{user}_members_backup.json", mime="application/json", use_container_width=True)
        st.download_button("⬇️ Download History JSON", data=history_payload, file_name=f"{user}_history_backup.json", mime="application/json", use_container_width=True)

        # restore
        merge_mode = st.checkbox("Merge instead of replace (recommended)", value=True)
        up_members = st.file_uploader("Upload Members JSON", type=["json"], key="up_mem")
        up_history = st.file_uploader("Upload History JSON", type=["json"], key="up_hist")

        import json as _json
        if st.button("Restore", type="primary", use_container_width=True):
            try:
                # members
                if up_members is not None:
                    uploaded_members = _json.load(up_members)
                    uploaded_list = uploaded_members.get(user, uploaded_members.get("members", uploaded_members.get("data", [])))
                    if not isinstance(uploaded_list, list):
                        raise ValueError("Members JSON must contain a list under your username.")
                    if merge_mode:
                        cur = {m["username"]: m for m in members_svc.load_members(user)}
                        for m in uploaded_list:
                            cur[m["username"]] = {"username": m["username"], "name": m.get("name", m["username"])}
                        members_svc.save_members(user, list(cur.values()))
                    else:
                        members_svc.save_members(user, [{"username": m["username"], "name": m.get("name", m["username"])} for m in uploaded_list])

                # history
                if up_history is not None:
                    uploaded_history = _json.load(up_history)
                    current_hist = history_svc.load_history()
                    incoming = uploaded_history.get(user, uploaded_history.get("history", {}))
                    if not isinstance(incoming, dict):
                        raise ValueError("History JSON must contain an object under your username.")
                    if merge_mode:
                        cur_user_hist = current_hist.get(user, {})
                        for uname, snaps in incoming.items():
                            cur_user_hist.setdefault(uname, [])
                            exist_weeks = {s["week_start"] for s in cur_user_hist[uname] if "week_start" in s}
                            for s in snaps:
                                if s.get("week_start") not in exist_weeks:
                                    cur_user_hist[uname].append(s)
                        current_hist[user] = cur_user_hist
                    else:
                        current_hist[user] = incoming
                    history_svc.save_history(current_hist)

                st.success("✅ Restore completed."); st.rerun()
            except Exception as e:
                st.error(f"❌ Restore failed: {e}")

# Footer
st.markdown("---")
st.markdown('<div style="text-align:center; color:var(--text-secondary); font-size:.9rem; padding:1rem 0;">🚀 Built with Streamlit • 💻 Developed by Laya • 📊 Team Dashboard</div>', unsafe_allow_html=True)
