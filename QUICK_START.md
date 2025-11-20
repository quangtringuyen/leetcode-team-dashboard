# Quick Start Guide

## 🚀 Deploy in 5 Minutes

### Step 1: Get the Code
```bash
git clone <your-repo-url>
cd leetcode-team-dashboard
```

### Step 2: Configure Environment
```bash
cp .env.example .env
nano .env  # Edit AWS credentials if using S3
```

### Step 3: Start Services
```bash
docker-compose up -d
```

### Step 4: Access Dashboard
Open browser: `http://localhost:8501`

---

## 🔍 Verify Everything is Working

### Check Services
```bash
docker-compose ps
```

You should see both services running:
- `leetcode-team-dashboard` - Web interface (port 8501)
- `leetcode-scheduler` - Background data fetcher

### Check Logs
```bash
# Dashboard logs
docker-compose logs -f leetcode-dashboard

# Scheduler logs
docker-compose logs -f scheduler
```

Look for `[SUCCESS]` messages - these indicate successful API calls.

---

## ⚠️ Troubleshooting "Failed to fetch data"

If you see errors when adding team members:

### 1. Run API Test
```bash
docker exec -it leetcode-team-dashboard python test_leetcode_api.py
```

This will show you exactly what's failing:
- ✅ All PASS = Everything works
- ❌ Some FAIL = Check which test failed

### 2. Check Error Logs
```bash
docker-compose logs leetcode-dashboard | grep ERROR
```

Look for patterns:
- `[ERROR] Connection error` = Network/DNS issue
- `[ERROR] Timeout error` = Firewall blocking requests
- `[ERROR] User not found` = Invalid username
- `[ERROR] Response status: 403` = LeetCode blocking requests

### 3. Test Network
```bash
docker exec -it leetcode-team-dashboard python test_network.py
```

### Common Fixes

**Network/DNS Issues:**
```bash
# Restart with fresh DNS
docker-compose down
docker-compose up -d --build
```

**LeetCode Blocking Requests:**
- Wait 5-10 minutes (rate limiting)
- Add valid LeetCode usernames only
- Don't add too many members at once

**Firewall/Corporate Network:**
- Check if leetcode.com is accessible from your network
- Try from a different network
- Contact your IT department to whitelist leetcode.com

---

## 📊 First Time Setup

1. **Create Account**
   - Go to http://localhost:8501
   - Click "Register"
   - Create your account

2. **Add Team Members**
   - Enter valid LeetCode usernames
   - Start with 1-2 members to test
   - Wait for data to load

3. **Verify Data**
   - Check the leaderboard
   - View member profiles
   - Verify statistics are correct

4. **Set Up Scheduler**
   - Scheduler runs automatically every Monday at midnight
   - To test immediately: Set `RUN_ON_STARTUP=true` in `.env`
   - Restart: `docker-compose restart scheduler`

---

## 🔧 Common Commands

```bash
# View all logs
docker-compose logs -f

# Restart everything
docker-compose restart

# Stop everything
docker-compose down

# Update and rebuild
git pull
docker-compose down
docker-compose up -d --build

# View scheduler status
docker-compose ps scheduler
docker-compose logs -f scheduler

# Run tests
docker exec -it leetcode-team-dashboard python test_leetcode_api.py
docker exec -it leetcode-team-dashboard python test_network.py
```

---

## 📝 Configuration Tips

### Minimal .env (Local Storage)
```bash
# Auth
COOKIE_NAME=leetdash_auth
COOKIE_KEY=your-random-secret-key
COOKIE_EXPIRY_DAYS=30

# Scheduler
RUN_ON_STARTUP=false
ENVIRONMENT=production
```

### Full .env (S3 Storage)
```bash
# AWS S3
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
AWS_DEFAULT_REGION=ap-southeast-1
S3_BUCKET_NAME=your-bucket
S3_PREFIX=prod

# Auth
COOKIE_NAME=leetdash_auth
COOKIE_KEY=your-random-secret-key
COOKIE_EXPIRY_DAYS=30

# Scheduler
RUN_ON_STARTUP=false
ENVIRONMENT=production
```

---

## 🆘 Getting Help

1. **Check logs first** - Most issues are visible in logs
2. **Run diagnostics** - Use the test scripts
3. **See full guide** - Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
4. **Report issues** - Include logs and test results

---

## ✅ Success Checklist

- [ ] Both containers running (`docker-compose ps`)
- [ ] No errors in logs (`docker-compose logs`)
- [ ] API tests passing (`python test_leetcode_api.py`)
- [ ] Can access dashboard (http://localhost:8501)
- [ ] Can create account
- [ ] Can add team members
- [ ] Data loads correctly
- [ ] Scheduler shows in logs

If all checked ✅ - You're good to go! 🎉
