#!/bin/bash

# Quick Deploy Script for LeetCode Team Dashboard
# Run this ON the server after SSH-ing in

set -e  # Exit on any error

echo "🚀 LeetCode Dashboard - Quick Deployment"
echo "========================================"
echo ""

# Check if we're in the right directory
if [ ! -f "docker-compose.fullstack.yml" ]; then
    echo "❌ Error: docker-compose.fullstack.yml not found in current directory"
    echo "Please navigate to your leetcode-team-dashboard directory first"
    exit 1
fi

echo "📂 Current directory: $(pwd)"
echo ""

# Pull latest changes
echo "📥 Pulling latest changes from git..."
git pull origin master
echo "✅ Git pull completed"
echo ""

# Rebuild scheduler container without cache
echo "🔨 Rebuilding scheduler container..."
sudo docker-compose -f docker-compose.fullstack.yml build --no-cache scheduler
echo "✅ Rebuild completed"
echo ""

# Restart scheduler
echo "▶️  Starting scheduler..."
sudo docker-compose -f docker-compose.fullstack.yml up -d scheduler
echo "✅ Scheduler started"
echo ""

# Wait for container to initialize
echo "⏳ Waiting 5 seconds for container to initialize..."
sleep 5
echo ""

# Show container status
echo "📊 Container status:"
sudo docker-compose -f docker-compose.fullstack.yml ps scheduler
echo ""

# Show scheduler logs (check for errors)
echo "📋 Scheduler logs (last 30 lines):"
sudo docker logs --tail 30 leetcode-scheduler
echo ""

# Check if scheduler is still running
echo "🔍 Checking scheduler status..."
if sudo docker ps | grep -q leetcode-scheduler; then
    echo "✅ Scheduler is running!"
    
    # Check if it's restarting
    RESTART_COUNT=$(sudo docker inspect leetcode-scheduler --format='{{.RestartCount}}')
    if [ "$RESTART_COUNT" -gt 0 ]; then
        echo "⚠️  Warning: Scheduler has restarted $RESTART_COUNT times"
        echo "📋 Check the full logs with: sudo docker logs -f leetcode-scheduler"
    else
        echo "✅ No restarts detected - looking good!"
    fi
else
    echo "❌ Scheduler is not running! Check logs above for errors."
    exit 1
fi

echo ""
echo "🎉 Deployment completed!"
echo ""
echo "💡 Useful commands:"
echo "  - View live logs: sudo docker logs -f leetcode-scheduler"
echo "  - Check status: sudo docker-compose -f docker-compose.fullstack.yml ps"
echo "  - Restart: sudo docker-compose -f docker-compose.fullstack.yml restart scheduler"
