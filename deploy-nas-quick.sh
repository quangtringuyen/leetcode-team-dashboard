#!/bin/bash
# Quick deployment script for NAS
# Run this ON THE NAS via SSH

set -e

echo "🚀 Deploying latest fixes to NAS..."

# Navigate to project directory
cd ~/code/leetcode-team-dashboard || cd ~/leetcode-team-dashboard || {
    echo "❌ Project directory not found. Please update the path in this script."
    exit 1
}

echo "📂 Current directory: $(pwd)"

# Pull latest code
echo "📥 Pulling latest code from GitHub..."
git pull origin master

# Rebuild and restart
echo "🔨 Rebuilding containers..."
sudo docker compose -f docker-compose.fullstack.yml build --no-cache

echo "🔄 Restarting services..."
sudo docker compose -f docker-compose.fullstack.yml up -d

echo "⏳ Waiting for services to start..."
sleep 10

echo "✅ Deployment complete!"
echo ""
echo "🧪 Testing endpoints..."
echo "Backend health: $(curl -s http://localhost:8090/api/health | grep -o 'healthy' || echo 'NOT READY')"
echo ""
echo "📋 Container status:"
sudo docker compose -f docker-compose.fullstack.yml ps
