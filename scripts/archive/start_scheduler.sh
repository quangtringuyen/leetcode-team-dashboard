#!/bin/bash
# Script to start the scheduler with pydantic-settings fix
# Use this until the Docker image is rebuilt with the updated requirements.txt

echo "Starting LeetCode Dashboard Scheduler..."

# Stop and remove existing scheduler if running
sudo docker stop leetcode-scheduler 2>/dev/null
sudo docker rm leetcode-scheduler 2>/dev/null

# Start scheduler with pydantic-settings installed at runtime
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

echo "Waiting for scheduler to start..."
sleep 5

# Show logs
echo ""
echo "Scheduler logs:"
sudo docker logs leetcode-scheduler --tail 20

echo ""
echo "✅ Scheduler started successfully!"
echo "To view logs: sudo docker logs leetcode-scheduler -f"
