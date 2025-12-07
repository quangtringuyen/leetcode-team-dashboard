# Notification Flow Verification Guide

## Code Flow Analysis

### ✅ **Scheduler → Discord Notification Flow**

The notification system is properly wired. Here's the complete flow:

#### 1. **Scheduler Checks for Updates (Every 15 minutes)**

`scheduler.py` → `check_new_submissions()` method (line 54-140):

```
1. Load team members from MEMBERS_FILE
2. Load last known state from LAST_STATE_FILE  
3. Fetch current LeetCode data for each member
4. Compare current_total vs previous_total
5. If current_total > previous_total:
   → Call check_and_notify_new_submissions()
   → Call check_and_notify_milestones()
6. Update LAST_STATE_FILE with new data
```

#### 2. **Create and Send Notification**

`backend/utils/notification_service.py` → `check_and_notify_new_submissions()` (line 366-458):

```
1. Calculate difference: diff = current_total - previous_total
2. If diff > 0:
   a. Fetch recent submissions with difficulty using fetch_submissions_with_tags()
   b. Build notification object with:
      - Title: "🚀 {name} solved {count} new problem(s)!"
      - Message: "{name} just solved {count} problem(s): Problem Name (Difficulty)"
      - Timestamp from actual LeetCode submission
   c. Call notification_service.send_notification(notification, channels=["in_app", "discord"])
```

#### 3. **Send to Discord**

`backend/utils/notification_service.py` → `send_notification()` (line 196-266):

```
1. Check if "discord" in channels (✅ it is)
2. Verify DISCORD_WEBHOOK_URL is set
3. Format Discord embed payload:
   - Username: "LeetCode Dashboard"
   - Avatar: LeetCode logo
   - Embed with title, description, color, timestamp
4. POST to Discord webhook URL
5. Log success or error
6. Save notification to database
```

---

## ✅ **Verification Checklist**

### Code Verification:
- ✅ Scheduler calls `check_and_notify_new_submissions()` when detecting changes (line 114)
- ✅ Function creates notification when diff > 0 (line 391)
- ✅ Notification is sent to **both** "in_app" AND "discord" channels (line 455)
- ✅ Discord webhook POST request is made (line 251)
- ✅ Error logging is in place for debugging (lines 250, 254, 257, 260)

### Required Configuration:
- ✅ `DISCORD_WEBHOOK_URL` must be set in backend/.env
- ✅ `MEMBERS_FILE` must contain team members
- ✅ `LAST_STATE_FILE` must exist (created automatically on first run)

---

## 🧪 **Testing Instructions**

### Test 1: Check Discord Webhook Configuration

On your server:
```bash
# Verify Discord webhook is set
ssh quangtringuyen@192.168.1.7
cd /volume1/docker/leetcode-dashboard
sudo docker exec leetcode-scheduler printenv | grep DISCORD_WEBHOOK_URL

# Expected output:
# DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
```

If empty, add to `backend/.env`:
```
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/YOUR_WEBHOOK_URL
```

### Test 2: Test Discord Webhook Manually

From the frontend Dashboard:
1. Go to **Settings** page
2. Scroll to **Discord Integration** section
3. Click **"Test Discord Notification"** button
4. Check Discord channel for test message

Expected result: 🔔 Test notification appears in Discord

### Test 3: Verify Last State File

Check the last state is being tracked:
```bash
sudo docker exec leetcode-scheduler cat /app/data/last_state.json | jq
```

Expected output:
```json
{
  "your_username": {
    "member_username": {
      "totalSolved": 150,
      "easy": 50,
      "medium": 80,
      "hard": 20
    }
  }
}
```

### Test 4: Manual Submission Check (Frontend)

1. **Solve a LeetCode problem** with one of your team members' accounts
2. Go to **Dashboard** page
3. Click the **refresh icon** (Check for new submissions) in the Notification Center
4. Wait for the spinner to stop

Expected results:
- ✅ Toast appears: "Found 1 new notification!"
- ✅ Notification appears in the Dashboard notification panel
- ✅ Message appears in Discord channel

### Test 5: Automated Scheduler Check

1. **Solve a LeetCode problem** with a team member account
2. **Wait 15 minutes** (default check interval)
3. **Check Discord** for notification
4. **Check scheduler logs**:

```bash
sudo docker logs leetcode-scheduler --tail 100 | grep -A 10 "Checking for new submissions"
```

Expected log output:
```
INFO - Checking for new submissions...
INFO - Fetching data for username...
INFO - Detected change for username: 150 -> 151 (+1)
INFO - Processing 1 new problems for username
INFO - Problem 1: Two Sum (Easy)
INFO - Sending Discord webhook to https://di...
INFO - Sent Discord notification: 🚀 Username solved 1 new problem!
INFO - Submission check completed.
```

---

## 🐛 **Troubleshooting**

