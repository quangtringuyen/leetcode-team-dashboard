# Scheduler Container Fix Deployment Guide

## Problem Fixed
The scheduler container was restarting because the `backend` directory was missing `__init__.py` files, preventing Python from treating it as a package. The scheduler imports from `backend.utils` and `backend.core`, which requires these directories to be proper Python packages.

## Changes Made
1. ✅ Created `backend/__init__.py`
2. ✅ Created `backend/core/__init__.py`
3. ✅ Committed and pushed to GitHub
4. ✅ Created deployment scripts

## Deployment Instructions

### Option 1: Using the Quick Deploy Script (Recommended)

1. **SSH into your server** (you already have a terminal open):
   ```bash
   ssh quangtringuyen@192.168.1.7
   ```

2. **Navigate to your project directory**:
   ```bash
   cd /path/to/leetcode-team-dashboard
   # Common paths on Synology NAS:
   # - /volume1/docker/leetcode-team-dashboard
   # - /home/quangtringuyen/leetcode-team-dashboard
   ```

3. **Pull the latest changes** (includes the fix):
   ```bash
   git pull
   ```

4. **Run the quick deploy script**:
   ```bash
   ./quick-deploy.sh
   ```

   This script will:
   - Pull latest changes
   - Stop the containers
   - Rebuild the scheduler container
   - Start all containers
   - Show you the status and logs
   - Verify the scheduler is running properly

### Option 2: Manual Deployment

If the script doesn't work, run these commands manually:

```bash
# Pull latest changes
git pull

# Stop containers
docker-compose down

# Rebuild scheduler (no cache to ensure fresh build)
docker-compose build --no-cache scheduler

# Start all containers
docker-compose up -d

# Check status
docker-compose ps

# View scheduler logs
docker logs -f leetcode-scheduler
```

## Verification

After deployment, the scheduler should:
1. ✅ Start successfully without restarting
2. ✅ Show "Imports completed successfully." in the logs
3. ✅ Show "Scheduler started. Waiting for scheduled tasks..." in the logs
4. ✅ Not have any import errors

### Check the logs:
```bash
docker logs leetcode-scheduler --tail 50
```

You should see output like:
```
Starting scheduler service...
Importing core modules...
Importing backend modules...
Imports completed successfully.
[timestamp] - __main__ - INFO - ============================================================
[timestamp] - __main__ - INFO - LeetCode Team Dashboard - Data Scheduler
[timestamp] - __main__ - INFO - ============================================================
[timestamp] - __main__ - INFO - Initialized DataScheduler with ...
[timestamp] - __main__ - INFO - Configuring scheduler with settings from database:
[timestamp] - __main__ - INFO - Scheduler started. Waiting for scheduled tasks...
Entering main loop...
```

### Check container is running and not restarting:
```bash
docker ps | grep scheduler
```

Should show status as "Up X minutes" not "Up X seconds" (which indicates constant restarting).

### Check restart count:
```bash
docker inspect leetcode-scheduler --format='{{.RestartCount}}'
```

Should show `0` after a successful deployment.

## Troubleshooting

If the scheduler is still restarting:

1. **Check for other import errors**:
   ```bash
   docker logs leetcode-scheduler --tail 100
   ```

2. **Check if all required files exist in the container**:
   ```bash
   docker exec leetcode-scheduler ls -la backend/
   docker exec leetcode-scheduler ls -la backend/core/
   docker exec leetcode-scheduler python -c "from backend.utils.leetcodeapi import fetch_user_data; print('OK')"
   ```

3. **Rebuild from scratch**:
   ```bash
   docker-compose down
   docker-compose build --no-cache
   docker-compose up -d
   ```

4. **Check environment variables** (make sure .env is properly loaded):
   ```bash
   docker exec leetcode-scheduler printenv | grep -E 'AWS|DISCORD|DATABASE'
   ```

## Monitoring

To monitor the scheduler in real-time:
```bash
docker logs -f leetcode-scheduler
```

Press `Ctrl+C` to exit the log view.

## Success Criteria

✅ Container stays running (no restarts)
✅ No import errors in logs
✅ "Scheduler started. Waiting for scheduled tasks..." message appears
✅ Restart count is 0
✅ Container status shows "Up" for more than 1 minute
