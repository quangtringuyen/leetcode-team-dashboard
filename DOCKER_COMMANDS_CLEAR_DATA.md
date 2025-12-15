# Docker Commands to Clear Data for Dec 15, 2025

## Quick Commands (Copy & Paste on NAS)

### Step 1: Copy script to container
```bash
cd /volume1/docker/leetcode-team-dashboard
docker cp clear_data_dec15.py leetcode-team-dashboard-backend-1:/app/clear_data_dec15.py
```

### Step 2: Run the clearing script
```bash
docker exec -it leetcode-team-dashboard-backend-1 python3 /app/clear_data_dec15.py
```

That's it! The script will:
- ✅ Create a backup automatically
- ✅ Show you what will be deleted
- ✅ Ask for confirmation before deleting
- ✅ Delete snapshots for Dec 15, 2025
- ✅ Preserve all notifications
- ✅ Clear API cache

---

## Alternative: One-liner (if you want to skip file copy)

```bash
docker exec -it leetcode-team-dashboard-backend-1 python3 -c "
import sqlite3
import os
from datetime import datetime
from shutil import copy2

# Paths
db_path = '/app/data/leetcode.db'
backup_dir = '/app/backups'
os.makedirs(backup_dir, exist_ok=True)

# Backup
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
backup_path = f'{backup_dir}/leetcode_before_clear_dec15_{timestamp}.db'
copy2(db_path, backup_path)
print(f'✅ Backup created: {backup_path}')

# Delete snapshots
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute('DELETE FROM snapshots WHERE week_start = ? OR DATE(timestamp) = ?', ('2024-12-15', '2024-12-15'))
deleted = cursor.rowcount
cursor.execute('DELETE FROM api_cache')
cache_deleted = cursor.rowcount
conn.commit()
conn.close()

print(f'✅ Deleted {deleted} snapshot(s)')
print(f'✅ Cleared {cache_deleted} cache entries')
print(f'✅ Notifications preserved')
print(f'📦 Backup: {backup_path}')
"
```

---

## View Backups

```bash
ls -lh /volume1/docker/leetcode-team-dashboard/backups/
```

## Restore from Backup (if needed)

```bash
# Stop containers
cd /volume1/docker/leetcode-team-dashboard
docker-compose down

# Restore (replace TIMESTAMP with actual timestamp)
cp backups/leetcode_before_clear_dec15_TIMESTAMP.db data/leetcode.db

# Start containers
docker-compose up -d
```
