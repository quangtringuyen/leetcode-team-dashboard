# Week-over-Week Logic & Timezone Issues - Analysis & Fixes

## Issues Identified

### 1. **Week-over-Week Logic is CORRECT** ✅
The current implementation in `/backend/api/analytics.py` (lines 283-416) is tracking **total accepted problems** (`totalSolved`), NOT daily challenges. 

**Current Logic:**
```python
total = snapshot.get("totalSolved", 0)  # Line 315
```

This is the cumulative count of ALL accepted problems, which is what you want.

**The "missing problems" issue is likely caused by:**
- Snapshots not being recorded at the right time due to timezone mismatch
- LeetCode's counter updates at UTC 00:00, but your scheduler runs at GMT+7 00:00

---

### 2. **CRITICAL: Timezone Mismatch** ⚠️

**Problem:**
- LeetCode resets daily challenges and updates counters at **UTC 00:00** (midnight)
- Your scheduler is set to run at **00:00 in your local time (GMT+7)**
- This means you're running the snapshot **7 hours BEFORE** LeetCode's day changes!

**Example:**
- Your time: Monday 00:00 GMT+7 = Sunday 17:00 UTC
- LeetCode's Monday starts at: Monday 00:00 UTC = Monday 07:00 GMT+7

**Impact:**
When you take a snapshot at Monday 00:00 GMT+7:
- It's still Sunday 17:00 UTC on LeetCode
- Any problems solved between Sunday 17:00 UTC and Monday 00:00 UTC (7 hours) will be **missed** in your Monday snapshot
- They'll appear in the NEXT week's snapshot instead

---

## Solutions

### Option 1: Adjust Scheduler Time (Recommended)
Run the snapshot at **07:00 GMT+7** (which is 00:00 UTC) to align with LeetCode's day change.

### Option 2: Use UTC Timezone in Scheduler
Configure the scheduler to use UTC timezone instead of local time.

### Option 3: Run Snapshot Later in the Day
Run at a time well after LeetCode's day change, e.g., **12:00 GMT+7** (05:00 UTC), giving a 5-hour buffer.

---

## Recommended Fix

**Change the default snapshot time from 00:00 to 07:30 GMT+7**

This ensures:
- LeetCode's day has changed (00:00 UTC = 07:00 GMT+7)
- 30-minute buffer for any delays
- All problems solved on Sunday (up to midnight UTC) are captured in Sunday's snapshot

---

## Implementation

### File: `backend/core/database.py`
Change the default snapshot time from `00:00` to `07:30`:

```python
cursor.execute("INSERT OR IGNORE INTO system_settings (key, value) VALUES ('snapshot_schedule_time', '\"07:30\"')")
```

### File: `scheduler.py`
The scheduler already reads this setting from the database, so no code changes needed!

---

## Verification Steps

1. **Check current setting:**
   ```sql
   SELECT * FROM system_settings WHERE key = 'snapshot_schedule_time';
   ```

2. **Update setting:**
   ```sql
   UPDATE system_settings SET value = '"07:30"' WHERE key = 'snapshot_schedule_time';
   ```

3. **Restart scheduler container:**
   ```bash
   docker-compose restart scheduler
   ```

4. **Verify in logs:**
   ```bash
   docker logs leetcode-api | grep "Snapshot: Every"
   ```

---

## Additional Notes

### LeetCode's Timezone Behavior
- **Daily Challenge**: Resets at 00:00 UTC (07:00 GMT+7)
- **User Stats**: Updates immediately when problems are solved
- **Weekly Contest**: Starts at Saturday 22:30 UTC (Sunday 05:30 GMT+7)

### Your Current Schedule
- **Snapshot**: Monday 00:00 GMT+7 (Sunday 17:00 UTC) ❌ TOO EARLY
- **Notifications**: Every 15 minutes ✅
- **Daily Challenge Notification**: 08:00 GMT+7 (01:00 UTC) ✅

### Recommended Schedule
- **Snapshot**: Monday 07:30 GMT+7 (Monday 00:30 UTC) ✅ AFTER LEETCODE RESET
- **Notifications**: Every 15 minutes ✅
- **Daily Challenge Notification**: 08:00 GMT+7 (01:00 UTC) ✅

---

## Testing the Fix

### Before Fix:
Problems solved on Sunday between 17:00-23:59 UTC are missed

### After Fix:
All problems solved on Sunday (00:00-23:59 UTC) are captured in Sunday's snapshot

### Test Case:
1. Note current `totalSolved` for a member
2. Have them solve a problem on Sunday at 23:00 UTC (Monday 06:00 GMT+7)
3. Wait for Monday 07:30 GMT+7 snapshot
4. Verify the problem is included in the snapshot

---

## Summary

| Issue | Status | Fix |
|-------|--------|-----|
| Week-over-Week tracks daily challenges instead of total problems | ❌ FALSE | No fix needed - logic is correct |
| Missing problems due to timezone mismatch | ✅ CONFIRMED | Change snapshot time to 07:30 GMT+7 |
| Scheduler uses local time instead of UTC | ⚠️ ISSUE | Update default setting in database |

**Action Required:**
1. Update `snapshot_schedule_time` setting to `07:30`
2. Restart scheduler container
3. Monitor next snapshot to verify all problems are captured
sudo docker ps -a