#!/bin/bash

# ===========================================
# Deploy to NAS - Complete Update Script
# ===========================================

set -e

echo "🚀 Deploying LeetCode Dashboard to NAS with fixes"
echo "=================================================="
echo ""

# Configuration - UPDATE THESE!
NAS_IP="${NAS_IP:-192.168.1.7}"
NAS_USER="${NAS_USER:-admin}"
NAS_PATH="${NAS_PATH:-/volume1/docker/leetcode-team-dashboard}"

echo "Configuration:"
echo "  NAS IP: $NAS_IP"
echo "  NAS User: $NAS_USER"
echo "  NAS Path: $NAS_PATH"
echo ""
echo "Press Enter to continue or Ctrl+C to cancel..."
read -r

# Step 1: Copy updated files to NAS
echo "📤 Step 1: Uploading updated files to NAS..."
echo "--------------------------------------------"

# Copy updated backend files
scp backend/core/security.py ${NAS_USER}@${NAS_IP}:${NAS_PATH}/backend/core/security.py
scp utils/auth.py ${NAS_USER}@${NAS_IP}:${NAS_PATH}/utils/auth.py

# Copy updated .env file
scp .env ${NAS_USER}@${NAS_IP}:${NAS_PATH}/.env

echo "✅ Files uploaded successfully"
echo ""

# Step 2: Rebuild and restart containers
echo "🔄 Step 2: Rebuilding and restarting containers..."
echo "---------------------------------------------------"

ssh ${NAS_USER}@${NAS_IP} << 'ENDSSH'
cd /volume1/docker/leetcode-team-dashboard

echo "Stopping containers..."
docker compose -f docker-compose.backend.yml down

echo "Removing old containers..."
docker compose -f docker-compose.backend.yml rm -f

echo "Building new images (this may take a few minutes)..."
docker compose -f docker-compose.backend.yml build --no-cache

echo "Starting services..."
docker compose -f docker-compose.backend.yml up -d

echo "Waiting for services to start..."
sleep 10

echo ""
echo "Container status:"
docker compose -f docker-compose.backend.yml ps

echo ""
echo "Recent logs:"
docker compose -f docker-compose.backend.yml logs --tail=20 api

ENDSSH

echo ""
echo "✅ Deployment complete!"
echo ""

# Step 3: Verify deployment
echo "🏥 Step 3: Verifying deployment..."
echo "----------------------------------"

sleep 5

echo "Testing health endpoint..."
HEALTH_CHECK=$(curl -s http://${NAS_IP}:8090/api/health || echo "failed")

if echo "$HEALTH_CHECK" | grep -q "healthy"; then
    echo "✅ Health check passed!"
    echo "Response: $HEALTH_CHECK"

    if echo "$HEALTH_CHECK" | grep -q '"storage":"local"'; then
        echo "✅ Using local storage (correct!)"
    else
        echo "⚠️  Warning: Not using local storage"
    fi
else
    echo "❌ Health check failed!"
    echo "Response: $HEALTH_CHECK"
    echo ""
    echo "Check logs with: ssh ${NAS_USER}@${NAS_IP} 'cd ${NAS_PATH} && docker compose -f docker-compose.backend.yml logs -f api'"
fi

echo ""
echo "=================================================="
echo "🎉 Deployment Complete!"
echo "=================================================="
echo ""
echo "Access URLs:"
echo "  • API Docs:     http://${NAS_IP}:8090/api/docs"
echo "  • Health Check: http://${NAS_IP}:8090/api/health"
echo ""
echo "Test authentication:"
echo "  • Register: curl -X POST http://${NAS_IP}:8090/api/auth/register -H 'Content-Type: application/json' -d '{\"username\":\"test\",\"email\":\"test@example.com\",\"password\":\"testpass\"}'"
echo "  • Login:    curl -X POST http://${NAS_IP}:8090/api/auth/login -d 'username=test&password=testpass'"
echo ""
echo "View logs:"
echo "  ssh ${NAS_USER}@${NAS_IP} 'cd ${NAS_PATH} && docker compose -f docker-compose.backend.yml logs -f'"
echo ""
