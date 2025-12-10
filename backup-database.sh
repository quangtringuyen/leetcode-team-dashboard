#!/bin/bash

# LeetCode Dashboard Database Backup Script
# Run this script to create a complete backup of your database

set -e

# Configuration
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_BASE="/volume2/docker/leetcode-dashboard/backups"
BACKUP_DIR="$BACKUP_BASE/backup_$TIMESTAMP"
DATA_DIR="/volume2/docker/leetcode-dashboard/data"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}LeetCode Dashboard - Database Backup${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Create backup directory
echo -e "${YELLOW}Creating backup directory...${NC}"
mkdir -p "$BACKUP_DIR"

# 1. Backup SQLite database file
echo -e "${YELLOW}Backing up database file...${NC}"
if sudo docker exec leetcode-api test -f /app/data/leetcode.db; then
    # Use Python to create a safe backup
    sudo docker exec leetcode-api python3 -c "
import sqlite3
import shutil
src = '/app/data/leetcode.db'
dst = '/app/data/temp_backup.db'
# Use backup API for safe copy
src_conn = sqlite3.connect(src)
dst_conn = sqlite3.connect(dst)
src_conn.backup(dst_conn)
src_conn.close()
dst_conn.close()
print('Backup created')
"
    sudo docker cp leetcode-api:/app/data/temp_backup.db "$BACKUP_DIR/leetcode.db"
    sudo docker exec leetcode-api rm /app/data/temp_backup.db
    echo -e "${GREEN}✓ Database file backed up${NC}"
else
    echo -e "${RED}✗ Database file not found!${NC}"
    exit 1
fi

# 2. Export to SQL dump
echo -e "${YELLOW}Creating SQL dump...${NC}"
sudo docker exec leetcode-api python3 -c "
import sqlite3
conn = sqlite3.connect('/app/data/leetcode.db')
with open('/app/data/dump.sql', 'w') as f:
    for line in conn.iterdump():
        f.write(f'{line}\n')
conn.close()
print('SQL dump created')
"
sudo docker cp leetcode-api:/app/data/dump.sql "$BACKUP_DIR/leetcode_dump.sql"
sudo docker exec leetcode-api rm /app/data/dump.sql
echo -e "${GREEN}✓ SQL dump created${NC}"

# 3. Export to JSON (for easy inspection)
echo -e "${YELLOW}Exporting data to JSON...${NC}"
sudo docker exec leetcode-api python3 -c "
import sqlite3
import json
from pathlib import Path

conn = sqlite3.connect('/app/data/leetcode.db')
conn.row_factory = sqlite3.Row

# Export each table
tables = ['snapshots', 'members', 'notifications', 'api_cache', 'system_settings']
exports = {}

for table in tables:
    try:
        cursor = conn.cursor()
        cursor.execute(f'SELECT * FROM {table}')
        rows = cursor.fetchall()
        exports[table] = [dict(row) for row in rows]
        print(f'{table}: {len(rows)} rows')
    except Exception as e:
        print(f'Error exporting {table}: {e}')

# Save to file
with open('/app/data/export.json', 'w') as f:
    json.dump(exports, f, indent=2, default=str)

conn.close()
print('Export complete!')
" > "$BACKUP_DIR/export_log.txt"

sudo docker cp leetcode-api:/app/data/export.json "$BACKUP_DIR/data_export.json"
sudo docker exec leetcode-api rm /app/data/export.json
echo -e "${GREEN}✓ JSON export created${NC}"

# 4. Backup JSON config files
echo -e "${YELLOW}Backing up config files...${NC}"
cp "$DATA_DIR"/*.json "$BACKUP_DIR/" 2>/dev/null || echo "No JSON files to backup"

# 5. Get database statistics
echo -e "${YELLOW}Generating statistics...${NC}"
sudo docker exec leetcode-api python3 -c "
from backend.core.database import get_db_connection

with get_db_connection() as conn:
    cursor = conn.cursor()
    
    print('Database Statistics:')
    print('=' * 50)
    
    # Snapshots
    cursor.execute('SELECT COUNT(*), MIN(week_start), MAX(week_start) FROM snapshots')
    count, min_week, max_week = cursor.fetchone()
    print(f'Snapshots: {count} (from {min_week} to {max_week})')
    
    # Members
    cursor.execute('SELECT COUNT(*) FROM members')
    print(f'Members: {cursor.fetchone()[0]}')
    
    # Notifications
    cursor.execute('SELECT COUNT(*) FROM notifications')
    print(f'Notifications: {cursor.fetchone()[0]}')
    
    # Cache
    cursor.execute('SELECT COUNT(*) FROM api_cache')
    print(f'Cache entries: {cursor.fetchone()[0]}')
    
    # Database size
    cursor.execute('SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size()')
    size_bytes = cursor.fetchone()[0]
    size_mb = size_bytes / (1024 * 1024)
    print(f'Database size: {size_mb:.2f} MB')
" > "$BACKUP_DIR/statistics.txt"

cat "$BACKUP_DIR/statistics.txt"

# 6. Create compressed archive
echo -e "${YELLOW}Creating compressed archive...${NC}"
cd "$BACKUP_BASE"
tar -czf "backup_$TIMESTAMP.tar.gz" "backup_$TIMESTAMP"
ARCHIVE_SIZE=$(du -h "backup_$TIMESTAMP.tar.gz" | cut -f1)
echo -e "${GREEN}✓ Archive created: backup_$TIMESTAMP.tar.gz ($ARCHIVE_SIZE)${NC}"

# 7. Cleanup old backups (keep last 10)
echo -e "${YELLOW}Cleaning up old backups...${NC}"
cd "$BACKUP_BASE"
ls -t backup_*.tar.gz | tail -n +11 | xargs -r rm
echo -e "${GREEN}✓ Kept last 10 backups${NC}"

# Summary
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Backup Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Backup location: $BACKUP_DIR"
echo "Archive: $BACKUP_BASE/backup_$TIMESTAMP.tar.gz"
echo "Archive size: $ARCHIVE_SIZE"
echo ""
echo "Files backed up:"
ls -lh "$BACKUP_DIR"
echo ""
echo -e "${YELLOW}To restore from this backup:${NC}"
echo "  sudo docker cp $BACKUP_DIR/leetcode.db leetcode-api:/app/data/leetcode.db"
echo "  sudo docker-compose -f docker-compose.fullstack.yml restart api scheduler"
