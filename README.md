# LeetCode Team Dashboard

A collaborative dashboard for tracking and visualizing LeetCode progress for teams, built with Streamlit.

## 🚀 Features

- **Team-based authentication:** Login/register to manage your own team.
- **Add/Remove Members:** Easily manage your team's LeetCode members.
- **Leaderboard:** See team rankings by problems solved.
- **Profile View:** View detailed stats for each member, including solved counts by difficulty.
- **Difficulty Distribution:** Interactive pie chart of solved problems by difficulty.
- **Team Performance:** Bar chart comparing all team members.
- **Automatic Data Capture:** Scheduler service automatically fetches and records data every Monday at midnight.
- **Week-over-Week Tracking:** Track progress over time with historical data snapshots.
- **Dark/Light Theme Support:** UI adapts to Streamlit theme.
- **Responsive Design:** Works on desktop and mobile.
- **Secure Data:** Passwords are hashed; each team's data is private.

## 🌐 Live Demo

Deployed at:  
**[https://leetcode-team-dashboard.streamlit.app/](https://leetcode-team-dashboard.streamlit.app/)**

## 🛠️ Setup & Installation

### Option 1: Docker (Recommended)

1. **Clone the repository:**
   ```bash
   git clone <your-repo-url>
   cd leetcode-team-dashboard
   ```

2. **Configure environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your AWS credentials (if using S3) and other settings
   ```

3. **Start with Docker Compose:**
   ```bash
   docker-compose up -d
   ```

4. **Access the dashboard:**
   - Dashboard: http://localhost:8501
   - The scheduler service runs automatically in the background

5. **View logs:**
   ```bash
   docker-compose logs -f scheduler    # View scheduler logs
   docker-compose logs -f leetcode-dashboard  # View dashboard logs
   ```

### Option 2: Local Python

1. **Clone the repository:**
   ```bash
   git clone <your-repo-url>
   cd leetcode-team-dashboard
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Run the dashboard:**
   ```bash
   streamlit run app.py
   ```

5. **Run the scheduler (optional, in a separate terminal):**
   ```bash
   python scheduler.py
   ```

## 📦 File Structure

- `app.py` — Main Streamlit app.
- `scheduler.py` — Background service for automatic data fetching every Monday at midnight.
- `docker-compose.yml` — Docker services configuration (dashboard + scheduler).
- `utils/leetcodeapi.py` — Fetches LeetCode user data via GraphQL.
- `utils/auth.py` — Handles authentication and user management.
- `services/` — Service layer for members, history, and LeetCode data.
- `core/storage.py` — Storage abstraction (supports local files or S3).
- `data/members.json` — Stores team member data (per user/team).
- `data/users.json` — Stores user credentials (hashed).
- `data/history.json` — Stores weekly snapshots of team progress.
- `.env` — Environment variables (credentials, configuration).
- `requirements.txt` — Python dependencies.

## 📝 Usage

- **Login/Register:** Create an account to manage your team.
- **Add Members:** Enter LeetCode username and full name to add a member.
- **Remove Members:** Select and remove members from your team.
- **View Stats:** Click on a member in the leaderboard to view their profile and stats.
- **Automatic Tracking:** The scheduler service automatically captures data every Monday at 00:00 (midnight).
- **Manual Refresh:** You can still manually refresh data in the dashboard at any time.

## ⏰ Scheduler Configuration

The scheduler service automatically fetches and records LeetCode data for all teams every Monday at midnight.

### Environment Variables

- `RUN_ON_STARTUP` — Set to `true` to run data fetch immediately on startup (useful for testing). Default: `false`
- `ENVIRONMENT` — Set environment name (e.g., `production`, `development`). Default: `production`

### Viewing Scheduler Status

```bash
# Check if scheduler is running
docker-compose ps

# View scheduler logs
docker-compose logs -f scheduler

# Restart scheduler
docker-compose restart scheduler
```

### Customizing Schedule

To change the schedule from Monday at midnight, edit the schedule configuration in [scheduler.py](scheduler.py:111):

```python
# Change from:
schedule.every().monday.at("00:00").do(self.fetch_and_record_all_teams)

# To (examples):
schedule.every().day.at("00:00").do(self.fetch_and_record_all_teams)  # Daily at midnight
schedule.every().sunday.at("23:59").do(self.fetch_and_record_all_teams)  # Sunday at 11:59 PM
schedule.every(6).hours.do(self.fetch_and_record_all_teams)  # Every 6 hours
```

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
## Open For collaboration 
contatct saralaufeysonlaya08@gmail.com or view my github profile for more info 

**Built with [Streamlit](https://streamlit.io/) and the LeetCode API.**
