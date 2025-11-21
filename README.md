# LeetCode Team Dashboard

A collaborative platform for tracking and visualizing LeetCode progress for teams, powered by a modern FastAPI backend with Docker deployment support.

> **Note:** This project has been migrated from Streamlit to a FastAPI REST API backend. The Streamlit version is still available in git history if needed.

## 🚀 Features

### Backend API (FastAPI)
- **RESTful API:** Modern REST API with OpenAPI documentation
- **JWT Authentication:** Secure token-based authentication
- **Team Management:** Add, remove, and manage team members via API
- **LeetCode Integration:** Real-time data fetching from LeetCode
- **Historical Tracking:** Weekly snapshots and trend analysis
- **Flexible Storage:** Supports both local JSON files and AWS S3
- **Docker Ready:** Containerized deployment with health checks
- **NAS Optimized:** Guides for Synology, QNAP, TrueNAS, Unraid
- **Production Ready:** Comprehensive testing, monitoring, and logging
- **Frontend Agnostic:** Use with React, Vue, Mobile apps, or any frontend

### Core Features
- **Team-based authentication:** Secure login/register with JWT tokens
- **Member Management:** Track multiple team members' LeetCode progress
- **Leaderboard Data:** Rankings by problems solved, difficulty levels
- **User Statistics:** Detailed stats including recent submissions
- **Automatic Snapshots:** Scheduler service records data every Monday at midnight
- **Historical Analytics:** Week-over-week progress tracking
- **Daily Challenges:** Fetch today's LeetCode daily challenge
- **Secure & Private:** Passwords hashed with bcrypt; team data isolated

## 🛠️ Setup & Installation

### Quick Start (60 seconds) ⚡

The fastest way to get started:

```bash
# 1. Clone the repository
git clone <your-repo-url>
cd leetcode-team-dashboard

# 2. Run automated deployment
./deploy-nas.sh
```

That's it! The script will configure everything and start the services.

**Access your API:**
- API Documentation: http://localhost:8000/api/docs
- Health Check: http://localhost:8000/api/health

### Manual Docker Deployment

For more control over the deployment:

```bash
# 1. Clone the repository
git clone <your-repo-url>
cd leetcode-team-dashboard

# 2. Configure environment variables
cp .env.backend.example .env
# Generate a secret key:
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
# Edit .env and set SECRET_KEY with the generated value

# 3. Start services with Docker Compose
docker compose -f docker-compose.backend.yml up -d

# 4. Verify deployment
docker compose -f docker-compose.backend.yml ps
curl http://localhost:8000/api/health
```

**Access URLs:**
- **API Docs (Swagger):** http://localhost:8000/api/docs
- **ReDoc:** http://localhost:8000/api/redoc
- **Health Check:** http://localhost:8000/api/health

### Local Development

For development and testing:

```bash
# 1. Clone and enter directory
git clone <your-repo-url>
cd leetcode-team-dashboard

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements_backend.txt

# 4. Configure environment
cp .env.backend.example .env
nano .env  # Set SECRET_KEY and other settings

# 5. Run the API server
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

# 6. Run tests (optional)
python test_backend.py
pytest backend/tests/
```

### NAS-Specific Deployment

For Synology, QNAP, TrueNAS, Unraid, and other NAS devices, see the comprehensive guide:

📖 **[NAS_DEPLOYMENT_GUIDE.md](NAS_DEPLOYMENT_GUIDE.md)** - Detailed instructions with GUI and SSH methods for each platform

## 📦 Project Structure

```
leetcode-team-dashboard/
├── backend/                          # FastAPI Application
│   ├── main.py                      # Main API entry point
│   ├── api/                         # API Endpoints
│   │   ├── auth.py                  # Authentication (login, register, JWT)
│   │   ├── team.py                  # Team member management
│   │   ├── leetcode.py              # LeetCode data integration
│   │   └── analytics.py             # Historical data & analytics
│   ├── core/                        # Core Modules
│   │   ├── config.py                # Configuration & settings
│   │   ├── security.py              # JWT & password handling
│   │   └── storage.py               # S3 and local file storage
│   └── tests/                       # Test Suite
│       └── test_api.py              # API endpoint tests
│
├── utils/                           # Business Logic (unchanged)
│   └── leetcodeapi.py               # LeetCode GraphQL integration
│
├── Docker & Deployment
│   ├── Dockerfile.backend           # Backend container image
│   ├── docker-compose.backend.yml   # Service orchestration
│   ├── deploy-nas.sh                # Automated deployment script
│   └── nginx/                       # Nginx reverse proxy config
│
├── Configuration
│   ├── .env.backend.example         # Environment template
│   ├── requirements_backend.txt     # Backend dependencies
│   └── .env                         # Your environment variables (create this)
│
├── Data Storage (auto-created)
│   ├── data/users.json              # User credentials (hashed)
│   ├── data/members.json            # Team members by user
│   ├── data/history.json            # Weekly snapshots
│   └── logs/                        # Application logs
│
└── Documentation
    ├── README.md                    # This file
    ├── README.Docker.md             # Docker quick start guide
    ├── NAS_DEPLOYMENT_GUIDE.md      # Comprehensive NAS deployment
    ├── DEPLOYMENT_SUMMARY.md        # Deployment options overview
    └── NO_STREAMLIT_MIGRATION.md    # Migration details
```

