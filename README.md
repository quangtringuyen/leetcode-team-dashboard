# LeetCode Team Dashboard

A collaborative dashboard for tracking and visualizing LeetCode progress for teams, built with Streamlit.

## 🚀 Features

- **Team-based authentication:** Login/register to manage your own team.
- **Add/Remove Members:** Easily manage your team's LeetCode members.
- **Leaderboard:** See team rankings by problems solved.
- **Profile View:** View detailed stats for each member, including solved counts by difficulty.
- **Difficulty Distribution:** Interactive pie chart of solved problems by difficulty.
- **Team Performance:** Bar chart comparing all team members.
- **Dark/Light Theme Support:** UI adapts to Streamlit theme.
- **Responsive Design:** Works on desktop and mobile.
- **Secure Data:** Passwords are hashed; each team's data is private.

## 🌐 Live Demo

Deployed at:  
**[https://leetcode-team-dashboard.streamlit.app/](https://leetcode-team-dashboard.streamlit.app/)**

## 🛠️ Setup & Installation

1. **Clone the repository:**
   ```bash
   git clone <your-repo-url>
   cd leetcode-team-dashboard
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run locally:**
   ```bash
   streamlit run app.py
   ```

## 📦 File Structure

- `app.py` — Main Streamlit app.
- `utils/leetcodeapi.py` — Fetches LeetCode user data via GraphQL.
- `utils/auth.py` — Handles authentication and user management.
- `data/members.json` — Stores team member data (per user/team).
- `data/users.json` — Stores user credentials (hashed).
- `requirements.txt` — Python dependencies.

## 📝 Usage

- **Login/Register:** Create an account to manage your team.
- **Add Members:** Enter LeetCode username and full name to add a member.
- **Remove Members:** Select and remove members from your team.
- **View Stats:** Click on a member in the leaderboard to view their profile and stats.

## 🔒 Security Notes

- Passwords are hashed before storage.
- Each user's/team's data is isolated.
- For production, use HTTPS and consider a real database for better security.

## 👩‍💻 Developed By
Its a small scale project do not use it for huge teamsizes
@saralaufeyson

## 📄 License

MIT License

---

**Built with [Streamlit](https://streamlit.io/) and the LeetCode API.**
