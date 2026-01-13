# 🚀 Quick Start Guide

## Backend is Already Running! ✅

Your FastAPI backend is currently running at: **http://localhost:8080**

Test it: http://localhost:8080/api/docs (Swagger UI)

---

## Start the Frontend

Open a **new terminal window** and run:

```bash
cd /Users/tringuyen/dev/code/leetcode-team-dashboard/frontend
npm run dev
```

Then open your browser to: **http://localhost:5173**

---

## What to Test

### 1. Register a New Account
- Click "Sign up" on the login page
- Fill in username, email, and password
- You'll be redirected to login

### 2. Login
- Enter your credentials
- You'll see the dashboard

### 3. Add Team Members
- Go to "Team" page (in the sidebar or top nav)
- Click "Add Member" button
- Enter:
  - **LeetCode Username**: e.g., "kamyu104" (a real LeetCode user)
  - **Display Name**: e.g., "Test User"
- Click "Add Member"

### 4. Record a Snapshot
- Go back to "Dashboard"
- Click "Record Snapshot" button
- Wait a few seconds (it fetches live data from LeetCode)
- You'll see member stats update

### 5. View Analytics
- Go to "Analytics" page
- See trend charts
- View week-over-week changes
- Check difficulty distribution

---

## API Endpoints

Your backend has these endpoints working:

**Auth:**
- POST `/api/auth/login` - Login
- POST `/api/auth/register` - Register
- GET `/api/auth/me` - Get current user

**Team:**
- GET `/api/team/members` - List members
- POST `/api/team/members` - Add member
- DELETE `/api/team/members/{username}` - Remove member
- GET `/api/team/stats` - Team statistics

**Analytics:**
- GET `/api/analytics/history` - Weekly snapshots
- POST `/api/analytics/snapshot` - Record new snapshot
- GET `/api/analytics/trends?weeks=12` - Trend data
- GET `/api/analytics/week-over-week` - Weekly changes

**LeetCode:**
- GET `/api/leetcode/user/{username}` - User stats
- GET `/api/leetcode/user/{username}/recent` - Recent submissions
- GET `/api/leetcode/daily-challenge` - Today's challenge

---

## Summary

✅ Backend running on :8080
✅ Frontend ready to start on :5173
✅ All 13 API endpoints working
✅ LeetCode data fetching working
✅ Complete documentation available

**Just start the frontend and you're good to go!** 🎉
