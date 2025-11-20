"""
Modern UI/UX Design System for LeetCode Team Dashboard
Provides comprehensive styling with animations, glassmorphism, and modern aesthetics
"""

MODERN_CSS = """
<style>
/* ==================== DESIGN TOKENS ==================== */
:root {
    /* Brand Colors */
    --leetcode-orange: #FFA116;
    --leetcode-green: #34A853;
    --leetcode-yellow: #FBBC04;
    --leetcode-red: #EF4743;
    --leetcode-blue: #1E88E5;

    /* Semantic Colors */
    --primary: #FFA116;
    --success: #34A853;
    --warning: #FBBC04;
    --danger: #EF4743;
    --info: #1E88E5;

    /* Medal Colors */
    --gold: #FFD700;
    --silver: #C0C0C0;
    --bronze: #CD7F32;

    /* Gradients */
    --gradient-primary: linear-gradient(135deg, #FFA116 0%, #FF8C00 100%);
    --gradient-success: linear-gradient(135deg, #34A853 0%, #2D8E47 100%);
    --gradient-danger: linear-gradient(135deg, #EF4743 0%, #D33C37 100%);
    --gradient-info: linear-gradient(135deg, #1E88E5 0%, #1976D2 100%);
    --gradient-dark: linear-gradient(135deg, #1A1F2E 0%, #0A0E1A 100%);
    --gradient-glass: linear-gradient(135deg, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0.05) 100%);

    /* Spacing Scale */
    --space-xs: 0.25rem;
    --space-sm: 0.5rem;
    --space-md: 1rem;
    --space-lg: 1.5rem;
    --space-xl: 2rem;
    --space-2xl: 3rem;
    --space-3xl: 4rem;

    /* Border Radius */
    --radius-sm: 6px;
    --radius-md: 10px;
    --radius-lg: 16px;
    --radius-xl: 24px;
    --radius-full: 9999px;

    /* Shadows */
    --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
    --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
    --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
    --shadow-xl: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
    --shadow-2xl: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
    --shadow-glow: 0 0 20px rgba(255, 161, 22, 0.3);
    --shadow-glow-lg: 0 0 40px rgba(255, 161, 22, 0.4);

    /* Typography */
    --font-sans: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Helvetica', 'Arial', sans-serif;
    --font-mono: 'SF Mono', Monaco, 'Cascadia Code', 'Roboto Mono', Consolas, 'Courier New', monospace;

    /* Z-index */
    --z-base: 1;
    --z-dropdown: 10;
    --z-sticky: 100;
    --z-fixed: 1000;
    --z-modal: 10000;
    --z-tooltip: 100000;

    /* Animation Timing */
    --transition-fast: 150ms;
    --transition-base: 250ms;
    --transition-slow: 350ms;
    --transition-slower: 500ms;
    --ease-in-out: cubic-bezier(0.4, 0, 0.2, 1);
    --ease-out: cubic-bezier(0.0, 0, 0.2, 1);
    --ease-in: cubic-bezier(0.4, 0, 1, 1);
}

/* Dark Theme (Default) */
[data-theme="dark"] {
    --bg-primary: #0A0E1A;
    --bg-secondary: #1A1F2E;
    --bg-tertiary: #242938;
    --bg-card: #1E2433;
    --bg-hover: #2A3142;
    --bg-active: #323A4F;
    --text-primary: #F5F5F5;
    --text-secondary: #B4B9C6;
    --text-tertiary: #7D8590;
    --border-color: #30374A;
    --border-hover: #3D465E;
    --overlay: rgba(10, 14, 26, 0.8);
}

/* Light Theme */
[data-theme="light"] {
    --bg-primary: #FFFFFF;
    --bg-secondary: #F7F8FA;
    --bg-tertiary: #EFF1F5;
    --bg-card: #FFFFFF;
    --bg-hover: #F0F2F6;
    --bg-active: #E8EBF0;
    --text-primary: #1A1F2E;
    --text-secondary: #4A5568;
    --text-tertiary: #718096;
    --border-color: #E2E8F0;
    --border-hover: #CBD5E0;
    --overlay: rgba(0, 0, 0, 0.5);
}

/* ==================== GLOBAL STYLES ==================== */
.stApp {
    background-color: var(--bg-primary) !important;
    font-family: var(--font-sans) !important;
}

.main .block-container {
    padding-top: 2rem;
    padding-bottom: 3rem;
    max-width: 1400px;
}

/* Remove Streamlit branding */
footer, #MainMenu, header {
    visibility: hidden;
}

/* ==================== TYPOGRAPHY ==================== */
.modern-title {
    background: var(--gradient-primary);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    font-weight: 800;
    font-size: 3rem;
    text-align: center;
    margin-bottom: var(--space-xl);
    letter-spacing: -0.02em;
    animation: fadeInDown var(--transition-slow) var(--ease-out);
}

.section-title {
    color: var(--text-primary);
    font-weight: 700;
    font-size: 1.75rem;
    margin-bottom: var(--space-lg);
    display: flex;
    align-items: center;
    gap: var(--space-sm);
}

.section-title::after {
    content: '';
    flex: 1;
    height: 2px;
    background: linear-gradient(90deg, var(--primary) 0%, transparent 100%);
}

.subtitle {
    color: var(--text-secondary);
    font-size: 1rem;
    font-weight: 500;
}

.caption {
    color: var(--text-tertiary);
    font-size: 0.875rem;
    font-weight: 400;
}

/* ==================== GLASS CARD SYSTEM ==================== */
.glass-card {
    background: rgba(30, 36, 51, 0.6);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: var(--radius-lg);
    padding: var(--space-lg);
    margin-bottom: var(--space-lg);
    box-shadow: var(--shadow-lg);
    transition: all var(--transition-base) var(--ease-in-out);
    position: relative;
    overflow: hidden;
}

.glass-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(255,161,22,0.5), transparent);
    opacity: 0;
    transition: opacity var(--transition-base) var(--ease-in-out);
}

.glass-card:hover::before {
    opacity: 1;
}

.glass-card:hover {
    transform: translateY(-2px);
    box-shadow: var(--shadow-xl);
    border-color: rgba(255, 161, 22, 0.3);
}

/* Glass card variants */
.glass-card-primary {
    border-color: rgba(255, 161, 22, 0.2);
    background: linear-gradient(135deg, rgba(255, 161, 22, 0.1), rgba(30, 36, 51, 0.6));
}

.glass-card-success {
    border-color: rgba(52, 168, 83, 0.2);
    background: linear-gradient(135deg, rgba(52, 168, 83, 0.1), rgba(30, 36, 51, 0.6));
}

.glass-card-danger {
    border-color: rgba(239, 71, 67, 0.2);
    background: linear-gradient(135deg, rgba(239, 71, 67, 0.1), rgba(30, 36, 51, 0.6));
}

/* ==================== LEADERBOARD COMPONENTS ==================== */
.leaderboard-container {
    display: flex;
    flex-direction: column;
    gap: var(--space-md);
}

.leaderboard-item {
    background: var(--bg-card);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-md);
    padding: var(--space-md);
    cursor: pointer;
    transition: all var(--transition-base) var(--ease-in-out);
    position: relative;
    overflow: hidden;
}

.leaderboard-item::before {
    content: '';
    position: absolute;
    left: 0;
    top: 0;
    bottom: 0;
    width: 4px;
    background: var(--primary);
    transform: scaleY(0);
    transition: transform var(--transition-base) var(--ease-out);
}

.leaderboard-item:hover {
    background: var(--bg-hover);
    transform: translateX(8px);
    box-shadow: var(--shadow-md);
}

.leaderboard-item:hover::before {
    transform: scaleY(1);
}

.leaderboard-item.selected {
    background: rgba(255, 161, 22, 0.12);
    border-color: var(--primary);
    box-shadow: var(--shadow-glow);
}

.leaderboard-item.selected::before {
    transform: scaleY(1);
}

/* Podium Display */
.podium-container {
    display: flex;
    justify-content: center;
    align-items: flex-end;
    gap: var(--space-md);
    margin: var(--space-xl) 0;
    padding: var(--space-lg);
}

.podium-place {
    flex: 1;
    max-width: 200px;
    text-align: center;
    cursor: pointer;
    transition: all var(--transition-base) var(--ease-in-out);
}

.podium-place:hover {
    transform: translateY(-10px);
}

.podium-avatar {
    width: 100px;
    height: 100px;
    border-radius: 50%;
    margin: 0 auto var(--space-md);
    box-shadow: var(--shadow-lg);
    transition: all var(--transition-base) var(--ease-in-out);
    position: relative;
}

.podium-place-1 .podium-avatar {
    width: 120px;
    height: 120px;
    border: 4px solid var(--gold);
    box-shadow: 0 0 30px rgba(255, 215, 0, 0.5);
}

.podium-place-2 .podium-avatar {
    border: 4px solid var(--silver);
}

.podium-place-3 .podium-avatar {
    border: 4px solid var(--bronze);
}

.podium-medal {
    position: absolute;
    bottom: -10px;
    right: -10px;
    width: 40px;
    height: 40px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 700;
    font-size: 1.2rem;
    box-shadow: var(--shadow-md);
}

.podium-place-1 .podium-medal {
    background: var(--gold);
    color: #000;
}

.podium-place-2 .podium-medal {
    background: var(--silver);
    color: #000;
}

.podium-place-3 .podium-medal {
    background: var(--bronze);
    color: #fff;
}

/* ==================== STAT CARDS ==================== */
.stat-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: var(--space-md);
    margin-bottom: var(--space-lg);
}

.stat-card {
    background: var(--bg-card);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-lg);
    padding: var(--space-lg);
    text-align: center;
    transition: all var(--transition-base) var(--ease-in-out);
    position: relative;
    overflow: hidden;
}

.stat-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: -100%;
    width: 100%;
    height: 100%;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.1), transparent);
    transition: left var(--transition-slower) var(--ease-in-out);
}

.stat-card:hover::before {
    left: 100%;
}

.stat-card:hover {
    transform: translateY(-4px);
    box-shadow: var(--shadow-xl);
    border-color: var(--primary);
}

.stat-icon {
    font-size: 2rem;
    margin-bottom: var(--space-sm);
    filter: drop-shadow(0 0 10px currentColor);
}

.stat-value {
    font-size: 2.5rem;
    font-weight: 800;
    color: var(--text-primary);
    margin: var(--space-sm) 0;
    line-height: 1;
}

.stat-label {
    font-size: 0.9rem;
    color: var(--text-secondary);
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

.stat-delta {
    font-size: 0.875rem;
    font-weight: 600;
    margin-top: var(--space-xs);
}

.stat-delta.positive {
    color: var(--success);
}

.stat-delta.negative {
    color: var(--danger);
}

/* Stat card variants */
.stat-card-primary {
    border-color: rgba(255, 161, 22, 0.3);
    background: linear-gradient(135deg, rgba(255, 161, 22, 0.05), var(--bg-card));
}

.stat-card-primary .stat-value {
    background: var(--gradient-primary);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.stat-card-success {
    border-color: rgba(52, 168, 83, 0.3);
    background: linear-gradient(135deg, rgba(52, 168, 83, 0.05), var(--bg-card));
}

.stat-card-success .stat-value {
    color: var(--success);
}

.stat-card-danger {
    border-color: rgba(239, 71, 67, 0.3);
    background: linear-gradient(135deg, rgba(239, 71, 67, 0.05), var(--bg-card));
}

.stat-card-danger .stat-value {
    color: var(--danger);
}

/* ==================== BADGES ==================== */
.badge {
    display: inline-flex;
    align-items: center;
    gap: var(--space-xs);
    padding: var(--space-xs) var(--space-md);
    border-radius: var(--radius-full);
    font-size: 0.875rem;
    font-weight: 600;
    letter-spacing: 0.02em;
    transition: all var(--transition-fast) var(--ease-in-out);
}

.badge-primary {
    background: var(--primary);
    color: #fff;
    box-shadow: 0 0 15px rgba(255, 161, 22, 0.3);
}

.badge-success {
    background: var(--success);
    color: #fff;
    box-shadow: 0 0 15px rgba(52, 168, 83, 0.3);
}

.badge-danger {
    background: var(--danger);
    color: #fff;
    box-shadow: 0 0 15px rgba(239, 71, 67, 0.3);
}

.badge-info {
    background: var(--info);
    color: #fff;
    box-shadow: 0 0 15px rgba(30, 136, 229, 0.3);
}

.badge-warning {
    background: var(--warning);
    color: #000;
    box-shadow: 0 0 15px rgba(251, 188, 4, 0.3);
}

.badge-outline {
    background: transparent;
    border: 1.5px solid currentColor;
    box-shadow: none;
}

.badge:hover {
    transform: translateY(-2px);
    filter: brightness(1.1);
}

/* ==================== PROFILE HEADER ==================== */
.profile-header {
    background: linear-gradient(135deg, #1E2433 0%, #0A0E1A 100%);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-xl);
    padding: var(--space-xl);
    margin-bottom: var(--space-xl);
    display: flex;
    align-items: center;
    gap: var(--space-xl);
    box-shadow: var(--shadow-2xl);
    position: relative;
    overflow: hidden;
}

.profile-header::before {
    content: '';
    position: absolute;
    top: -50%;
    right: -50%;
    width: 200%;
    height: 200%;
    background: radial-gradient(circle, rgba(255, 161, 22, 0.1) 0%, transparent 70%);
    animation: rotate 20s linear infinite;
}

@keyframes rotate {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
}

.profile-avatar {
    width: 120px;
    height: 120px;
    border-radius: 50%;
    border: 4px solid var(--primary);
    box-shadow: 0 0 30px rgba(255, 161, 22, 0.5);
    position: relative;
    z-index: var(--z-base);
}

.profile-info {
    flex: 1;
    position: relative;
    z-index: var(--z-base);
}

.profile-name {
    font-size: 2rem;
    font-weight: 800;
    color: var(--text-primary);
    margin-bottom: var(--space-xs);
}

.profile-username {
    font-size: 1.1rem;
    color: var(--text-secondary);
    margin-bottom: var(--space-md);
}

/* ==================== BUTTONS ==================== */
.stButton > button {
    background: var(--gradient-primary) !important;
    color: #fff !important;
    border: none !important;
    border-radius: var(--radius-md) !important;
    padding: 0.75rem 2rem !important;
    font-weight: 600 !important;
    font-size: 1rem !important;
    transition: all var(--transition-base) var(--ease-in-out) !important;
    box-shadow: var(--shadow-md) !important;
    position: relative !important;
    overflow: hidden !important;
}

.stButton > button::before {
    content: '';
    position: absolute;
    top: 50%;
    left: 50%;
    width: 0;
    height: 0;
    border-radius: 50%;
    background: rgba(255, 255, 255, 0.3);
    transform: translate(-50%, -50%);
    transition: width var(--transition-base) var(--ease-out), height var(--transition-base) var(--ease-out);
}

.stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: var(--shadow-glow-lg) !important;
}

.stButton > button:hover::before {
    width: 300px;
    height: 300px;
}

.stButton > button:active {
    transform: translateY(0) !important;
}

/* ==================== PROGRESS BARS ==================== */
.stProgress > div > div > div {
    background: var(--gradient-primary) !important;
    border-radius: var(--radius-full) !important;
    box-shadow: 0 0 10px rgba(255, 161, 22, 0.5) !important;
}

.stProgress > div > div {
    background-color: var(--bg-tertiary) !important;
    border-radius: var(--radius-full) !important;
}

/* ==================== CHARTS & VISUALIZATIONS ==================== */
.chart-container {
    background: var(--bg-card);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-lg);
    padding: var(--space-lg);
    margin-bottom: var(--space-lg);
    box-shadow: var(--shadow-md);
}

.chart-title {
    font-size: 1.25rem;
    font-weight: 700;
    color: var(--text-primary);
    margin-bottom: var(--space-md);
}

/* ==================== TABLES ==================== */
.dataframe {
    border-radius: var(--radius-md) !important;
    overflow: hidden !important;
    box-shadow: var(--shadow-md) !important;
}

.dataframe thead tr th {
    background: var(--bg-tertiary) !important;
    color: var(--text-primary) !important;
    font-weight: 700 !important;
    padding: 1rem !important;
    border: none !important;
}

.dataframe tbody tr {
    transition: all var(--transition-fast) var(--ease-in-out) !important;
}

.dataframe tbody tr:hover {
    background: var(--bg-hover) !important;
    transform: scale(1.01) !important;
}

.dataframe tbody td {
    padding: 0.875rem !important;
    border-bottom: 1px solid var(--border-color) !important;
}

/* ==================== INPUTS ==================== */
.stTextInput > div > div > input,
.stSelectbox > div > div > select,
.stMultiSelect > div > div > div {
    background-color: var(--bg-card) !important;
    color: var(--text-primary) !important;
    border: 1px solid var(--border-color) !important;
    border-radius: var(--radius-md) !important;
    padding: 0.75rem !important;
    transition: all var(--transition-base) var(--ease-in-out) !important;
}

.stTextInput > div > div > input:focus,
.stSelectbox > div > div > select:focus {
    border-color: var(--primary) !important;
    box-shadow: 0 0 0 3px rgba(255, 161, 22, 0.1) !important;
}

/* ==================== ANIMATIONS ==================== */
@keyframes fadeIn {
    from {
        opacity: 0;
    }
    to {
        opacity: 1;
    }
}

@keyframes fadeInUp {
    from {
        opacity: 0;
        transform: translateY(20px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

@keyframes fadeInDown {
    from {
        opacity: 0;
        transform: translateY(-20px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

@keyframes slideInLeft {
    from {
        opacity: 0;
        transform: translateX(-30px);
    }
    to {
        opacity: 1;
        transform: translateX(0);
    }
}

@keyframes slideInRight {
    from {
        opacity: 0;
        transform: translateX(30px);
    }
    to {
        opacity: 1;
        transform: translateX(0);
    }
}

@keyframes scaleIn {
    from {
        opacity: 0;
        transform: scale(0.9);
    }
    to {
        opacity: 1;
        transform: scale(1);
    }
}

@keyframes pulse {
    0%, 100% {
        opacity: 1;
    }
    50% {
        opacity: 0.8;
    }
}

@keyframes shimmer {
    0% {
        background-position: -1000px 0;
    }
    100% {
        background-position: 1000px 0;
    }
}

.animate-fade-in {
    animation: fadeIn var(--transition-slow) var(--ease-out);
}

.animate-fade-in-up {
    animation: fadeInUp var(--transition-slow) var(--ease-out);
}

.animate-fade-in-down {
    animation: fadeInDown var(--transition-slow) var(--ease-out);
}

.animate-slide-in-left {
    animation: slideInLeft var(--transition-slow) var(--ease-out);
}

.animate-slide-in-right {
    animation: slideInRight var(--transition-slow) var(--ease-out);
}

.animate-scale-in {
    animation: scaleIn var(--transition-slow) var(--ease-out);
}

.animate-pulse {
    animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}

/* ==================== LOADING SKELETON ==================== */
.skeleton {
    background: linear-gradient(90deg, var(--bg-secondary) 25%, var(--bg-tertiary) 50%, var(--bg-secondary) 75%);
    background-size: 200% 100%;
    animation: shimmer 1.5s infinite;
    border-radius: var(--radius-md);
}

.skeleton-text {
    height: 1rem;
    margin-bottom: var(--space-sm);
}

.skeleton-title {
    height: 2rem;
    width: 60%;
    margin-bottom: var(--space-md);
}

.skeleton-card {
    height: 200px;
    margin-bottom: var(--space-lg);
}

/* ==================== RESPONSIVE DESIGN ==================== */
@media (max-width: 768px) {
    .modern-title {
        font-size: 2rem;
    }

    .section-title {
        font-size: 1.5rem;
    }

    .stat-grid {
        grid-template-columns: 1fr;
    }

    .podium-container {
        flex-direction: column;
        align-items: center;
    }

    .profile-header {
        flex-direction: column;
        text-align: center;
    }

    .stat-value {
        font-size: 2rem;
    }
}

@media (max-width: 480px) {
    .modern-title {
        font-size: 1.75rem;
    }

    .main .block-container {
        padding-left: 1rem;
        padding-right: 1rem;
    }
}

/* ==================== ACCESSIBILITY ==================== */
.sr-only {
    position: absolute;
    width: 1px;
    height: 1px;
    padding: 0;
    margin: -1px;
    overflow: hidden;
    clip: rect(0, 0, 0, 0);
    white-space: nowrap;
    border-width: 0;
}

/* Focus styles for accessibility */
*:focus-visible {
    outline: 2px solid var(--primary);
    outline-offset: 2px;
}

/* ==================== UTILITIES ==================== */
.text-center { text-align: center; }
.text-left { text-align: left; }
.text-right { text-align: right; }

.flex { display: flex; }
.flex-col { flex-direction: column; }
.items-center { align-items: center; }
.justify-center { justify-content: center; }
.justify-between { justify-content: space-between; }
.gap-sm { gap: var(--space-sm); }
.gap-md { gap: var(--space-md); }
.gap-lg { gap: var(--space-lg); }

.mt-sm { margin-top: var(--space-sm); }
.mt-md { margin-top: var(--space-md); }
.mt-lg { margin-top: var(--space-lg); }
.mb-sm { margin-bottom: var(--space-sm); }
.mb-md { margin-bottom: var(--space-md); }
.mb-lg { margin-bottom: var(--space-lg); }

.opacity-50 { opacity: 0.5; }
.opacity-75 { opacity: 0.75; }

.cursor-pointer { cursor: pointer; }
.cursor-not-allowed { cursor: not-allowed; }

/* ==================== CUSTOM SCROLLBAR ==================== */
::-webkit-scrollbar {
    width: 10px;
    height: 10px;
}

::-webkit-scrollbar-track {
    background: var(--bg-secondary);
}

::-webkit-scrollbar-thumb {
    background: var(--bg-tertiary);
    border-radius: var(--radius-full);
}

::-webkit-scrollbar-thumb:hover {
    background: var(--primary);
}

/* ==================== TOOLTIPS ==================== */
.tooltip {
    position: relative;
    display: inline-block;
}

.tooltip .tooltip-text {
    visibility: hidden;
    background-color: var(--bg-tertiary);
    color: var(--text-primary);
    text-align: center;
    border-radius: var(--radius-sm);
    padding: var(--space-sm) var(--space-md);
    position: absolute;
    z-index: var(--z-tooltip);
    bottom: 125%;
    left: 50%;
    transform: translateX(-50%);
    opacity: 0;
    transition: opacity var(--transition-base) var(--ease-in-out);
    white-space: nowrap;
    box-shadow: var(--shadow-lg);
}

.tooltip:hover .tooltip-text {
    visibility: visible;
    opacity: 1;
}

</style>
"""

def inject_modern_styles():
    """Inject modern CSS into the Streamlit app"""
    import streamlit as st
    st.markdown(MODERN_CSS, unsafe_allow_html=True)
