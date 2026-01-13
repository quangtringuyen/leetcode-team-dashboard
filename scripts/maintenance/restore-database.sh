#!/bin/bash

# LeetCode Dashboard Database Restore Script
# Usage: ./restore-database.sh <backup_directory_or_archive>

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

if [ -z "$1" ]; then
    echo -e "${RED}Usage: $0 <backup_directory_or_archive>${NC}"
    echo ""
    echo "Examples:"
    echo "  $0 /volume2/docker/leetcode-dashboard/backups/backup_20251210_221600"
    echo "  $0 /volume2/docker/leetcode-dashboard/backups/backup_20251210_221600.tar.gz"
    echo ""
    echo "Available backups:"
    ls -lht /volume2/docker/leetcode-dashboard/backups/ | head -10
    exit 1
fi

BACKUP_PATH="$1"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}LeetCode Dashboard - Database Restore${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Check if it's an archive
if [[ "$BACKUP_PATH" == *.tar.gz ]]; then
    echo -e "${YELLOW}Extracting archive...${NC}"
    TEMP_DIR="/tmp/leetcode_restore_$$"
    mkdir -p "$TEMP_DIR"
    tar -xzf "$BACKUP_PATH" -C "$TEMP_DIR"
    BACKUP_DIR=$(find "$TEMP_DIR" -type d -name "backup_*" | head -1)
    echo -e "${GREEN}✓ Archive extracted to $BACKUP_DIR${NC}"
else
    BACKUP_DIR="$BACKUP_PATH"
fi

# Verify backup directory
if [ ! -d "$BACKUP_DIR" ]; then
    echo -e "${RED}Error: Backup directory not found: $BACKUP_DIR${NC}"
    exit 1
fi

# Check if database file exists in backup
if [ ! -f "$BACKUP_DIR/leetcode.db" ]; then
    echo -e "${RED}Error: leetcode.db not found in backup directory${NC}"
    exit 1
fi

echo "Backup directory: $BACKUP_DIR"
echo ""
echo "Backup contents:"
ls -lh "$BACKUP_DIR"
echo ""

# Confirm restore
echo -e "${YELLOW}WARNING: This will replace the current database!${NC}"
echo -e "${YELLOW}Current database will be backed up first.${NC}"
echo ""
read -p "Are you sure you want to restore? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "Restore cancelled."
    exit 0
fi

# Backup current database first
echo -e "${YELLOW}Backing up current database...${NC}"
SAFETY_BACKUP="/volume2/docker/leetcode-dashboard/data/leetcode_before_restore_$(date +%Y%m%d_%H%M%S).db"
sudo docker cp leetcode-api:/app/data/leetcode.db "$SAFETY_BACKUP"
echo -e "${GREEN}✓ Current database backed up to: $SAFETY_BACKUP${NC}"

# Stop services
echo -e "${YELLOW}Stopping services...${NC}"
cd /volume2/docker/leetcode-dashboard
sudo docker-compose -f docker-compose.fullstack.yml stop api scheduler
echo -e "${GREEN}✓ Services stopped${NC}"

# Restore database
echo -e "${YELLOW}Restoring database...${NC}"
sudo docker cp "$BACKUP_DIR/leetcode.db" leetcode-api:/app/data/leetcode.db
echo -e "${GREEN}✓ Database restored${NC}"

# Restore JSON files if they exist
if ls "$BACKUP_DIR"/*.json 1> /dev/null 2>&1; then
    echo -e "${YELLOW}Restoring JSON files...${NC}"
    for json_file in "$BACKUP_DIR"/*.json; do
        filename=$(basename "$json_file")
        if [ "$filename" != "data_export.json" ]; then
            sudo docker cp "$json_file" leetcode-api:/app/data/
            echo "  ✓ Restored $filename"
        fi
    done
fi

# Start services
echo -e "${YELLOW}Starting services...${NC}"
sudo docker-compose -f docker-compose.fullstack.yml start api scheduler
sleep 5
echo -e "${GREEN}✓ Services started${NC}"

# Verify restore
echo -e "${YELLOW}Verifying restore...${NC}"
sudo docker exec leetcode-api python3 -c "
from backend.core.database import get_db_connection

with get_db_connection() as conn:
    cursor = conn.cursor()
    
    # Check snapshots
    cursor.execute('SELECT COUNT(*), MIN(week_start), MAX(week_start) FROM snapshots')
    count, min_week, max_week = cursor.fetchone()
    print(f'Snapshots: {count} (from {min_week} to {max_week})')
    
    # Check members
    cursor.execute('SELECT COUNT(*) FROM members')
    print(f'Members: {cursor.fetchone()[0]}')
    
    print('Database restore verified!')
"

# Cleanup temp directory if we extracted an archive
if [[ "$BACKUP_PATH" == *.tar.gz ]]; then
    rm -rf "$TEMP_DIR"
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Restore Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Database has been restored from: $BACKUP_DIR"
echo "Safety backup of previous database: $SAFETY_BACKUP"
echo ""
echo "Services are now running with the restored database."
