#!/bin/bash
# Rebuild Backend Only
# Run this on your NAS to rebuild the backend container with updated dependencies

set -e

echo "🔨 Rebuilding Backend Container"
echo "================================"
echo ""

# Stop the API container
echo "🛑 Stopping API container..."
docker-compose -f docker-compose.fullstack.yml stop api

# Rebuild backend with no cache
echo ""
echo "🔨 Rebuilding backend (this may take a few minutes)..."
docker-compose -f docker-compose.fullstack.yml build --no-cache api

# Start the API container
echo ""
echo "🚀 Starting API container..."
docker-compose -f docker-compose.fullstack.yml up -d api

# Wait for container to start
echo ""
echo "⏳ Waiting for container to start..."
sleep 5

# Show status
echo ""
echo "📊 Container Status:"
docker-compose -f docker-compose.fullstack.yml ps api

# Show recent logs
echo ""
echo "📋 Recent logs:"
docker-compose -f docker-compose.fullstack.yml logs --tail=20 api

echo ""
echo "✅ Backend rebuild complete!"
echo ""
echo "🧪 Test the API:"
echo "   curl http://localhost:8090/api/health"
echo ""
echo "📋 View live logs:"
echo "   docker-compose -f docker-compose.fullstack.yml logs -f api"
echo ""
