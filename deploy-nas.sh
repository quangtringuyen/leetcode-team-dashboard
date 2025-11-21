#!/bin/bash

# ===========================================
# LeetCode Team Dashboard - NAS Quick Deploy
# ===========================================
# This script automates the deployment process for NAS devices
# Compatible with: Synology, QNAP, TrueNAS, Unraid, and other Docker-enabled NAS

set -e  # Exit on error

echo "🚀 LeetCode Team Dashboard - NAS Deployment Script"
echo "=================================================="
echo ""

# Check if docker is available
if ! command -v docker &> /dev/null; then
    echo "❌ Error: Docker is not installed or not in PATH"
    echo "Please install Docker on your NAS first"
    exit 1
fi

# Check if we're in the right directory
if [ ! -f "docker-compose.backend.yml" ]; then
    echo "❌ Error: docker-compose.backend.yml not found"
    echo "Please run this script from the project root directory"
    exit 1
fi

echo "✅ Docker found"
echo ""

# Step 1: Environment Configuration
echo "📋 Step 1: Setting up environment configuration"
echo "------------------------------------------------"

if [ ! -f ".env" ]; then
    echo "⚠️  No .env file found. Creating from template..."
    cp .env.backend.example .env

    # Generate a random secret key
    SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))" 2>/dev/null || openssl rand -base64 32)

    # Update the .env file with generated secret
    if [ "$(uname)" = "Darwin" ]; then
        # macOS
        sed -i '' "s|SECRET_KEY=.*|SECRET_KEY=${SECRET_KEY}|g" .env
    else
        # Linux
        sed -i "s|SECRET_KEY=.*|SECRET_KEY=${SECRET_KEY}|g" .env
    fi

    echo "✅ Created .env file with generated SECRET_KEY"
    echo ""
    echo "⚠️  IMPORTANT: Please review and update .env file with your settings:"
    echo "   - AWS credentials (if using S3 storage)"
    echo "   - CORS_ORIGINS (if using custom domain)"
    echo ""
    echo "Press Enter to continue after reviewing .env, or Ctrl+C to exit..."
    read -r
else
    echo "✅ .env file already exists"
fi

echo ""

# Step 2: Create data directories
echo "📁 Step 2: Creating data directories"
echo "------------------------------------"
mkdir -p data logs
chmod 755 data logs
echo "✅ Data directories created"
echo ""

# Step 3: Stop existing containers (if any)
echo "🛑 Step 3: Stopping existing containers (if any)"
echo "------------------------------------------------"
docker compose -f docker-compose.backend.yml down 2>/dev/null || true
echo "✅ Cleanup complete"
echo ""

# Step 4: Build Docker images
echo "🔨 Step 4: Building Docker images"
echo "---------------------------------"
echo "This may take a few minutes on first run..."
docker compose -f docker-compose.backend.yml build --no-cache
echo "✅ Build complete"
echo ""

# Step 5: Start services
echo "🚀 Step 5: Starting services"
echo "----------------------------"
docker compose -f docker-compose.backend.yml up -d
echo "✅ Services started"
echo ""

# Step 6: Wait for services to be healthy
echo "⏳ Step 6: Waiting for services to be healthy..."
echo "------------------------------------------------"
sleep 10

# Check container status
echo "Container Status:"
docker compose -f docker-compose.backend.yml ps
echo ""

# Step 7: Health check
echo "🏥 Step 7: Running health check"
echo "-------------------------------"
sleep 5  # Give API a bit more time to start

# Try health check
if command -v curl &> /dev/null; then
    HEALTH_CHECK=$(curl -s http://localhost:8000/api/health || echo "failed")
    if echo "$HEALTH_CHECK" | grep -q "healthy"; then
        echo "✅ API health check passed!"
    else
        echo "⚠️  API health check failed or still starting up"
        echo "Check logs with: docker compose -f docker-compose.backend.yml logs -f api"
    fi
else
    echo "⚠️  curl not found - skipping health check"
    echo "Manually verify: http://localhost:8000/api/health"
fi

echo ""

# Display access information
echo "=================================================="
echo "🎉 Deployment Complete!"
echo "=================================================="
echo ""
echo "📍 Access URLs (replace 'localhost' with your NAS IP):"
echo "   • API Documentation: http://localhost:8000/api/docs"
echo "   • ReDoc:            http://localhost:8000/api/redoc"
echo "   • Health Check:     http://localhost:8000/api/health"
echo ""
echo "🔧 Useful Commands:"
echo "   • View logs:        docker compose -f docker-compose.backend.yml logs -f"
echo "   • Stop services:    docker compose -f docker-compose.backend.yml down"
echo "   • Restart:          docker compose -f docker-compose.backend.yml restart"
echo "   • View status:      docker compose -f docker-compose.backend.yml ps"
echo ""
echo "📖 Next Steps:"
echo "   1. Open http://YOUR-NAS-IP:8000/api/docs in your browser"
echo "   2. Register your first user via /api/auth/register"
echo "   3. Login to get access token"
echo "   4. Start adding team members!"
echo ""
echo "For detailed documentation, see: NAS_DEPLOYMENT_GUIDE.md"
echo "=================================================="
