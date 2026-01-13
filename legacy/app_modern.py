"""
LeetCode Team Dashboard - Modern Redesign
Multi-page app with modern UI components and layout
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import date, timedelta, datetime
import os
import json

# Modern UI imports
try:
    from streamlit_option_menu import option_menu
    from streamlit_extras.metric_cards import style_metric_cards
    from streamlit_extras.colored_header import colored_header
    from streamlit_extras.add_vertical_space import add_vertical_space
    MODERN_COMPONENTS_AVAILABLE = True
except ImportError:
    MODERN_COMPONENTS_AVAILABLE = False
    st.warning("⚠️ Install modern components: `pip install streamlit-extras streamlit-option-menu`")

# Import existing utilities
from utils.leetcodeapi import fetch_user_data, fetch_recent_submissions, fetch_daily_challenge
from utils.auth import register as auth_register, credentials_for_authenticator, verify_login

# ============================================================================
# PAGE CONFIGURATION
# ============================================================================

st.set_page_config(
    page_title="LeetCode Team Dashboard",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://github.com/your-repo',
        'Report a bug': 'https://github.com/your-repo/issues',
        'About': '# LeetCode Team Dashboard\nTrack your team\'s coding progress!'
    }
)

# ============================================================================
# MODERN STYLING
# ============================================================================

st.markdown("""
<style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    /* Global Styles */
    * {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Main container */
    .main {
        background: linear-gradient(135deg, #0a0e1a 0%, #1a1f2e 100%);
        padding: 0 !important;
    }

    .block-container {
        padding: 2rem 3rem !important;
        max-width: 100% !important;
    }

    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a1f2e 0%, #0a0e1a 100%);
        border-right: 1px solid rgba(255, 161, 22, 0.1);
    }

    [data-testid="stSidebar"] > div:first-child {
        padding-top: 2rem;
    }

    /* Custom Header */
    .dashboard-header {
        background: linear-gradient(135deg, rgba(255,161,22,0.1) 0%, rgba(30,136,229,0.1) 100%);
        border: 1px solid rgba(255,161,22,0.2);
        border-radius: 20px;
        padding: 2rem;
        margin-bottom: 2rem;
        backdrop-filter: blur(10px);
        box-shadow: 0 8px 32px rgba(0,0,0,0.3);
    }

    .dashboard-title {
        font-size: 2.5rem;
        font-weight: 800;
        background: linear-gradient(135deg, #FFA116 0%, #FF8C00 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0;
        letter-spacing: -0.02em;
    }

    .dashboard-subtitle {
        font-size: 1.1rem;
        color: rgba(255,255,255,0.7);
        margin-top: 0.5rem;
    }

    /* Modern Cards */
    .modern-card {
        background: rgba(26, 31, 46, 0.8);
        backdrop-filter: blur(20px);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 16px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: 0 4px 20px rgba(0,0,0,0.2);
    }

    .modern-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 12px 40px rgba(255,161,22,0.2);
        border-color: rgba(255,161,22,0.3);
    }

    /* Metric Cards */
    div[data-testid="metric-container"] {
        background: linear-gradient(135deg, rgba(26,31,46,0.9) 0%, rgba(36,41,56,0.9) 100%);
        border: 1px solid rgba(255,161,22,0.2);
        border-radius: 12px;
        padding: 1.5rem 1rem;
        box-shadow: 0 4px 16px rgba(0,0,0,0.2);
        transition: all 0.3s ease;
    }

    div[data-testid="metric-container"]:hover {
        transform: scale(1.05);
        box-shadow: 0 8px 32px rgba(255,161,22,0.3);
    }

    div[data-testid="metric-container"] > label {
        font-size: 0.85rem !important;
        font-weight: 600 !important;
        color: rgba(255,255,255,0.7) !important;
        text-transform: uppercase !important;
        letter-spacing: 0.05em !important;
    }

    div[data-testid="metric-container"] > div {
        font-size: 2rem !important;
        font-weight: 700 !important;
        color: #FFA116 !important;
    }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 2rem;
        background-color: rgba(26,31,46,0.5);
        border-radius: 12px;
        padding: 0.5rem;
        margin-bottom: 2rem;
    }

    .stTabs [data-baseweb="tab"] {
        height: 3rem;
        padding: 0 2rem;
        background-color: transparent;
        border-radius: 8px;
        color: rgba(255,255,255,0.6);
        font-weight: 600;
        font-size: 1rem;
        transition: all 0.3s ease;
    }

    .stTabs [data-baseweb="tab"]:hover {
        background-color: rgba(255,161,22,0.1);
        color: #FFA116;
    }

    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #FFA116 0%, #FF8C00 100%);
        color: white !important;
        box-shadow: 0 4px 12px rgba(255,161,22,0.4);
    }

    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #FFA116 0%, #FF8C00 100%);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        font-size: 1rem;
        transition: all 0.3s ease;
        box-shadow: 0 4px 12px rgba(255,161,22,0.3);
    }

    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 24px rgba(255,161,22,0.5);
    }

    /* Progress bars */
    .stProgress > div > div > div {
        background: linear-gradient(90deg, #FFA116 0%, #34A853 100%);
        border-radius: 10px;
    }

    /* Dataframe/Table */
    .dataframe {
        border-radius: 12px !important;
        overflow: hidden !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
    }

    /* Custom scrollbar */
    ::-webkit-scrollbar {
        width: 10px;
        height: 10px;
    }

    ::-webkit-scrollbar-track {
        background: rgba(26,31,46,0.5);
    }

    ::-webkit-scrollbar-thumb {
        background: linear-gradient(180deg, #FFA116 0%, #FF8C00 100%);
        border-radius: 10px;
    }

    ::-webkit-scrollbar-thumb:hover {
        background: linear-gradient(180deg, #FF8C00 0%, #FFA116 100%);
    }

    /* Input fields */
    .stTextInput > div > div > input,
    .stSelectbox > div > div > select {
        background-color: rgba(26,31,46,0.8);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 10px;
        color: white;
        padding: 0.75rem 1rem;
        font-size: 1rem;
    }

    .stTextInput > div > div > input:focus,
    .stSelectbox > div > div > select:focus {
        border-color: #FFA116;
        box-shadow: 0 0 0 2px rgba(255,161,22,0.2);
    }

    /* Sidebar logo */
    .sidebar-logo {
        text-align: center;
        padding: 1rem;
        margin-bottom: 2rem;
    }

    .sidebar-logo img {
        width: 60px;
        height: 60px;
        border-radius: 50%;
        border: 3px solid #FFA116;
        box-shadow: 0 0 20px rgba(255,161,22,0.5);
    }

    /* Stats widget */
    .stat-widget {
        background: linear-gradient(135deg, rgba(255,161,22,0.1) 0%, rgba(30,136,229,0.1) 100%);
        border: 1px solid rgba(255,161,22,0.2);
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1rem;
    }

    .stat-widget h3 {
        color: #FFA116;
        font-size: 1.5rem;
        margin: 0 0 0.5rem 0;
    }

    .stat-widget p {
        color: rgba(255,255,255,0.7);
        margin: 0;
        font-size: 0.9rem;
    }

    /* Animation */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }

    .animated {
        animation: fadeIn 0.6s ease-out;
    }

    /* Badge */
    .custom-badge {
        display: inline-block;
        padding: 0.35rem 0.75rem;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
        margin: 0 0.25rem;
    }

    .badge-success { background: rgba(52,168,83,0.2); color: #34A853; border: 1px solid #34A853; }
    .badge-warning { background: rgba(251,188,4,0.2); color: #FBBC04; border: 1px solid #FBBC04; }
    .badge-danger { background: rgba(239,71,67,0.2); color: #EF4743; border: 1px solid #EF4743; }
    .badge-info { background: rgba(30,136,229,0.2); color: #1E88E5; border: 1px solid #1E88E5; }
    .badge-primary { background: rgba(255,161,22,0.2); color: #FFA116; border: 1px solid #FFA116; }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# STORAGE FUNCTIONS (Keep existing logic)
# ============================================================================

def _use_s3() -> bool:
    try:
        required_keys = ("AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_DEFAULT_REGION", "S3_BUCKET_NAME", "S3_PREFIX")
        return all(os.environ.get(k) for k in required_keys)
    except Exception:
        return False

def storage_read_json(local_path: str, default):
    """Read JSON from S3 or local file"""
    if _use_s3():
        try:
            import boto3
            s3 = boto3.client("s3",
                aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
                aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
                region_name=os.environ.get("AWS_DEFAULT_REGION"))
            bucket = os.environ.get("S3_BUCKET_NAME")
            prefix = os.environ.get("S3_PREFIX", "").rstrip("/")
            key = f"{prefix}/{local_path.lstrip('/')}"
            obj = s3.get_object(Bucket=bucket, Key=key)
            return json.loads(obj["Body"].read().decode("utf-8"))
        except Exception:
            return default
    else:
        if not os.path.exists(local_path):
            return default
        with open(local_path, "r", encoding="utf-8") as f:
            return json.load(f)

def storage_write_json(local_path: str, payload):
    """Write JSON to S3 or local file"""
    if _use_s3():
        import boto3
        s3 = boto3.client("s3",
            aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
            region_name=os.environ.get("AWS_DEFAULT_REGION"))
        bucket = os.environ.get("S3_BUCKET_NAME")
        prefix = os.environ.get("S3_PREFIX", "").rstrip("/")
        key = f"{prefix}/{local_path.lstrip('/')}"
        s3.put_object(Bucket=bucket, Key=key, Body=json.dumps(payload, indent=2, ensure_ascii=False).encode("utf-8"))
    else:
        os.makedirs(os.path.dirname(local_path) or ".", exist_ok=True)
        with open(local_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)

# ============================================================================
# SESSION STATE INITIALIZATION
# ============================================================================

if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'username' not in st.session_state:
    st.session_state.username = None
if 'selected_member' not in st.session_state:
    st.session_state.selected_member = None

# ============================================================================
# MODERN UI COMPONENTS
# ============================================================================

def render_header():
    """Render modern dashboard header"""
    st.markdown("""
        <div class="dashboard-header animated">
            <div class="dashboard-title">🚀 LeetCode Team Dashboard</div>
            <div class="dashboard-subtitle">Track, analyze, and celebrate your team's coding journey</div>
        </div>
    """, unsafe_allow_html=True)

def render_metric_card(label, value, delta=None, delta_color="normal"):
    """Render a modern metric card"""
    st.metric(label=label, value=value, delta=delta, delta_color=delta_color)

def render_sidebar():
    """Render modern sidebar with navigation"""
    with st.sidebar:
        # Logo
        st.markdown("""
            <div class="sidebar-logo">
                <div style="width:60px; height:60px; margin:0 auto; border-radius:50%; background:linear-gradient(135deg, #FFA116 0%, #FF8C00 100%); display:flex; align-items:center; justify-content:center; box-shadow: 0 0 20px rgba(255,161,22,0.5); font-size:2rem;">
                    🚀
                </div>
            </div>
        """, unsafe_allow_html=True)

        # Navigation menu
        if MODERN_COMPONENTS_AVAILABLE:
            selected = option_menu(
                menu_title="Navigation",
                options=["Dashboard", "Team", "Analytics", "Settings"],
                icons=['speedometer2', 'people-fill', 'graph-up', 'gear-fill'],
                menu_icon="cast",
                default_index=0,
                styles={
                    "container": {"padding": "0", "background-color": "transparent"},
                    "icon": {"color": "#FFA116", "font-size": "1.2rem"},
                    "nav-link": {
                        "font-size": "1rem",
                        "text-align": "left",
                        "margin": "0.5rem 0",
                        "padding": "0.75rem 1rem",
                        "border-radius": "8px",
                        "background-color": "transparent",
                        "color": "rgba(255,255,255,0.7)"
                    },
                    "nav-link-selected": {
                        "background": "linear-gradient(135deg, #FFA116 0%, #FF8C00 100%)",
                        "color": "white",
                        "font-weight": "600"
                    },
                }
            )
            return selected
        else:
            return st.selectbox("📍 Navigation", ["Dashboard", "Team", "Analytics", "Settings"])

# ============================================================================
# MAIN APP
# ============================================================================

def main():
    # Render header
    render_header()

    # Render sidebar and get selected page
    selected_page = render_sidebar()

    # Page routing
    if selected_page == "Dashboard":
        render_dashboard_page()
    elif selected_page == "Team":
        render_team_page()
    elif selected_page == "Analytics":
        render_analytics_page()
    elif selected_page == "Settings":
        render_settings_page()

def render_dashboard_page():
    """Main dashboard with overview metrics"""
    st.markdown("### 📊 Overview")

    # Top metrics row
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        render_metric_card("Total Problems", "1,234", "+25", "normal")

    with col2:
        render_metric_card("Team Members", "15", "+2", "normal")

    with col3:
        render_metric_card("Avg. Acceptance", "85.3%", "+2.1%", "normal")

    with col4:
        render_metric_card("Active Streak", "7 days", "🔥", "off")

    if MODERN_COMPONENTS_AVAILABLE:
        style_metric_cards(background_color="rgba(26,31,46,0.8)", border_left_color="#FFA116")

    # Charts row
    st.markdown("---")
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 📈 Weekly Progress")
        # Placeholder chart
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
            y=[10, 15, 13, 17, 20, 18, 22],
            mode='lines+markers',
            line=dict(color='#FFA116', width=3),
            marker=dict(size=10, color='#FFA116'),
            fill='tozeroy',
            fillcolor='rgba(255,161,22,0.2)'
        ))
        fig.update_layout(
            template='plotly_dark',
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=0, r=0, t=0, b=0),
            height=300,
            xaxis=dict(showgrid=False),
            yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)')
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("### 🎯 Difficulty Breakdown")
        # Placeholder pie chart
        fig = go.Figure(data=[go.Pie(
            labels=['Easy', 'Medium', 'Hard'],
            values=[500, 450, 284],
            marker=dict(colors=['#34A853', '#FBBC04', '#EF4743']),
            hole=0.5,
            textfont=dict(size=14, color='white')
        )])
        fig.update_layout(
            template='plotly_dark',
            paper_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=0, r=0, t=0, b=0),
            height=300,
            showlegend=True,
            legend=dict(font=dict(color='white'))
        )
        st.plotly_chart(fig, use_container_width=True)

def render_team_page():
    """Team members management and leaderboard"""
    st.markdown("### 👥 Team Leaderboard")

    # Sample data
    team_data = {
        "Rank": ["🥇", "🥈", "🥉", "4", "5"],
        "Member": ["Alice Johnson", "Bob Smith", "Charlie Davis", "Diana Wilson", "Eve Martinez"],
        "Solved": [250, 200, 180, 150, 120],
        "Easy": [100, 80, 70, 60, 50],
        "Medium": [100, 80, 70, 60, 50],
        "Hard": [50, 40, 40, 30, 20],
        "Acceptance": ["85%", "82%", "88%", "79%", "91%"]
    }

    df = pd.DataFrame(team_data)

    st.dataframe(
        df,
        use_container_width=True,
        height=400,
        hide_index=True,
        column_config={
            "Rank": st.column_config.TextColumn("Rank", width="small"),
            "Member": st.column_config.TextColumn("Member", width="medium"),
            "Solved": st.column_config.ProgressColumn(
                "Total Solved",
                help="Total problems solved",
                format="%d",
                min_value=0,
                max_value=300,
            ),
        }
    )

def render_analytics_page():
    """Advanced analytics and insights"""
    st.markdown("### 📊 Advanced Analytics")

    tab1, tab2, tab3 = st.tabs(["📈 Trends", "🔥 Activity", "🏆 Achievements"])

    with tab1:
        st.markdown("#### Progress Trends")
        st.info("📊 Trend analysis coming soon!")

    with tab2:
        st.markdown("#### Activity Heatmap")
        st.info("🔥 Activity tracking coming soon!")

    with tab3:
        st.markdown("#### Team Achievements")
        st.info("🏆 Achievements system coming soon!")

def render_settings_page():
    """Settings and configuration"""
    st.markdown("### ⚙️ Settings")

    with st.expander("👥 Team Management"):
        st.text_input("Add team member (LeetCode username)")
        st.button("➕ Add Member", use_container_width=True)

    with st.expander("🎨 Theme Settings"):
        st.selectbox("Color Scheme", ["Dark (Default)", "Light", "Auto"])
        st.selectbox("Accent Color", ["Orange (LeetCode)", "Blue", "Green", "Purple"])

    with st.expander("💾 Data Management"):
        storage_type = "S3 Cloud Storage" if _use_s3() else "Local Storage"
        st.markdown(f"**Current Storage:** `{storage_type}`")
        st.button("📥 Export Data", use_container_width=True)
        st.button("📤 Import Data", use_container_width=True)

if __name__ == "__main__":
    main()
