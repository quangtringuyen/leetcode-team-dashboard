# Modern UI Quick Reference Card

## 🚀 Quick Setup

```python
# At the top of app.py
from ui.components import inject_base_css

# After page config
inject_base_css()
```

## 📦 Component Imports

```python
from ui.components import (
    # Layout & Headers
    modern_title, section_header,

    # Cards & Containers
    glass_card, stat_card, badge,

    # Profile & Leaderboard
    profile_header, leaderboard, podium_display,

    # Charts & Visualizations
    pie_difficulty, team_bar, activity_heatmap, trend_chart,

    # Utilities
    loading_skeleton, metric_grid, daily_challenge_card
)
```

## 🎨 Essential Components

### Title
```python
modern_title("Dashboard Name", "📊")
```

### Section Headers
```python
section_header("Section Name", "🏆")
```

### Stat Cards (Grid)
```python
metrics = [
    {"label": "Total", "value": "150", "icon": "✅", "variant": "success", "delta": "+10"},
    {"label": "Rank", "value": "#42", "icon": "🏅", "variant": "primary"}
]
metric_grid(metrics, columns=4)
```

### Badges
```python
badge("Success", "success")  # Green
badge("Primary", "primary")  # Orange
badge("Danger", "danger")    # Red
badge("Info", "info")        # Blue
badge("Warning", "warning")  # Yellow
```

### Profile Header
```python
profile_header({
    "name": "John Doe",
    "username": "johndoe",
    "avatar": "https://...",
    "ranking": 12345,
    "totalSolved": 250
})
```

### Leaderboard
```python
selected_user = leaderboard(df_sorted, selected_user_un="username")
```

### Podium (Top 3)
```python
top_3 = [
    {"username": "u1", "name": "Alice", "avatar": "url", "totalSolved": 250},
    {"username": "u2", "name": "Bob", "avatar": "url", "totalSolved": 200},
    {"username": "u3", "name": "Charlie", "avatar": "url", "totalSolved": 180}
]
selected = podium_display(top_3, selected_user="u1")
```

## 📊 Charts

### Pie Chart
```python
pie_difficulty(easy=100, med=80, hard=30, title="Progress")
```

### Bar Chart
```python
team_bar(performance_df, title="Team Comparison")
```

### Heatmap
```python
activity_heatmap(calendar_df, username="johndoe")
```

### Trend Chart
```python
trend_chart(trend_df, title="Weekly Progress")
```

## 🎭 Variants Reference

| Variant | Color | Use Case |
|---------|-------|----------|
| `primary` | Orange | Main actions, highlights |
| `success` | Green | Positive metrics, easy difficulty |
| `danger` | Red | Errors, hard difficulty |
| `info` | Blue | Information, links |
| `warning` | Yellow | Cautions, medium difficulty |

## 🎨 Color Tokens

```css
--leetcode-orange: #FFA116  /* Primary */
--leetcode-green:  #34A853  /* Success */
--leetcode-red:    #EF4743  /* Danger */
--leetcode-blue:   #1E88E5  /* Info */
--leetcode-yellow: #FBBC04  /* Warning */
```

## 📐 Spacing Scale

```css
--space-xs:  0.25rem  /* 4px */
--space-sm:  0.5rem   /* 8px */
--space-md:  1rem     /* 16px */
--space-lg:  1.5rem   /* 24px */
--space-xl:  2rem     /* 32px */
--space-2xl: 3rem     /* 48px */
```

## 🎬 Animation Classes

```html
<div class="animate-fade-in">Fade in</div>
<div class="animate-fade-in-up">Slide up</div>
<div class="animate-fade-in-down">Slide down</div>
<div class="animate-scale-in">Scale in</div>
<div class="animate-pulse">Pulse effect</div>
```

## 🛠️ Utility Classes

```html
<!-- Text -->
<div class="text-center">Center</div>
<div class="text-left">Left</div>
<div class="text-right">Right</div>

<!-- Flex -->
<div class="flex items-center gap-md">Flex</div>

<!-- Spacing -->
<div class="mt-lg mb-md">Spacing</div>

<!-- Opacity -->
<div class="opacity-75">75% opacity</div>
```

## 💾 Loading States

```python
# While loading
if is_loading:
    loading_skeleton(type="card", count=3)
else:
    # Show data
    pass
```

## 🎯 Common Patterns

### Stat Overview
```python
section_header("Overview", "📊")
metric_grid([
    {"label": "Total", "value": "150", "icon": "✅", "variant": "success"},
    {"label": "Members", "value": "10", "icon": "👥", "variant": "primary"}
], columns=4)
```

### Member Selection
```python
section_header("Team", "🏆")
if len(top_members) >= 3:
    selected = podium_display(top_members, selected_user)
selected = leaderboard(all_members, selected_user)
```

### Data Visualization
```python
section_header("Statistics", "📈")
col1, col2 = st.columns(2)
with col1:
    pie_difficulty(easy, med, hard)
with col2:
    team_bar(performance_df)
```

## ⚡ Quick Wins

### Replace This:
```python
st.markdown("### 🏆 Leaderboard")
st.markdown('<div class="leetcode-card">', unsafe_allow_html=True)
# content
st.markdown('</div>', unsafe_allow_html=True)
```

### With This:
```python
section_header("Leaderboard", "🏆")
# content (auto-wrapped)
```

### Replace This:
```python
st.markdown('<div class="header-title">Dashboard</div>', unsafe_allow_html=True)
```

### With This:
```python
modern_title("Dashboard", "📊")
```

## 🔍 Debugging

### Styles Not Working?
```python
# Add at top of page
inject_base_css()
```

### Theme Not Switching?
```bash
# Check config exists
ls .streamlit/config.toml
```

### Component Errors?
```python
# Check imports
from ui.components import component_name
```

## 📱 Responsive Breakpoints

```css
Desktop:  > 768px   (4 columns)
Tablet:   ≤ 768px   (2 columns)
Mobile:   ≤ 480px   (1 column)
```

## 🎯 Best Practices

✅ **DO**
- Use semantic component names
- Apply consistent variants
- Show loading states
- Test both themes
- Use metric_grid for stats

❌ **DON'T**
- Mix old and new styles
- Override component CSS
- Skip loading states
- Use inconsistent colors
- Forget to inject CSS

## 📚 Full Documentation

- **Complete Guide**: [UI_REDESIGN_GUIDE.md](UI_REDESIGN_GUIDE.md)
- **Examples**: [MODERN_UI_EXAMPLE.py](MODERN_UI_EXAMPLE.py)
- **Summary**: [UI_REDESIGN_SUMMARY.md](UI_REDESIGN_SUMMARY.md)
- **Components**: [ui/components.py](ui/components.py)
- **Styles**: [ui/modern_styles.py](ui/modern_styles.py)

## 🆘 Support

Issues? Check:
1. This quick reference
2. Full guide (UI_REDESIGN_GUIDE.md)
3. Example file (MODERN_UI_EXAMPLE.py)
4. Component source (ui/components.py)

---

**TIP**: Start with metric_grid, section_header, and modern_title for quick visual impact!
