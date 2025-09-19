# ui/components.py
from __future__ import annotations
import streamlit as st
import plotly.express as px
import pandas as pd

def inject_base_css():
    st.markdown("""
        <style>
        :root { --leetcode-orange:#FFA116; --leetcode-green:#34A853; --leetcode-red:#EF4743; --leetcode-blue:#1E88E5; }
        [data-theme="dark"] { --bg-primary:#0E1117; --bg-secondary:#262730; --bg-card:#1E1E1E; --text-primary:#FAFAFA; --text-secondary:#A0A0A0; --border-color:#333; --hover-bg:#2A2A2A; }
        [data-theme="light"] { --bg-primary:#FFFFFF; --bg-secondary:#F0F2F6; --bg-card:#FFFFFF; --text-primary:#262730; --text-secondary:#6C757D; --border-color:#E0E0E0; --hover-bg:#F8F9FA; }
        .header-title { color: var(--leetcode-orange)!important; font-weight:700; font-size:2.5rem; padding-bottom:.5rem; border-bottom:3px solid #FFA116; margin-bottom:1.5rem; text-align:center; }
        .leetcode-card { background: var(--bg-card)!important; border-radius:12px; border:1px solid var(--border-color); padding:1.5rem; margin-bottom:1.5rem; }
        .leaderboard-item { transition: all .3s ease; border-radius:8px; padding:12px; margin-bottom:8px; background: var(--bg-card); border:1px solid var(--border-color); cursor:pointer; }
        .leaderboard-item.selected { background: rgba(255,161,22,.15); border-left:4px solid var(--leetcode-orange); }
        .stat-card { background:var(--bg-card); border-radius:10px; padding:1.2rem; text-align:center; border:1px solid var(--border-color); }
        .stat-label { color: var(--text-secondary); font-size:.9rem; font-weight:500; }
        .stat-value { font-size:1.8rem; font-weight:700; margin:.5rem 0; color:var(--text-primary); }
        .stProgress>div>div>div { background-color: var(--leetcode-orange)!important; }
        footer, #MainMenu, header { visibility:hidden; }
        </style>
    """, unsafe_allow_html=True)

def leaderboard(df_sorted, selected_user_un):
    st.markdown("### 🏆 Leaderboard")
    st.markdown('<div class="leetcode-card">', unsafe_allow_html=True)
    max_ac = int(df_sorted["Accepted"].max()) if not df_sorted.empty else 0
    ret_selected = selected_user_un
    for i, row in enumerate(df_sorted.itertuples(index=False), start=1):
        is_sel = (row.username == selected_user_un)
        item_class = "leaderboard-item selected" if is_sel else "leaderboard-item"
        st.markdown(f'<div class="{item_class}">', unsafe_allow_html=True)
        c1, c2 = st.columns([0.2, 0.8])
        with c1:
            st.image(row.avatar, width=40)
        with c2:
            if st.button(f"#{i} {row.name}", key=f"lb_{row.username}", use_container_width=True):
                ret_selected = row.username
            progress = (row.Accepted / max_ac) if max_ac > 0 else 0
            st.progress(progress, text=f"🎯 {row.Accepted} Accepted")
        st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    return ret_selected

def pie_difficulty(easy, med, hard, title="Accepted by Difficulty"):
    if (easy + med + hard) == 0:
        st.info("🎯 No accepted challenges yet!")
        return
    fig = px.pie(
        [{"difficulty":"Easy","count":easy},{"difficulty":"Medium","count":med},{"difficulty":"Hard","count":hard}],
        values="count", names="difficulty",
        color="difficulty",
        color_discrete_map={'Easy': '#34A853', 'Medium': '#FFA116', 'Hard': '#EF4743'},
        hole=0.4,
    )
    fig.update_layout(height=520, showlegend=True, margin=dict(l=20, r=20, t=30, b=0),
                      legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5, font=dict(size=13)),
                      paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(size=13))
    fig.update_traces(textposition='inside', textinfo='percent+label',
                      hovertemplate="<b>%{label}</b><br>Accepted: %{value}<br>Percentage: %{percent}",
                      textfont=dict(color='#FFFFFF', size=13))
    st.plotly_chart(fig, use_container_width=True)

def team_bar(perf_df):
    fig = px.bar(
        perf_df, x="name", y="Accepted", color="Accepted",
        color_continuous_scale=[(0, "#FFA116"), (1, "#34A853")],
        text="Accepted", labels={"name":"Team Members","Accepted":"Accepted Challenges"},
        title="Team Members — Total Accepted Challenges (Easy + Medium + Hard)"
    )
    fig.update_layout(xaxis_title="Team Members", yaxis_title="Accepted Challenges",
                      plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                      margin=dict(l=20, r=20, t=50, b=20), xaxis=dict(tickangle=-45),
                      showlegend=False, height=400, title=dict(font=dict(size=16), x=0.5, xanchor="center"))
    fig.update_traces(texttemplate="%{text}", textposition="outside",
                      marker_line_color="rgba(0,0,0,0.1)", marker_line_width=1,
                      textfont=dict(size=12, color="#FFFFFF"))
    st.plotly_chart(fig, use_container_width=True)
