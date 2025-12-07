#!/bin/bash

# Verification Script for Notification System
# Run this on your server to verify everything is working

set -e

echo "🔍 LeetCode Dashboard - Notification System Verification"
echo "========================================================"
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check 1: Scheduler is running
echo "1️⃣  Checking if scheduler container is running..."
if sudo docker ps | grep -q leetcode-scheduler; then
    echo -e "${GREEN}✅ Scheduler is running${NC}"
    
    # Check restart count
    RESTART_COUNT=$(sudo docker inspect leetcode-scheduler --format='{{.RestartCount}}' 2>/dev/null || echo "unknown")
    if [ "$RESTART_COUNT" = "0" ]; then
        echo -e "${GREEN}✅ No restarts detected (restart count: 0)${NC}"
    else
        echo -e "${YELLOW}⚠️  Warning: Restart count is $RESTART_COUNT${NC}"
    fi
else
    echo -e "${RED}❌ Scheduler is not running!${NC}"
    exit 1
fi
echo ""

# Check 2: Discord webhook configured
echo "2️⃣  Checking Discord webhook configuration..."
DISCORD_URL=$(sudo docker exec leetcode-scheduler printenv DISCORD_WEBHOOK_URL 2>/dev/null || echo "")
if [ -n "$DISCORD_URL" ]; then
    echo -e "${GREEN}✅ Discord webhook is configured${NC}"
    echo "   URL: ${DISCORD_URL:0:30}..."
else
    echo -e "${RED}❌ DISCORD_WEBHOOK_URL is not set!${NC}"
    echo "   Add it to backend/.env and restart the container"
fi
echo ""

# Check 3: Last state file exists
echo "3️⃣  Checking last state file..."
if sudo docker exec leetcode-scheduler test -f /app/data/last_state.json 2>/dev/null; then
    echo -e "${GREEN}✅ Last state file exists${NC}"
    
    # Show a sample of the data
    echo "   Sample data:"
    sudo docker exec leetcode-scheduler cat /app/data/last_state.json 2>/dev/null | head -10 | sed 's/^/   /'
else
    echo -e "${YELLOW}⚠️  Last state file not found (will be created on first run)${NC}"
fi
echo ""

# Check 4: Members file exists
echo "4️⃣  Checking team members configuration..."
if sudo docker exec leetcode-scheduler test -f /app/data/members.json 2>/dev/null; then
    echo -e "${GREEN}✅ Members file exists${NC}"
    
    # Count members
    MEMBER_COUNT=$(sudo docker exec leetcode-scheduler cat /app/data/members.json 2>/dev/null | grep -o '"username"' | wc -l || echo "0")
    echo "   Total members configured: $MEMBER_COUNT"
else
    echo -e "${RED}❌ Members file not found!${NC}"
    echo "   Add team members through the Dashboard"
fi
echo ""

# Check 5: Scheduler logs show it's working
echo "5️⃣  Checking scheduler logs for main loop..."
if sudo docker logs leetcode-scheduler 2>&1 | grep -q "Entering main loop"; then
    echo -e "${GREEN}✅ Scheduler main loop is running${NC}"
    
    # Check for recent heartbeat
    if sudo docker logs leetcode-scheduler --tail 50 2>&1 | grep -q "Heartbeat"; then
        echo -e "${GREEN}✅ Recent heartbeat detected${NC}"
    else
        echo -e "${YELLOW}⚠️  No recent heartbeat (container may have just started)${NC}"
    fi
else
    echo -e "${RED}❌ Main loop not detected in logs!${NC}"
    echo "   The scheduler may not be running properly"
fi
echo ""

