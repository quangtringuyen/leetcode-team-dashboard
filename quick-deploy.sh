#!/bin/bash

# Quick Deploy Script for LeetCode Team Dashboard
# Run this ON the server after SSH-ing in

set -e  # Exit on any error

echo "🚀 LeetCode Dashboard - Quick Deployment"
echo "========================================"
echo ""

# Check if we're in the right directory
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ Error: docker-compose.yml not found in current directory"
    echo "Please navigate to your leetcode-team-dashboard directory first"
    exit 1
fi

echo "📂 Current directory: $(pwd)"
echo ""

# Pull latest changes
echo "📥 Pulling latest changes from git..."
git pull
echo "✅ Git pull completed"
echo ""

# Stop containers
echo "🛑 Stopping containers..."
docker-compose down
echo "✅ Containers stopped"
echo ""

# Rebuild scheduler container without cache
echo "🔨 Rebuilding scheduler container..."
docker-compose build --no-cache scheduler
echo "✅ Rebuild completed"
echo ""

# Start containers
echo "▶️  Starting containers..."
docker-compose up -d
echo "✅ Containers started"
echo ""

# Wait for containers to initialize
echo "⏳ Waiting 10 seconds for containers to initialize..."
sleep 10
echo ""

# Show container status
echo "📊 Container status:"
docker-compose ps
echo ""

# Show scheduler logs (check for errors)
echo "📋 Scheduler logs (last 30 lines):"
docker logs --tail 30 leetcode-scheduler
echo ""

# Check if scheduler is still running
echo "🔍 Checking scheduler status..."
if docker ps | grep -q leetcode-scheduler; then
    echo "✅ Scheduler is running!"
    
    # Check if it's restarting
    RESTART_COUNT=$(docker inspect leetcode-scheduler --format='{{.RestartCount}}')
    if [ "$RESTART_COUNT" -gt 0 ]; then
        echo "⚠️  Warning: Scheduler has restarted $RESTART_COUNT times"
        echo "📋 Check the full logs with: docker logs -f leetcode-scheduler"
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
echo "  - View live logs: docker logs -f leetcode-scheduler"
echo "  - Check status: docker-compose ps"
echo "  - Restart: docker-compose restart scheduler"
