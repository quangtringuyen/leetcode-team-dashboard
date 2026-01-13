#!/bin/bash
# Resolve git conflicts on NAS and deploy latest code

set -e

echo "🔧 Resolving Git Conflicts on NAS..."
echo "===================================="
echo ""

cd ~/leetcode-team-dashboard || exit 1

echo "📍 Current directory: $(pwd)"
echo ""

# Check git status
echo "📊 Checking git status..."
git status

echo ""
echo "🔄 Stashing any local changes..."
git stash

echo ""
echo "📥 Pulling latest code from master..."
git pull origin master

echo ""
echo "✅ Conflicts resolved! Proceeding with deployment..."
echo ""

# Navigate to frontend
cd frontend

echo "📦 Installing dependencies..."
npm install

echo ""
echo "🔨 Building frontend..."
npm run build

echo ""
echo "✅ Frontend built successfully"
echo ""

# Go back to root
cd ..

echo "🛑 Stopping Docker containers..."
docker-compose -f docker-compose.fullstack.yml down

echo ""
echo "🔨 Rebuilding Docker containers..."
docker-compose -f docker-compose.fullstack.yml build --no-cache

echo ""
echo "🚀 Starting Docker containers..."
docker-compose -f docker-compose.fullstack.yml up -d

echo ""
echo "⏳ Waiting for containers to start..."
sleep 5

echo ""
echo "📊 Container Status:"
docker-compose -f docker-compose.fullstack.yml ps

echo ""
echo "✅ Deployment Complete!"
echo ""
echo "🌐 Your application should be available at:"
echo "   https://leetcode.quangtringuyen.cloud"
echo ""
