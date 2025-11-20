# UI/UX Redesign Guide

## Overview

The LeetCode Team Dashboard has been redesigned with a modern, attractive UI/UX while preserving all business logic. This guide explains the new design system and how to use the enhanced components.

## What's New

### 1. Modern Design System
- **Glassmorphism effects** - Translucent cards with blur effects
- **Smooth animations** - Fade-in, slide-in, scale effects on all components
- **Enhanced color palette** - Updated LeetCode-inspired colors with gradients
- **Improved typography** - Better font hierarchy and spacing
- **Custom scrollbars** - Themed scrollbars matching the design
- **Loading skeletons** - Professional loading states

### 2. New Components

#### Core Components
- `modern_title()` - Animated gradient title
- `section_header()` - Headers with decorative lines
- `glass_card()` - Glassmorphism container
- `stat_card()` - Enhanced metric cards with icons and deltas
- `badge()` - Colorful labels for status/categories
- `profile_header()` - Animated profile display with gradient background
- `podium_display()` - Top 3 winners in podium layout

#### Data Visualization
- `pie_difficulty()` - Enhanced donut chart with center annotation
- `team_bar()` - Gradient bar chart for team comparison
- `activity_heatmap()` - GitHub-style contribution heatmap
- `trend_chart()` - Area chart for progress trends

#### Utilities
- `loading_skeleton()` - Loading placeholders
- `metric_grid()` - Responsive grid for metrics
- `daily_challenge_card()` - Featured challenge display

### 3. Design Tokens

All colors, spacing, and styles use CSS variables for consistency:

```css
/* Colors */
--leetcode-orange: #FFA116
--leetcode-green: #34A853
--leetcode-red: #EF4743
--leetcode-blue: #1E88E5

/* Spacing */
--space-sm: 0.5rem
--space-md: 1rem
--space-lg: 1.5rem
--space-xl: 2rem

/* Shadows */
--shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1)
--shadow-glow: 0 0 20px rgba(255, 161, 22, 0.3)
```

### 4. Theming

Both dark and light modes are fully supported with automatic theme switching:

