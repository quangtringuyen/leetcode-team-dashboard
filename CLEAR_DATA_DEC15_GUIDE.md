# Clear Data for December 15, 2025 - Quick Guide

## Overview
Scripts to clear snapshot data for December 15, 2025, allowing you to record a fresh snapshot.

**What gets cleared:**
- ✅ Snapshots for December 15, 2025
- ✅ API cache
- ❌ Notifications (PRESERVED - not deleted)

**Safety features:**
- Automatic backup before deletion
- Interactive confirmation
- Detailed summary of changes

---

## Usage

### Option 1: Run on NAS Docker (Recommended)

```bash
# Make script executable (first time only)
chmod +x clear-data-dec15-nas.sh

# Run the script
./clear-data-dec15-nas.sh
```

This script will:
1. Detect if you're on NAS or running remotely via SSH
2. Copy the Python script to the backend container
3. Execute it inside the container with interactive prompts
4. Create a backup in `/volume1/docker/leetcode-team-dashboard/backups/`

### Option 2: Run Locally (Development)

```bash
# Make script executable (first time only)
chmod +x clear-data-dec15.sh

# Run the script
./clear-data-dec15.sh
```

### Option 3: Run Python Script Directly

```bash
# Activate virtual environment (if using one)
source venv/bin/activate

# Run the script
python3 clear_data_dec15.py
```

---

## What the Script Does

### Step-by-Step Process

1. **Create Backup** 📦
   - Backs up `leetcode.db` to `backups/leetcode_before_clear_dec15_TIMESTAMP.db`
   - Ensures you can restore if needed

2. **Check Data** 🔍
   - Counts snapshots for December 15, 2025
   - Shows what will be deleted

3. **List Snapshots** 📋
   - Displays detailed list of all snapshots that will be deleted
   - Shows username, week_start, solved counts, timestamp

4. **Confirmation** ⚠️
   - Asks for explicit confirmation before deletion
   - Type `yes` to proceed, anything else to cancel

5. **Delete Data** 🗑️
   - Deletes snapshots for December 15, 2025
   - Preserves all notifications
   - Clears API cache for fresh data

6. **Summary** 📊
   - Shows counts of deleted items
   - Displays backup location
   - Provides restore instructions

---

## Example Output

```
================================================================================
🗑️  Data Clearing Script for 2024-12-15
================================================================================

📦 Step 1: Creating backup...
✅ Backup created: /path/to/backups/leetcode_before_clear_dec15_20251215_203000.db

🔍 Step 2: Checking data for 2024-12-15...
  - Snapshots to delete: 5
  - Notifications: PRESERVED (not deleted)

📋 Step 3: Listing snapshots...
────────────────────────────────────────────────────────────────────────────────
  ID:    1 | User: alice123           | Week: 2024-12-15 | Solved:  150 (E: 50 M: 80 H: 20) | Time: 2024-12-15 10:30:00
  ID:    2 | User: bob456             | Week: 2024-12-15 | Solved:  200 (E: 70 M:100 H: 30) | Time: 2024-12-15 10:31:00
  ...
────────────────────────────────────────────────────────────────────────────────

⚠️  Step 4: Confirmation
  This will delete:
    - 5 snapshot(s)
    - Notifications: PRESERVED (not deleted)
  Backup saved at: /path/to/backups/leetcode_before_clear_dec15_20251215_203000.db

  Proceed with deletion? (yes/no): yes

🗑️  Step 5: Deleting data...
  ✅ Deleted 5 snapshot(s)
  ℹ️  Notifications preserved (not deleted)

🧹 Step 6: Clearing API cache...
  ✅ Cleared 3 cache entry(ies)

================================================================================
✅ OPERATION COMPLETED SUCCESSFULLY
================================================================================
📊 Summary:
  - Snapshots deleted: 5
  - Notifications: PRESERVED
  - Cache entries cleared: 3
  - Backup location: /path/to/backups/leetcode_before_clear_dec15_20251215_203000.db
================================================================================

💡 You can now record a new snapshot for 2024-12-15
   To restore the backup if needed, run:
   cp /path/to/backups/leetcode_before_clear_dec15_20251215_203000.db /path/to/data/leetcode.db
================================================================================
```

---

## Restoring from Backup

If you need to restore the data:

### On NAS Docker:
```bash
# SSH to NAS
ssh quangtringuyen@192.168.1.7

# Stop containers
cd /volume1/docker/leetcode-team-dashboard
docker-compose down

# Restore backup (replace TIMESTAMP with actual timestamp)
cp backups/leetcode_before_clear_dec15_TIMESTAMP.db data/leetcode.db

# Start containers
docker-compose up -d
```

### Local Development:
```bash
# Replace TIMESTAMP with actual timestamp
cp backups/leetcode_before_clear_dec15_TIMESTAMP.db data/leetcode.db
```

---

## Troubleshooting

### Container Not Running
```bash
# Check container status
docker ps -a | grep leetcode

# Start containers
cd /volume1/docker/leetcode-team-dashboard
docker-compose up -d
```

### Permission Issues
```bash
# Make scripts executable
chmod +x clear-data-dec15.sh clear-data-dec15-nas.sh
```

### SSH Connection Issues
```bash
# Test SSH connection
ssh quangtringuyen@192.168.1.7 "echo 'Connection successful'"
```

### View Backups
```bash
# On NAS
ssh quangtringuyen@192.168.1.7 'ls -lh /volume1/docker/leetcode-team-dashboard/backups/'

# Local
ls -lh backups/
```

---

## Files Created

- **`clear_data_dec15.py`** - Main Python script that performs the data clearing
- **`clear-data-dec15.sh`** - Shell wrapper for local execution
- **`clear-data-dec15-nas.sh`** - Shell wrapper for NAS Docker execution
- **`CLEAR_DATA_DEC15_GUIDE.md`** - This guide

---

## Next Steps After Clearing

1. **Record New Snapshot**
   - Use your normal snapshot recording process
   - The scheduler will automatically create snapshots based on your schedule
   - Or manually trigger a snapshot via the Admin Panel

2. **Verify Data**
   - Check the Dashboard to ensure new data is showing correctly
   - Verify the Week-over-Week table has updated data

3. **Monitor Backups**
   - Backups are stored indefinitely
   - Consider cleaning old backups periodically
   - Keep at least the most recent backup

---

## Safety Notes

✅ **Safe Operations:**
- Automatic backup before any deletion
- Interactive confirmation required
- Detailed logging of all operations
- Notifications are preserved

⚠️ **Important:**
- Always review the snapshot list before confirming deletion
- Keep backups in a safe location
- Test restore process if unsure

---

## Support

If you encounter any issues:
1. Check the backup was created successfully
2. Review the script output for error messages
3. Verify container is running: `docker ps | grep leetcode`
4. Check logs: `docker logs leetcode-team-dashboard-backend-1`