## 📝 API Usage

### Quick Start with API

1. **Access API Documentation:**
   ```
   http://localhost:8000/api/docs
   ```
   Interactive Swagger UI with all endpoints

2. **Register a User:**
   ```bash
   curl -X POST http://localhost:8000/api/auth/register \
     -H "Content-Type: application/json" \
     -d '{"username":"myuser","email":"user@example.com","password":"mypassword"}'
   ```

3. **Login (Get JWT Token):**
   ```bash
   curl -X POST http://localhost:8000/api/auth/login \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "username=myuser&password=mypassword"
   ```
   Returns: `{"access_token": "your-jwt-token", "token_type": "bearer"}`

4. **Add Team Member:**
   ```bash
   curl -X POST http://localhost:8000/api/team/members \
     -H "Authorization: Bearer your-jwt-token" \
     -H "Content-Type: application/json" \
     -d '{"username":"leetcode_user","name":"John Doe"}'
   ```

5. **Get Team Leaderboard:**
   ```bash
   curl -X GET http://localhost:8000/api/team/members \
     -H "Authorization: Bearer your-jwt-token"
   ```

### API Endpoints

**Authentication:**
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login and get JWT token
- `GET /api/auth/me` - Get current user info

**Team Management:**
- `GET /api/team/members` - List all team members with stats
- `POST /api/team/members` - Add new team member
- `DELETE /api/team/members/{username}` - Remove member

**LeetCode Data:**
- `GET /api/leetcode/user/{username}` - Get user stats
- `GET /api/leetcode/submissions/{username}` - Recent submissions
- `GET /api/leetcode/daily-challenge` - Today's challenge

**Analytics:**
- `GET /api/analytics/history` - Get weekly snapshots
- `POST /api/analytics/snapshot` - Create snapshot manually
- `GET /api/analytics/trends` - Get team trends

**Full documentation:** http://localhost:8000/api/docs

## ⚙️ Configuration

### Environment Variables

Create a `.env` file from the template:

```bash
cp .env.backend.example .env
```

**Required Settings:**

```bash
# REQUIRED: Generate with: python3 -c "import secrets; print(secrets.token_urlsafe(32))"
SECRET_KEY=your-random-secret-key-here
```

**Optional Settings:**

```bash
# AWS S3 Storage (leave empty for local file storage)
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_DEFAULT_REGION=ap-southeast-1
S3_BUCKET_NAME=
S3_PREFIX=prod

# Application Settings
ENVIRONMENT=production
LOG_LEVEL=info
RUN_ON_STARTUP=false  # Run snapshot on startup

# CORS Origins (add your frontend URL)
CORS_ORIGINS=http://localhost:3000,http://localhost:8000

# JWT Token expiration (minutes, default: 7 days)
ACCESS_TOKEN_EXPIRE_MINUTES=10080
```

### ⏰ Scheduler Service

The scheduler service automatically captures team data every Monday at midnight.

**Check Status:**
```bash
docker compose -f docker-compose.backend.yml ps
docker compose -f docker-compose.backend.yml logs -f scheduler
```

**Customize Schedule:**
Edit `scheduler.py` to change the schedule:
```python
schedule.every().monday.at("00:00").do(...)  # Current: Monday midnight
schedule.every().day.at("00:00").do(...)     # Daily midnight
schedule.every(6).hours.do(...)              # Every 6 hours
```

## 🔒 Security Notes

- Passwords are hashed before storage.
- Each user's/team's data is isolated.
- For production, use HTTPS and consider a real database for better security.

## 🧪 Testing

### Quick Health Check

```bash
# Check if API is running
curl http://localhost:8000/api/health

# Expected response:
# {"status":"healthy","service":"LeetCode Team Dashboard API","version":"2.0.0"}
```

