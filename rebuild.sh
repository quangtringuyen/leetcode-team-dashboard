#!/bin/bash

# Quick rebuild script after fixing scheduler and CORS issues

set -e

echo "🔧 Rebuilding LeetCode Team Dashboard..."
echo ""

# Check if docker command exists
if ! command -v docker &> /dev/null; then
    echo "❌ Docker command not found in PATH"
    echo ""
    echo "Options:"
    echo "  1. Use Docker Desktop GUI (Containers → Delete old → Rebuild)"
    echo "  2. Add Docker to PATH:"
    echo "     export PATH=\"/usr/local/bin:\$PATH\""
    echo "     source ~/.zshrc"
    echo ""
    exit 1
fi

echo "✅ Docker found"
echo ""

# Stop and remove old containers
echo "🛑 Stopping old containers..."
docker compose -f docker-compose.backend.yml down || true
echo ""

# Rebuild with no cache
echo "🔨 Rebuilding images (this may take a minute)..."
docker compose -f docker-compose.backend.yml build --no-cache
echo ""

# Start services
echo "🚀 Starting services..."
docker compose -f docker-compose.backend.yml up -d
echo ""

# Wait a moment
echo "⏳ Waiting for services to start..."
sleep 5
echo ""

# Check status
echo "📊 Container Status:"
docker compose -f docker-compose.backend.yml ps
echo ""

# Health check
echo "🏥 Health Check:"
sleep 3
curl -s http://localhost:8080/api/health | python3 -m json.tool 2>/dev/null || echo "Waiting for API to be ready..."
echo ""

echo "=================================================="
echo "✅ Rebuild Complete!"
echo "=================================================="
echo ""
echo "Access your API:"
echo "  • Swagger UI:  http://localhost:8080/api/docs"
echo "  • ReDoc:       http://localhost:8080/api/redoc"
echo "  • Health:      http://localhost:8080/api/health"
echo ""
echo "View logs:"
echo "  docker compose -f docker-compose.backend.yml logs -f"
echo ""
echo "Happy coding! 🚀"
