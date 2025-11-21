#!/bin/bash

# ===========================================
# LeetCode Team Dashboard - Full Stack Deploy
# ===========================================
# Deploys React Frontend + FastAPI Backend to NAS

set -e  # Exit on error

echo "🚀 LeetCode Team Dashboard - Full Stack Deployment"
echo "===================================================="
echo ""

# Check if docker is available
if ! command -v docker &> /dev/null; then
    echo "❌ Error: Docker is not installed or not in PATH"
    exit 1
fi

echo "✅ Docker found"
echo ""

# Step 1: Environment Configuration
echo "📋 Step 1: Configuring environment"
echo "-----------------------------------"

if [ ! -f ".env" ]; then
    echo "❌ Error: .env file not found!"
    echo "Please create .env file first. See .env.README.md for details."
    exit 1
fi

# Source .env to check critical settings
set -a
source .env
set +a

if [ -z "$SECRET_KEY" ]; then
    echo "⚠️  WARNING: SECRET_KEY not set in .env!"
    echo "Generating random SECRET_KEY..."
    SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))" 2>/dev/null || openssl rand -base64 32)
    echo "SECRET_KEY=$SECRET_KEY" >> .env
    echo "✅ SECRET_KEY generated and added to .env"
fi

echo "✅ Environment configured"
echo "   - SECRET_KEY: Set"
echo "   - CORS_ORIGINS: $CORS_ORIGINS"
echo "   - Storage: $([ -n "$S3_BUCKET_NAME" ] && echo "S3 ($S3_BUCKET_NAME)" || echo "Local (data/)")"
echo ""

# Step 2: Create data directories
echo "📁 Step 2: Creating data directories"
echo "-------------------------------------"
mkdir -p data logs
chmod 755 data logs
echo "✅ Directories created"
echo ""

# Step 3: Stop existing containers
echo "🛑 Step 3: Stopping existing containers"
echo "----------------------------------------"
docker compose -f docker-compose.fullstack.yml down 2>/dev/null || true
echo "✅ Cleanup complete"
echo ""

# Step 4: Build Docker images
echo "🔨 Step 4: Building Docker images"
echo "----------------------------------"
echo "This may take 5-10 minutes on first run..."
echo ""

# Build backend
echo "Building backend..."
docker compose -f docker-compose.fullstack.yml build --no-cache api
echo "✅ Backend built"
echo ""

# Build frontend
echo "Building frontend..."
docker compose -f docker-compose.fullstack.yml build --no-cache frontend
echo "✅ Frontend built"
echo ""

# Step 5: Start services
echo "🚀 Step 5: Starting services"
echo "----------------------------"
docker compose -f docker-compose.fullstack.yml up -d
echo "✅ Services started"
echo ""

# Step 6: Wait for services
echo "⏳ Step 6: Waiting for services to be healthy..."
echo "-------------------------------------------------"
echo "Waiting for backend to start..."
sleep 15

# Step 7: Health checks
echo "🏥 Step 7: Running health checks"
echo "---------------------------------"

# Check backend
if command -v curl &> /dev/null; then
    echo "Checking backend..."
    for i in {1..10}; do
        HEALTH=$(curl -s http://localhost:8080/api/health 2>/dev/null || echo "")
        if echo "$HEALTH" | grep -q "healthy"; then
            echo "✅ Backend is healthy!"
            echo "   Storage: $(echo $HEALTH | grep -o '"storage":"[^"]*"' | cut -d'"' -f4)"
            break
        fi
        if [ $i -eq 10 ]; then
            echo "⚠️  Backend health check timeout"
            echo "   Check logs: docker compose -f docker-compose.fullstack.yml logs api"
        else
            echo "   Waiting... ($i/10)"
            sleep 3
        fi
    done

    echo ""
    echo "Checking frontend..."
    sleep 5
    FRONTEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000 2>/dev/null || echo "000")
    if [ "$FRONTEND_STATUS" = "200" ] || [ "$FRONTEND_STATUS" = "304" ]; then
        echo "✅ Frontend is accessible!"
    else
        echo "⚠️  Frontend not responding yet"
        echo "   It may still be starting. Check in a minute."
    fi
else
    echo "⚠️  curl not found - skipping health checks"
fi

echo ""

# Display container status
echo "📊 Container Status:"
echo "--------------------"
docker compose -f docker-compose.fullstack.yml ps
echo ""

# Display access information
echo "===================================================="
echo "🎉 Deployment Complete!"
echo "===================================================="
echo ""
echo "📍 Access URLs:"
echo "   • Frontend:     http://localhost:3000"
echo "   • API Docs:     http://localhost:8080/api/docs"
echo "   • Health Check: http://localhost:8080/api/health"
echo ""
echo "🌐 For remote access, replace 'localhost' with your NAS IP"
echo "   Example: http://192.168.1.100:3000"
echo ""
echo "🔧 Useful Commands:"
echo "   • View logs:    docker compose -f docker-compose.fullstack.yml logs -f"
echo "   • Stop:         docker compose -f docker-compose.fullstack.yml down"
echo "   • Restart:      docker compose -f docker-compose.fullstack.yml restart"
echo "   • Status:       docker compose -f docker-compose.fullstack.yml ps"
echo ""
echo "📖 Next Steps:"
echo "   1. Open http://YOUR-NAS-IP:3000 in browser"
echo "   2. Register your first user account"
echo "   3. Login and start using the dashboard!"
echo "   4. Add team members and record snapshots"
echo ""
echo "📚 Documentation:"
echo "   • Quick Start:  QUICK_START.md"
echo "   • Full Guide:   NAS_DEPLOYMENT_COMPLETE.md"
echo "===================================================="
