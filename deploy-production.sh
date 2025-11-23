#!/bin/bash

# Production Deployment Script for NAS
# This script deploys the LeetCode Team Dashboard to production

set -e  # Exit on error

echo "🚀 LeetCode Team Dashboard - Production Deployment"
echo "=================================================="

# Check if .env.production exists
if [ ! -f .env.production ]; then
    echo "❌ Error: .env.production not found!"
    echo ""
    echo "Please create it from the example:"
    echo "  cp .env.production.example .env.production"
    echo ""
    echo "Then edit .env.production with your actual values:"
    echo "  - AWS credentials"
    echo "  - SECRET_KEY (generate with: python3 -c \"import secrets; print(secrets.token_urlsafe(32))\")"
    echo "  - Verify CORS_ORIGINS and VITE_API_URL"
    exit 1
fi

echo "✅ Found .env.production"

# Verify critical environment variables
echo ""
echo "📋 Checking environment configuration..."

# Source the .env.production file
set -a
source .env.production
set +a

# Check VITE_API_URL
if [[ "$VITE_API_URL" == *"localhost"* ]]; then
    echo "⚠️  WARNING: VITE_API_URL contains 'localhost'"
    echo "   Current value: $VITE_API_URL"
    echo "   Expected: https://api.quangtringuyen.cloud"
    read -p "   Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    echo "✅ VITE_API_URL: $VITE_API_URL"
fi

# Check CORS_ORIGINS
if [[ "$CORS_ORIGINS" == *"quangtringuyen.cloud"* ]]; then
    echo "✅ CORS_ORIGINS includes production domain"
else
    echo "⚠️  WARNING: CORS_ORIGINS might not include production domain"
    echo "   Current value: $CORS_ORIGINS"
fi

# Check SECRET_KEY
if [[ "$SECRET_KEY" == *"your-secret-key"* ]] || [[ "$SECRET_KEY" == *"generate"* ]]; then
    echo "❌ Error: SECRET_KEY not set properly!"
    echo "   Generate one with: python3 -c \"import secrets; print(secrets.token_urlsafe(32))\""
    exit 1
else
    echo "✅ SECRET_KEY is set"
fi

echo ""
read -p "🔨 Ready to build and deploy. Continue? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Deployment cancelled."
    exit 0
fi

# Stop existing containers
echo ""
echo "🛑 Stopping existing containers..."
docker-compose -f docker-compose.fullstack.yml down || true

# Build with production environment
echo ""
echo "🔨 Building containers with production configuration..."
docker-compose -f docker-compose.fullstack.yml --env-file .env.production build --no-cache

# Start services
echo ""
echo "🚀 Starting services..."
docker-compose -f docker-compose.fullstack.yml --env-file .env.production up -d

# Wait for services to be healthy
echo ""
echo "⏳ Waiting for services to be healthy..."
sleep 10

# Check container status
echo ""
echo "📊 Container Status:"
docker-compose -f docker-compose.fullstack.yml ps

# Test API health
echo ""
echo "🏥 Testing API health..."
if command -v curl &> /dev/null; then
    # Try localhost first
    if curl -f http://localhost:8090/api/health &> /dev/null; then
        echo "✅ API is healthy on localhost:8090"
    else
        echo "⚠️  API health check failed on localhost"
    fi
    
    # Try production domain if available
    if curl -f https://api.quangtringuyen.cloud/api/health &> /dev/null; then
        echo "✅ API is accessible at https://api.quangtringuyen.cloud"
    else
        echo "ℹ️  API not yet accessible at production domain (may need reverse proxy setup)"
    fi
else
    echo "ℹ️  curl not available, skipping health check"
fi

echo ""
echo "✅ Deployment complete!"
echo ""
echo "📝 Next steps:"
echo "   1. Ensure reverse proxy (Nginx/Traefik) is configured"
echo "   2. Verify SSL certificates are in place"
echo "   3. Test from external network: https://quangtringuyen.cloud"
echo "   4. Check API: https://api.quangtringuyen.cloud/api/health"
echo ""
echo "📖 For detailed instructions, see: PRODUCTION_DEPLOYMENT.md"
echo ""
echo "📋 View logs with:"
echo "   docker-compose -f docker-compose.fullstack.yml logs -f"
echo ""
