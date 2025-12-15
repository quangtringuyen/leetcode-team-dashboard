# Scheduler Startup Guide

## Current Status

The scheduler container requires `pydantic-settings` which is not in the current Docker image due to disk space issues during rebuild.

## Quick Start

### Option 1: Use the Startup Script (Recommended)

```bash
cd /volume2/docker/leetcode-dashboard
git pull
./start_scheduler.sh
```

This script:
- Stops any existing scheduler
- Starts a new scheduler with pydantic-settings installed at runtime
- Shows the logs to verify it's working

### Option 2: Manual Start

```bash
sudo docker stop leetcode-scheduler 2>/dev/null
sudo docker rm leetcode-scheduler 2>/dev/null

sudo docker run -d \
  --name leetcode-scheduler \
  --restart unless-stopped \
  -v /volume2/docker/leetcode-dashboard/data:/app/data \
  --env-file /volume2/docker/leetcode-dashboard/.env \
  --dns 8.8.8.8 \
  --dns 8.8.4.4 \
  --dns 1.1.1.1 \
  leetcode-dashboard-scheduler:latest \
  sh -c "pip install pydantic-settings && python scheduler.py"
```

## Verify Scheduler is Running

```bash
# Check logs
sudo docker logs leetcode-scheduler --tail 30

# You should see:
# ✅ "Snapshot: Every monday at 07:30"
# ✅ "Notifications: Every 15 minutes"
# ✅ No "unable to open database file" errors
```

## Permanent Fix (When Disk Space Available)

When you have freed up disk space:

```bash
cd /volume2/docker/leetcode-dashboard
git pull

# Clean up Docker to free space
sudo docker system prune -a --volumes -f

# Rebuild scheduler
sudo docker-compose build --no-cache scheduler
sudo docker-compose up -d scheduler
```

The `requirements.txt` already has the fix, so the rebuild will include `pydantic-settings`.

## Troubleshooting

### Scheduler keeps restarting
- Check logs: `sudo docker logs leetcode-scheduler`
- If you see "ModuleNotFoundError: No module named 'pydantic_settings'", use the startup script

### Database connection errors
- Verify the data volume is mounted: `sudo docker inspect leetcode-scheduler | grep -A 5 Mounts`
- Should show: `/volume2/docker/leetcode-dashboard/data:/app/data`

### Scheduler not running at all
- Check if container exists: `sudo docker ps -a | grep scheduler`
- Start it with the script: `./start_scheduler.sh`
