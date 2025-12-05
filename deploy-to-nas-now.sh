#!/bin/bash
# Deploy latest code to NAS
# This script pulls latest code, rebuilds frontend, and restarts Docker containers

set -e  # Exit on error

echo "🚀 Starting deployment to NAS..."
echo "================================"
echo ""

# Navigate to project directory
cd ~/leetcode-team-dashboard || {
    echo "❌ Error: Project directory not found"
    echo "Looking for: ~/leetcode-team-dashboard"
    exit 1
}

echo "📂 Current directory: $(pwd)"
echo ""

# Pull latest code
echo "📥 Pulling latest code from GitHub..."
git pull origin master

if [ $? -ne 0 ]; then
    echo "❌ Git pull failed!"
    exit 1
fi

echo "✅ Code updated successfully"
echo ""

# Navigate to frontend
cd frontend

# Install dependencies (in case new ones were added)
echo "📦 Installing frontend dependencies..."
npm install

if [ $? -ne 0 ]; then
    echo "⚠️  npm install had warnings, but continuing..."
fi

echo ""

# Build frontend
echo "🔨 Building frontend..."
npm run build

if [ $? -ne 0 ]; then
    echo "❌ Frontend build failed!"
    exit 1
fi

echo "✅ Frontend built successfully"
echo ""

# Go back to project root
cd ..

# Stop containers
echo "🛑 Stopping Docker containers..."
docker-compose -f docker-compose.fullstack.yml down

echo ""

# Rebuild containers (no cache to ensure fresh build)
echo "🔨 Rebuilding Docker containers..."
docker-compose -f docker-compose.fullstack.yml build --no-cache

if [ $? -ne 0 ]; then
    echo "❌ Docker build failed!"
    exit 1
fi

echo ""

# Start containers
echo "🚀 Starting Docker containers..."
docker-compose -f docker-compose.fullstack.yml up -d

if [ $? -ne 0 ]; then
    echo "❌ Failed to start containers!"
    exit 1
fi

echo ""

# Wait for containers to start
echo "⏳ Waiting for containers to start..."
sleep 5

# Show container status
echo ""
echo "📊 Container Status:"
docker-compose -f docker-compose.fullstack.yml ps

echo ""
echo "📋 Recent logs:"
echo "--- Frontend ---"
docker-compose -f docker-compose.fullstack.yml logs --tail=10 frontend 2>/dev/null || echo "Frontend container not found"
echo ""
echo "--- API ---"
docker-compose -f docker-compose.fullstack.yml logs --tail=10 api 2>/dev/null || echo "API container not found"

echo ""
echo "✅ Deployment complete!"
echo ""
echo "🌐 Your application should be available at:"
echo "   Frontend: https://leetcode.quangtringuyen.cloud"
echo "   API: https://api.quangtringuyen.cloud"
echo ""
echo "💡 If you don't see changes, try:"
echo "   - Hard refresh browser: Cmd+Shift+R (Mac) or Ctrl+Shift+R (Windows)"
echo "   - Clear browser cache"
echo ""