**Dark Theme (Default)**
- Background: Deep blue-black (#0A0E1A)
- Cards: Soft dark (#1E2433)
- Text: Off-white (#F5F5F5)

**Light Theme**
- Background: White (#FFFFFF)
- Cards: White with subtle shadow
- Text: Dark gray (#1A1F2E)

## Migration Guide

### Before (Old Code)

```python
import streamlit as st

st.markdown("### 🏆 Leaderboard")
st.markdown('<div class="leetcode-card">', unsafe_allow_html=True)
# ... card content
st.markdown('</div>', unsafe_allow_html=True)
```

### After (New Code)

```python
from ui.components import section_header, glass_card

section_header("Leaderboard", "🏆")
# Content is automatically wrapped in modern glass card
```

### Component Examples

#### 1. Modern Title

```python
from ui.components import modern_title

modern_title("LeetCode Team Dashboard", "👨🏼‍💻")
```

#### 2. Stat Cards Grid

```python
from ui.components import metric_grid

metrics = [
    {"label": "Total Solved", "value": "150", "icon": "✅", "variant": "success", "delta": "+15"},
    {"label": "Team Rank", "value": "#42", "icon": "🏅", "variant": "primary"},
    {"label": "Daily Streak", "value": "7", "icon": "🔥", "variant": "warning"},
    {"label": "Acceptance Rate", "value": "85%", "icon": "📊", "variant": "info"}
]

metric_grid(metrics, columns=4)
```

#### 3. Podium Display

```python
from ui.components import podium_display

top_3 = [
    {"username": "user1", "name": "Alice", "avatar": "url1", "totalSolved": 250},
    {"username": "user2", "name": "Bob", "avatar": "url2", "totalSolved": 200},
    {"username": "user3", "name": "Charlie", "avatar": "url3", "totalSolved": 180}
]

selected = podium_display(top_3, selected_user="user1")
```

#### 4. Profile Header

```python
from ui.components import profile_header

member_data = {
    "name": "Alice Johnson",
    "username": "alice_codes",
    "avatar": "https://...",
    "realName": "Alice J.",
    "ranking": 15234,
    "totalSolved": 250,
    "totalAttempted": 300
}

profile_header(member_data)
```

#### 5. Enhanced Charts

```python
from ui.components import pie_difficulty, team_bar, trend_chart

# Difficulty breakdown
pie_difficulty(easy=100, med=80, hard=30, title="My Progress")

# Team comparison
team_bar(performance_df, title="Team Leaderboard")

# Progress trends
trend_chart(weekly_df, title="Weekly Progress")
```

#### 6. Daily Challenge Card

```python
from ui.components import daily_challenge_card

challenge = {
    "title": "Two Sum",
    "difficulty": "Easy",
    "questionId": "1",
    "date": "2025-11-20",
    "link": "https://leetcode.com/problems/two-sum"
}

daily_challenge_card(challenge)
```

#### 7. Loading States

```python
from ui.components import loading_skeleton

# While data is loading
if is_loading:
    loading_skeleton(type="card", count=3)
else:
    # Show actual data
    pass
```

## Animation Classes

Add animation classes to any HTML element:

```python
st.markdown('<div class="animate-fade-in">Content</div>', unsafe_allow_html=True)
```

Available animations:
- `animate-fade-in` - Fade in
- `animate-fade-in-up` - Fade in from bottom
- `animate-fade-in-down` - Fade in from top
- `animate-slide-in-left` - Slide from left
- `animate-slide-in-right` - Slide from right
- `animate-scale-in` - Scale up
- `animate-pulse` - Pulsing effect

## Utility Classes

```html
<!-- Text alignment -->
<div class="text-center">Centered text</div>

<!-- Flexbox -->
<div class="flex items-center gap-md">Items</div>

<!-- Spacing -->
<div class="mt-lg mb-sm">Content</div>

<!-- Opacity -->
<div class="opacity-75">Semi-transparent</div>
```

## Responsive Design

All components are mobile-responsive:

- **Desktop**: Full layout with 4-column grids
- **Tablet (≤768px)**: 2-column grids, smaller fonts
- **Mobile (≤480px)**: Single column, optimized spacing

## Best Practices

### 1. Use Semantic Components
```python
# Good
section_header("Statistics", "📊")
metric_grid(metrics, columns=4)

# Avoid
st.markdown("### 📊 Statistics")
col1, col2, col3, col4 = st.columns(4)
```

### 2. Consistent Variants
Use variant names consistently:
- `primary` - Orange (main actions)
- `success` - Green (positive metrics)
- `warning` - Yellow (caution)
- `danger` - Red (errors/hard difficulty)
- `info` - Blue (information)

### 3. Loading States
Always show loading states for async operations:
```python
with st.spinner("Loading data..."):
    data = fetch_data()

if data is None:
    loading_skeleton(type="card", count=3)
```

### 4. Accessibility
- Use descriptive button text
- Provide alt text for images
- Ensure sufficient color contrast
- Support keyboard navigation

## Color Usage Guide

| Use Case | Color | Variable | Hex |
|----------|-------|----------|-----|
| Primary actions | Orange | `--leetcode-orange` | #FFA116 |
| Success states | Green | `--leetcode-green` | #34A853 |
| Errors/Hard | Red | `--leetcode-red` | #EF4743 |
| Info/Links | Blue | `--leetcode-blue` | #1E88E5 |
| Warnings/Medium | Yellow | `--leetcode-yellow` | #FBBC04 |
| Gold medal | Gold | `--gold` | #FFD700 |
| Silver medal | Silver | `--silver` | #C0C0C0 |
| Bronze medal | Bronze | `--bronze` | #CD7F32 |

## Performance Tips

1. **Lazy load images**: Use `loading="lazy"` attribute
2. **Minimize reruns**: Use `st.cache_data` for expensive operations
3. **Optimize animations**: Keep animation durations under 500ms
4. **Reduce DOM updates**: Batch state updates together

## Browser Support

- ✅ Chrome 90+
- ✅ Firefox 88+
- ✅ Safari 14+
- ✅ Edge 90+
- ⚠️ IE 11 (limited support, no backdrop-filter)

## Troubleshooting

### Styles Not Applying
```python
# Ensure you import and call inject_base_css()
from ui.components import inject_base_css
inject_base_css()
```

### Animations Not Working
- Check that animation classes are spelled correctly
- Verify CSS is injected before components render
- Clear browser cache

### Theme Not Switching
- Streamlit's theme selector is in the sidebar menu (⋮)
- Refresh page after changing theme
- Check `.streamlit/config.toml` is configured

## Future Enhancements

Planned improvements:
- [ ] Dark/Light theme toggle button
- [ ] Customizable color schemes
- [ ] More chart types (radar, sankey, treemap)
- [ ] Interactive data tables with sorting/filtering
- [ ] Export charts as images
- [ ] Comparison mode for members
- [ ] Achievement badges system
- [ ] Notification toasts for actions

## Support

For UI/UX issues or enhancement requests, please:
1. Check this guide first
2. Review component documentation in `ui/components.py`
3. Check CSS variables in `ui/modern_styles.py`
4. Create an issue with screenshots and browser info

## Credits

Design inspiration:
- LeetCode official website
- GitHub contribution graphs
- Glassmorphism design trend
- Modern dashboard UIs (Vercel, Linear, Stripe)