### Issue: No Discord notification appears

**Check 1: Webhook URL is set**
```bash
sudo docker exec leetcode-scheduler printenv | grep DISCORD_WEBHOOK_URL
```
If empty → Add to `backend/.env` and restart

** Check 2: Test webhook manually**
- Dashboard → Settings → Test Discord Notification
- If this fails, webhook URL is invalid

**Check 3: Check scheduler logs for errors**
```bash
sudo docker logs leetcode-scheduler --tail 200 | grep -i "discord\|error"
```

Common errors:
- "DISCORD_WEBHOOK_URL not set" → Add to .env
- "Discord API error 404" → Webhook URL is invalid/deleted
- "Failed to send Discord notification: Connection timeout" → Network issue

### Issue: Notification not triggered even after solving problem

**Check 1: Verify state file updated**
```bash
# Before solving problem
sudo docker exec leetcode-scheduler cat /app/data/last_state.json | jq '.your_username.member_username.totalSolved'

# Solve a problem on LeetCode

# After solving, check again
sudo docker exec leetcode-scheduler cat /app/data/last_state.json | jq '.your_username.member_username.totalSolved'
# Should be +1
```

**Check 2: Force a manual check**
- Dashboard → Notification Center → Click refresh icon
- Check browser console and network tab for errors

**Check 3: Verify member is in team**
```bash
sudo docker exec leetcode-scheduler cat /app/data/members.json | jq
```
Your LeetCode username should be in the list

### Issue: Scheduler not running

```bash
# Check if running
sudo docker ps | grep scheduler

# Check restart count (should be 0)
sudo docker inspect leetcode-scheduler --format='{{.RestartCount}}'

# Check logs for errors
sudo docker logs leetcode-scheduler --tail 50
```

If restarting, see FIXES_SUMMARY.md for scheduler fixes

---

## 📊 **Expected Behavior Summary**

### When a team member solves a problem:

**Automated (via Scheduler - every 15 min):**
1. Scheduler detects change in totalSolved count
2. Fetches recent submissions with difficulty
3. Creates notification with problem details
4. Sends to Discord webhook → ✅ Message in Discord
5. Saves to database → ✅ Available in Dashboard
6. Logs success → ✅ Visible in `docker logs`

**Manual (via Dashboard button):**
1. User clicks "Check for new submissions"
2. Backend performs same steps as scheduler
3. Returns notification count to frontend
4. Frontend shows toast → ✅ "Found X new notifications!"
5. Discord receives webhook → ✅ Message in Discord
6. Dashboard updates → ✅ Notification visible

### Discord Message Format:

```
🚀 John Doe solved 1 new problem!
John Doe just solved 1 problem: Two Sum (Easy). Keep it up!
```

For multiple problems:
```
🚀 John Doe solved 3 new problems!
John Doe just solved 3 problems: Two Sum (Easy), Add Two Numbers (Medium), Median of Two Sorted Arrays (Hard). Keep it up!
```

---

## 🔍 **Live Monitoring**

To watch notifications in real-time:

```bash
# Terminal 1: Watch scheduler logs
sudo docker logs -f leetcode-scheduler | grep -E "Checking|Detected|Sending|Sent"

# Terminal 2: Monitor Discord webhooks
sudo docker logs -f leetcode-scheduler | grep -i discord

# Terminal 3: Watch all notification activity
sudo docker logs -f leetcode-scheduler | grep -E "notification|discord|problem|submission"
```

Then solve a problem and watch the logs update!

---

## ✅ **Code Flow Diagram**

```
LeetCode Profile (User solves problem)
           ↓
Scheduler runs (every 15 min) OR User clicks button
           ↓
fetch_user_data() → Get current stats
           ↓
Compare with last_state.json
           ↓
If totalSolved increased:
  ↓
  fetch_submissions_with_tags() → Get problem details
  ↓
  check_and_notify_new_submissions()
    ↓
    create_problem_solved_notification()
    ↓
    send_notification(channels=["in_app", "discord"])
      ↓
      ├─→ Save to database (in_app)
      └─→ POST to Discord webhook URL
           ↓
           Discord Channel receives message! 🎉
```

---

## 📝 **Verification Summary**

✅ **Code Flow**: Complete from scheduler → notification service → Discord  
✅ **Discord Integration**: Webhook POST request implemented  
✅ **Error Handling**: Logging in place for debugging  
✅ **Channels**: Notifications sent to both "in_app" AND "discord"  
✅ **Data Format**: Includes problem name and difficulty  
✅ **Timestamp**: Uses actual LeetCode submission time  

**Conclusion**: The notification system is properly implemented. When a member solves a problem, the notification **WILL** be created and sent to Discord, provided:
1. DISCORD_WEBHOOK_URL is configured
2. Scheduler is running
3. Member is in the team list
4. Last state file exists
