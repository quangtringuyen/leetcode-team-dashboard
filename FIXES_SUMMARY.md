# Scheduler & Notification Fixes - Summary

## Issues Fixed Today (Dec 7, 2025)

### 1. ✅ Scheduler Container Restarting Issue

**Problem:** The scheduler container kept restarting every few seconds (9+ restarts).

**Root Causes Found:**
1. **Missing `__init__.py` files** - The `backend/` and `backend/core/` directories were missing `__init__.py` files, preventing Python from treating them as packages. This caused import errors for:
   - `from backend.utils.leetcodeapi import fetch_user_data`
   - `from backend.core.config import settings`
   - `from backend.core.storage import read_json, write_json`

2. **Critical Indentation Bug** - The main `while True` loop (lines 329-338) in `scheduler.py` was accidentally indented inside the `backup_data()` method instead of being part of `run_scheduler()`. This caused the program to exit immediately after logging "Scheduler started" without entering the infinite loop.

**Fixes Applied:**
- Created `backend/__init__.py` (empty file)
- Created `backend/core/__init__.py` (empty file)
- Fixed indentation in `scheduler.py` to move the main loop back into `run_scheduler()` method

**Verification:**
After fixes, scheduler logs should show:
```
Starting scheduler service...
Importing core modules...
Importing backend modules...
Imports completed successfully.
Scheduler started. Waiting for scheduled tasks...
Scheduled jobs:
  - Every 1 week at 00:00:00 do fetch_and_record_all_teams()
  - Every 15 minutes do check_new_submissions()
  - ...
Entering main loop...
Heartbeat: Scheduler is alive
```

---

### 2. ✅ Notification Service Bug

**Problem:** Notifications weren't being sent when team members solved problems, both from:
- The automated scheduler (every 15 minutes)
- The manual "Check for new submissions" button on the Dashboard

**Root Cause:**
The `notification_service.py` (line 404) had a broken import and incorrect API usage:
```python
from backend.utils.leetcodeapi import fetch_recent_submissions, fetch_problem_details
```

Problems:
- `fetch_problem_details` doesn't exist (should be `_fetch_problem_details` with underscore, which is private)
- The code was making multiple API calls per problem to fetch difficulty
- This was inefficient and caused errors

**Fix Applied:**
Replaced the broken code with the correct function that already returns all needed data:
```python
from backend.utils.leetcodeapi import fetch_submissions_with_tags
recent_subs = fetch_submissions_with_tags(member, limit=max(10, diff * 2))
```

Benefits:
- ✅ One API call instead of many
- ✅ Already includes difficulty information
- ✅ More efficient and faster
- ✅ No more import errors

---

### 3. ✅ Frontend Notification Feedback

**Problem:** When clicking "Check for new submissions" button on Dashboard, there was no visual feedback to tell the user if:
- Notifications were found
- How many were found
- If there was an error

**Fix Applied:**
Added toast notifications to `NotificationCenter.tsx`:
- Success toast: "Found X new notifications!" (with description to check Discord)
- Info toast: "No new submissions found" (when all caught up)
- Error toast: "Failed to check submissions" (on API error)

---

## Deployment Instructions

### For Scheduler Container (on Server):

```bash
cd /volume1/docker/leetcode-dashboard
git pull origin master
sudo docker-compose -f docker-compose.fullstack.yml build --no-cache scheduler
sudo docker-compose -f docker-compose.fullstack.yml up -d scheduler

# Verify it's running
sudo docker logs --tail 30 leetcode-scheduler
sudo docker ps | grep scheduler
sudo docker inspect leetcode-scheduler --format='{{.RestartCount}}'  # Should be 0
```

### For Frontend (on Server):

```bash
cd /volume1/docker/leetcode-dashboard
git pull origin master
sudo docker-compose -f docker-compose.fullstack.yml build --no-cache frontend
sudo docker-compose -f docker-compose.fullstack.yml up -d frontend
```

---

## How Notifications Now Work

### Automated (Scheduler):
1. **Every 15 minutes**, the scheduler:
   - Fetches current LeetCode data for all team members
   - Compares with last known state
   - Detects new problems solved
   - Creates notifications and sends to:
     - ✅ Discord webhook
     - ✅ In-app notification center (database)