# Check 6: Check for recent notification checks
echo "6️⃣  Checking for recent notification activity..."
RECENT_CHECKS=$(sudo docker logs leetcode-scheduler --tail 200 2>&1 | grep -c "Checking for new submissions" || echo "0")
if [ "$RECENT_CHECKS" -gt 0 ]; then
    echo -e "${GREEN}✅ Found $RECENT_CHECKS recent submission checks${NC}"
    
    # Check for any detected changes
    CHANGES=$(sudo docker logs leetcode-scheduler --tail 200 2>&1 | grep -c "Detected change for" || echo "0")
    if [ "$CHANGES" -gt 0 ]; then
        echo -e "${GREEN}✅ Detected $CHANGES submission changes${NC}"
    else
        echo "   No changes detected (no new problems solved recently)"
    fi
    
    # Check for Discord sends
    DISCORD_SENDS=$(sudo docker logs leetcode-scheduler --tail 200 2>&1 | grep -c "Sent Discord notification" || echo "0")
    if [ "$DISCORD_SENDS" -gt 0 ]; then
        echo -e "${GREEN}✅ Sent $DISCORD_SENDS Discord notifications${NC}"
    else
        echo "   No Discord notifications sent yet"
    fi
else
    echo -e "${YELLOW}⚠️  No recent submission checks found${NC}"
    echo "   Scheduler may have just started, or interval hasn't passed yet"
fi
echo ""

# Check 7: Check for errors
echo "7️⃣  Checking for errors in logs..."
ERROR_COUNT=$(sudo docker logs leetcode-scheduler --tail 500 2>&1 | grep -i "error\|exception\|traceback" | grep -v "No error" | wc -l || echo "0")
if [ "$ERROR_COUNT" -eq 0 ]; then
    echo -e "${GREEN}✅ No errors found in recent logs${NC}"
else
    echo -e "${YELLOW}⚠️  Found $ERROR_COUNT error/exception messages${NC}"
    echo "   Recent errors:"
    sudo docker logs leetcode-scheduler --tail 500 2>&1 | grep -i "error\|exception" | grep -v "No error" | tail -5 | sed 's/^/   /'
fi
echo ""

# Summary
echo "========================================================"
echo "📊 VERIFICATION SUMMARY"
echo "========================================================"
echo ""

# Count checks passed
CHECKS_PASSED=0
TOTAL_CHECKS=7

sudo docker ps | grep -q leetcode-scheduler && ((CHECKS_PASSED++)) || true
[ "$RESTART_COUNT" = "0" ] && ((CHECKS_PASSED++)) || true
[ -n "$DISCORD_URL" ] && ((CHECKS_PASSED++)) || true
sudo docker exec leetcode-scheduler test -f /app/data/last_state.json 2>/dev/null && ((CHECKS_PASSED++)) || true
sudo docker exec leetcode-scheduler test -f /app/data/members.json 2>/dev/null && ((CHECKS_PASSED++)) || true
sudo docker logs leetcode-scheduler 2>&1 | grep -q "Entering main loop" && ((CHECKS_PASSED++)) || true
[ "$ERROR_COUNT" -eq 0 ] && ((CHECKS_PASSED++)) || true

echo "Checks passed: $CHECKS_PASSED / $TOTAL_CHECKS"
echo ""

if [ "$CHECKS_PASSED" -eq "$TOTAL_CHECKS" ]; then
    echo -e "${GREEN}✅ All checks passed! Notification system is ready.${NC}"
    echo ""
    echo "🎯 Next steps:"
    echo "   1. Solve a problem on LeetCode with one of your team members"
    echo "   2. Wait 15 minutes for the scheduler to check"
    echo "   3. OR click 'Check for new submissions' on the Dashboard"
    echo "   4. Check your Discord channel for the notification!"
else
    echo -e "${YELLOW}⚠️  Some checks failed. Review the details above.${NC}"
    echo ""
    echo "🔧 Common fixes:"
    echo "   - Add DISCORD_WEBHOOK_URL to backend/.env if missing"
    echo "   - Add team members through the Dashboard"
    echo "   - Check scheduler logs: sudo docker logs leetcode-scheduler --tail 100"
fi

echo ""
echo "========================================================"
echo ""

# Offer to show live logs
read -p "Would you like to watch live scheduler logs? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Watching scheduler logs (Press Ctrl+C to exit)..."
    echo ""
    sudo docker logs -f leetcode-scheduler
fi