### Run Full Test Suite

```bash
# If using Docker
docker exec leetcode-api python test_backend.py

# If running locally
python test_backend.py
pytest backend/tests/
```

**Test Results:** All 5/5 tests passing ✅

### Test Coverage

- ✅ Imports and dependencies
- ✅ Password hashing and verification
- ✅ Storage operations (S3 and local)
- ✅ API creation and endpoints
- ✅ LeetCode API integration

## 🔧 Troubleshooting

### Service Won't Start

```bash
# Check logs
docker compose -f docker-compose.backend.yml logs api

# Common fixes:
# 1. Port 8000 in use
lsof -i :8000  # Find and kill conflicting process

# 2. Missing .env file
cp .env.backend.example .env

# 3. Permission issues
chmod -R 755 data/
```

### Can't Access API

```bash
# Test locally first
curl http://localhost:8000/api/health

# Check container status
docker compose -f docker-compose.backend.yml ps
# Should show "Up (healthy)"

# Check firewall (allow port 8000)
```

### LeetCode API Errors

```bash
# Test connectivity
docker exec leetcode-api curl -I https://leetcode.com

# Already configured with public DNS (8.8.8.8, 1.1.1.1)
# Check logs for specific errors
docker compose -f docker-compose.backend.yml logs -f api
```

**For detailed troubleshooting:** See [NAS_DEPLOYMENT_GUIDE.md](NAS_DEPLOYMENT_GUIDE.md#troubleshooting)

## 🚀 Deployment Options

### Choose Your Deployment Method

| Method | Best For | Documentation | Time |
|--------|----------|---------------|------|
| **Automated Script** | Quick setup, NAS users | Run `./deploy-nas.sh` | 2 min |
| **Manual Docker** | Customization | [README.Docker.md](README.Docker.md) | 5 min |
| **NAS-Specific** | Synology, QNAP, TrueNAS, Unraid | [NAS_DEPLOYMENT_GUIDE.md](NAS_DEPLOYMENT_GUIDE.md) | 5-10 min |
| **Local Development** | Testing, development | See above | 10 min |

### Production Considerations

- ✅ Generate unique SECRET_KEY
- ✅ Enable HTTPS (nginx or NAS reverse proxy)
- ✅ Configure firewall (restrict port 8000)
- ✅ Set up automated backups
- ✅ Monitor logs and health checks
- ✅ Keep Docker images updated

**See:** [DEPLOYMENT_SUMMARY.md](DEPLOYMENT_SUMMARY.md) for complete deployment overview

## 📚 Documentation

- **[README.md](README.md)** - This file, main overview
- **[README.Docker.md](README.Docker.md)** - Docker deployment quick start
- **[NAS_DEPLOYMENT_GUIDE.md](NAS_DEPLOYMENT_GUIDE.md)** - Comprehensive NAS deployment guide
- **[DEPLOYMENT_SUMMARY.md](DEPLOYMENT_SUMMARY.md)** - Deployment options overview
- **[NO_STREAMLIT_MIGRATION.md](NO_STREAMLIT_MIGRATION.md)** - Streamlit to FastAPI migration details
- **[API Documentation](http://localhost:8000/api/docs)** - Interactive API docs (after deployment)

## 🎯 Frontend Development

The backend API is ready for any frontend framework:

**Recommended Frameworks:**
- React / Next.js (Web)
- Vue / Nuxt (Web)
- Flutter (Mobile)
- React Native (Mobile)
- Electron / Tauri (Desktop)

**Getting Started:**
1. API is already CORS-configured for `localhost:3000`
2. Use JWT bearer token authentication
3. Full API documentation at `http://localhost:8000/api/docs`
4. Example API calls provided in this README

## 🔐 Security

- ✅ Passwords hashed with bcrypt
- ✅ JWT token-based authentication
- ✅ CORS protection
- ✅ Team data isolation
- ✅ Environment variable configuration
- ✅ Health check endpoints
- ⚠️ For production: Use HTTPS, configure firewall, enable monitoring

## 👩‍💻 Developed By

Small scale project - suitable for small to medium teams (up to ~100 members)

Original developer: @saralaufeyson

## 📄 License

MIT License

## 🤝 Open For Collaboration

Contact: saralaufeysonlaya08@gmail.com

For more info, visit the GitHub profile

---

**Built with [FastAPI](https://fastapi.tiangolo.com/), Docker, and the LeetCode GraphQL API** 🚀