2. **Every Monday at midnight**:
   - Takes weekly snapshot of all team member stats
   - Records to history for trend analysis

3. **Every day at 8:00 AM**:
   - Fetches daily LeetCode challenge
   - Sends notification to Discord

### Manual (Dashboard Button):
1. User clicks "Check for new submissions" button
2. Backend:
   - Fetches current data for all team members
   - Compares with last state
   - Creates notifications
   - Sends to Discord
   - Returns count to frontend
3. Frontend:
   - Shows toast with count
   - Refreshes notification list
   - User can see notifications in the panel

---

## Files Changed

### Backend:
1. `backend/__init__.py` - Created (empty file for package recognition)
2. `backend/core/__init__.py` - Created (empty file for package recognition)
3. `scheduler.py` - Fixed indentation bug in main loop
4. `backend/utils/notification_service.py` - Fixed API import and usage

### Frontend:
1. `frontend/src/components/dashboard/NotificationCenter.tsx` - Added toast feedback

### Scripts:
1. `deploy.sh` - Created deployment automation script
2. `quick-deploy.sh` - Created quick deployment script for server
3. `DEPLOYMENT_GUIDE.md` - Created comprehensive deployment guide

---

## Testing the Fixes

### Test Scheduler is Running:
```bash
# Should show "Up" status (not constantly restarting)
sudo docker ps | grep scheduler

# Should show 0 restarts
sudo docker inspect leetcode-scheduler --format='{{.RestartCount}}'

# Should show "Entering main loop..." and periodic heartbeats
sudo docker logs -f leetcode-scheduler
```

### Test Notifications:
1. **Solve a LeetCode problem** with your team member account
2. **Wait 15 minutes** for scheduler to run, OR
3. **Click "Check for new submissions"** button on Dashboard
4. You should see:
   - ✅ Toast message showing notification count
   - ✅ Notification in the Dashboard notification panel
   - ✅ Message in Discord channel

### Check Logs for Successful Notification:
```bash
sudo docker logs leetcode-scheduler | grep -A 5 "Checking for new submissions"
```

Should show:
```
INFO - Checking for new submissions...
INFO - Detected change for username: 100 -> 101 (+1)
INFO - Processing 1 new problems for username
INFO - Problem 1: Two Sum (Easy)
INFO - Sent Discord notification: 🚀 Name solved 1 new problem!
INFO - Submission check completed.
```

---

## Troubleshooting

### If scheduler still restarts:
```bash
# Get full error logs
sudo docker logs leetcode-scheduler --tail 200

# Check if __init__.py files exist in container
sudo docker exec leetcode-scheduler ls -la backend/
sudo docker exec leetcode-scheduler ls -la backend/core/

# Test import inside container
sudo docker exec leetcode-scheduler python -c "from backend.utils.leetcodeapi import fetch_user_data; print('OK')"
```

### If notifications don't appear:
1. Check Discord webhook is configured in `.env`:
   ```bash
   sudo docker exec leetcode-scheduler printenv | grep DISCORD
   ```

2. Check last state file is being updated:
   ```bash
   sudo docker exec leetcode-scheduler cat /app/data/last_state.json
   ```

3. Test Discord manually:
   - Go to Dashboard
   - Settings page
   - Click "Test Discord Notification"

---

## Summary of Commit History

1. `6fa665b` - Fix scheduler container restart issue by adding missing __init__.py files to backend package
2. `308551a` - Add deployment scripts for server updates
3. `5889591` - Update deployment scripts for fullstack docker-compose
4. `d0475a8` - Fix critical indentation bug: move main loop out of backup_data method
5. `f3bb7c0` - Fix notification bug: use correct API function for fetching submissions with difficulty
6. `2ddfec3` - Add toast feedback for check submissions button to show notification count

All fixes pushed to: `origin/master`

---

## Next Steps / Future Improvements

1. **Persistent In-App Notifications**: Currently in-app notifications are stored in memory and lost on restart. Consider moving to database-only storage.

2. **Real-time Updates**: Add WebSocket support for real-time notification updates without page refresh.

3. **Notification History**: Add a dedicated page to view all past notifications.

4. **Customizable Check Interval**: Allow users to configure how often the scheduler checks (currently fixed at 15 minutes).

5. **Rate Limiting**: Add rate limiting to prevent too many manual checks in short time.
