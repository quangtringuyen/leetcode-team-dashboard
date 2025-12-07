#!/bin/bash

# Deployment script for LeetCode Team Dashboard
# This script pulls the latest changes and rebuilds the Docker containers on the NAS server

set -e  # Exit on any error

# Server configuration
SERVER_USER="quangtringuyen"
SERVER_HOST="192.168.1.7"
PROJECT_PATH="/volume1/docker/leetcode-team-dashboard"  # Adjust this path to match your NAS setup

echo "🚀 Starting deployment to $SERVER_HOST..."
echo ""

# SSH into server and execute deployment commands
ssh "${SERVER_USER}@${SERVER_HOST}" << 'EOF'
set -e

# Navigate to project directory
cd ${PROJECT_PATH:-/volume1/docker/leetcode-team-dashboard}

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

# Rebuild containers without cache
echo "🔨 Rebuilding containers (this may take a few minutes)..."
docker-compose build --no-cache scheduler
echo "✅ Rebuild completed"
echo ""

# Start containers
echo "▶️  Starting containers..."
docker-compose up -d
echo "✅ Containers started"
echo ""

# Wait a moment for containers to initialize
echo "⏳ Waiting 10 seconds for containers to initialize..."
sleep 10
echo ""

# Show container status
echo "📊 Container status:"
docker-compose ps
echo ""

# Show scheduler logs
echo "📋 Scheduler logs (last 50 lines):"
docker logs --tail 50 leetcode-scheduler
echo ""

echo "✨ Deployment completed successfully!"
EOF

echo ""
echo "🎉 Deployment finished!"
echo ""
echo "To monitor the scheduler logs, run:"
echo "  ssh ${SERVER_USER}@${SERVER_HOST} 'docker logs -f leetcode-scheduler'"
