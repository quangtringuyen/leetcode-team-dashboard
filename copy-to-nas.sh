#!/bin/bash
# Copy updated frontend files to NAS and rebuild

set -e

echo "📦 Copying Updated Frontend Files to NAS"
echo "========================================"
echo ""

# Configuration
NAS_USER="quangtringuyen"
NAS_HOST="192.168.1.7"
NAS_PATH="/volume1/docker/leetcode-team-dashboard"  # Update this path!

echo "Target: $NAS_USER@$NAS_HOST:$NAS_PATH"
echo ""

# Confirm
read -p "Is the NAS path correct? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Please update NAS_PATH in this script with the correct path."
    exit 1
fi

echo "📤 Copying files..."

# Copy updated authentication files
echo "  → authStore.ts (session persistence fix)"
scp frontend/src/stores/authStore.ts "$NAS_USER@$NAS_HOST:$NAS_PATH/frontend/src/stores/"

echo "  → App.tsx (protected route fix)"
scp frontend/src/App.tsx "$NAS_USER@$NAS_HOST:$NAS_PATH/frontend/src/"

echo "  → Analytics.tsx (undefined property fix)"
scp frontend/src/pages/Analytics.tsx "$NAS_USER@$NAS_HOST:$NAS_PATH/frontend/src/pages/"

echo "✅ Files copied successfully!"
echo ""
echo "🔨 Now rebuild the frontend on NAS:"
echo ""
echo "ssh $NAS_USER@$NAS_HOST"
echo "cd $NAS_PATH"
echo "docker-compose -f docker-compose.fullstack.yml down"
echo "docker-compose -f docker-compose.fullstack.yml build --no-cache frontend"
echo "docker-compose -f docker-compose.fullstack.yml up -d"
echo ""
echo "Or run the rebuild script:"
echo "./rebuild-frontend-nas.sh"
echo ""
