#!/bin/bash

# Script to clear December 15, 2025 data on NAS Docker deployment
# This script will execute the Python clearing script inside the backend container

set -e

echo "🗑️  Clear Data for Dec 15, 2025 - NAS Docker Deployment"
echo "========================================================"
echo ""

# Check if we're on the NAS or need to SSH
if [ -f "/etc/synoinfo.conf" ]; then
    echo "✅ Running on Synology NAS"
    ON_NAS=true
else
    echo "📡 Running from remote machine - will use SSH"
    ON_NAS=false
    NAS_HOST="quangtringuyen@192.168.1.7"
fi

# Function to run command (either locally on NAS or via SSH)
run_cmd() {
    if [ "$ON_NAS" = true ]; then
        eval "$1"
    else
        ssh "$NAS_HOST" "$1"
    fi
}

# Navigate to project directory
PROJECT_DIR="/volume1/docker/leetcode-team-dashboard"

echo "📂 Project directory: $PROJECT_DIR"
echo ""

# Check if backend container is running
echo "🔍 Checking backend container status..."
CONTAINER_NAME="leetcode-team-dashboard-backend-1"

if run_cmd "docker ps --format '{{.Names}}' | grep -q '$CONTAINER_NAME'"; then
    echo "✅ Backend container is running"
else
    echo "❌ Backend container is not running!"
    echo "   Please start the containers first with:"
    echo "   cd $PROJECT_DIR && docker-compose up -d"
    exit 1
fi

echo ""
echo "📋 This script will:"
echo "   1. Copy the clearing script to the backend container"
echo "   2. Execute it inside the container"
echo "   3. Create a backup before deletion"
echo "   4. Delete snapshots for December 15, 2025"
echo "   5. Clear API cache"
echo "   6. Preserve all notifications"
echo ""
read -p "Continue? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "❌ Operation cancelled"
    exit 0
fi

echo ""
echo "🚀 Executing data clearing script..."
echo ""

# Copy the Python script to the container
echo "📤 Copying script to container..."
if [ "$ON_NAS" = true ]; then
    docker cp "$PROJECT_DIR/clear_data_dec15.py" "$CONTAINER_NAME:/app/clear_data_dec15.py"
else
    # First copy to NAS, then to container
    scp "$PWD/clear_data_dec15.py" "$NAS_HOST:$PROJECT_DIR/"
    ssh "$NAS_HOST" "docker cp $PROJECT_DIR/clear_data_dec15.py $CONTAINER_NAME:/app/clear_data_dec15.py"
fi

echo "✅ Script copied to container"
echo ""

# Execute the script inside the container
echo "▶️  Running clearing script inside container..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if [ "$ON_NAS" = true ]; then
    docker exec -it "$CONTAINER_NAME" python3 /app/clear_data_dec15.py
else
    ssh -t "$NAS_HOST" "docker exec -it $CONTAINER_NAME python3 /app/clear_data_dec15.py"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "✅ Script execution completed!"
echo ""
echo "💡 Next steps:"
echo "   1. You can now record a new snapshot for December 15, 2025"
echo "   2. The backup is stored in: $PROJECT_DIR/backups/"
echo "   3. To view backups, run:"
if [ "$ON_NAS" = true ]; then
    echo "      ls -lh $PROJECT_DIR/backups/"
else
    echo "      ssh $NAS_HOST 'ls -lh $PROJECT_DIR/backups/'"
fi
echo ""
