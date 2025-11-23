#!/bin/bash
# Rebuild Frontend with Production API URL
# Run this script on your NAS after updating .env file

set -e

echo "🔨 Rebuilding Frontend with Production API URL"
echo "=============================================="
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ Error: .env file not found!"
    echo "Please create .env file with VITE_API_URL=https://api.quangtringuyen.cloud"
    exit 1
fi

# Show current VITE_API_URL
echo "📋 Current configuration:"
grep "VITE_API_URL" .env | grep -v "^#" || echo "⚠️  VITE_API_URL not set!"
grep "CORS_ORIGINS" .env | grep -v "^#" | head -1 || echo "⚠️  CORS_ORIGINS not set!"
echo ""

# Confirm
read -p "🚀 Ready to rebuild frontend container. Continue? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelled."
    exit 0
fi

# Stop containers
echo ""
echo "🛑 Stopping containers..."
docker-compose -f docker-compose.fullstack.yml down

# Rebuild frontend with no cache
echo ""
echo "🔨 Rebuilding frontend (this may take a few minutes)..."
docker-compose -f docker-compose.fullstack.yml build --no-cache frontend

# Rebuild backend too (to pick up new CORS settings)
echo ""
echo "🔨 Rebuilding backend (to update CORS settings)..."
docker-compose -f docker-compose.fullstack.yml build --no-cache api

# Start containers
echo ""
echo "🚀 Starting containers..."
docker-compose -f docker-compose.fullstack.yml up -d

# Wait for containers to start
echo ""
echo "⏳ Waiting for containers to start..."
sleep 5

# Show status
echo ""
echo "📊 Container Status:"
docker-compose -f docker-compose.fullstack.yml ps

# Show recent logs
echo ""
echo "📋 Recent logs:"
echo "--- Frontend ---"
docker-compose -f docker-compose.fullstack.yml logs --tail=10 frontend
echo ""
echo "--- API ---"
docker-compose -f docker-compose.fullstack.yml logs --tail=10 api

echo ""
echo "✅ Rebuild complete!"
echo ""
echo "🧪 Test your application:"
echo "   Frontend: https://leetcode.quangtringuyen.cloud"
echo "   API Health: https://api.quangtringuyen.cloud/api/health"
echo ""
echo "🔍 Check browser DevTools → Network tab"
echo "   API calls should go to: https://api.quangtringuyen.cloud"
echo "   NOT localhost:8090"
echo ""
echo "📋 View live logs:"
echo "   docker-compose -f docker-compose.fullstack.yml logs -f"
echo ""
