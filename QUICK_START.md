# ⚡ Quick Start Guide - 60 Seconds to Live

Get your LeetCode Team Dashboard API running in under 60 seconds.

---

## 🎯 One-Command Deployment

```bash
./deploy-nas.sh
```

**That's it!** The script handles everything automatically.

---

## 📍 What Happens

The deployment script will:

1. ✅ Check Docker installation
2. ✅ Create `.env` file with secure SECRET_KEY
3. ✅ Create data directories
4. ✅ Build Docker images (~1-2 minutes)
5. ✅ Start API and scheduler services
6. ✅ Run health checks
7. ✅ Display access URLs

---

## 🌐 Access Your API

After deployment completes, open your browser:

```
http://localhost:8000/api/docs
```

Or if on NAS, replace `localhost` with your NAS IP:

```
http://192.168.1.100:8000/api/docs
```

---

## ✅ Verify It's Working

### 1. Quick Health Check

```bash
curl http://localhost:8000/api/health
```

**Expected:**
```json
{
  "status": "healthy",
  "service": "LeetCode Team Dashboard API",
  "version": "2.0.0"
}
```

### 2. Check Containers

```bash
docker compose -f docker-compose.backend.yml ps
```

**Expected:**
```
NAME                  STATUS              PORTS
leetcode-api         Up (healthy)        0.0.0.0:8000->8000/tcp
leetcode-scheduler   Up (healthy)
```

### 3. View Logs

```bash
docker compose -f docker-compose.backend.yml logs -f
```

You should see:
- API server starting on port 8000
- No error messages
- Scheduler running

---

## 🎨 First Steps with API

### 1. Register Your User

Open: http://localhost:8000/api/docs

Find: `POST /api/auth/register`

Click: **Try it out**

Fill in:
```json
{
  "username": "yourname",
  "email": "your@email.com",
  "password": "yourpassword"
}
```

Click: **Execute**

### 2. Login (Get Token)

Find: `POST /api/auth/login`

Fill in:
```
username: yourname
password: yourpassword
```

Click: **Execute**

**Copy the `access_token`** from the response

### 3. Authorize API

Click: **Authorize** button (top right)

Enter: `Bearer <your-access-token>`

Click: **Authorize**

Now you can use all endpoints!

### 4. Add Team Member

Find: `POST /api/team/members`

Fill in:
```json
{
  "username": "leetcode_username",
  "name": "Team Member Name"
}
```

Click: **Execute**

### 5. View Team

Find: `GET /api/team/members`

Click: **Execute**

You'll see all team members with their LeetCode stats!

---

## 📊 Using the API

### From Command Line

```bash
# 1. Register
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"myuser","email":"user@example.com","password":"pass123"}'

# 2. Login (save token)
TOKEN=$(curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=myuser&password=pass123" | jq -r '.access_token')

# 3. Add member
curl -X POST http://localhost:8000/api/team/members \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"username":"leetcode_user","name":"John Doe"}'

# 4. Get team
curl -X GET http://localhost:8000/api/team/members \
  -H "Authorization: Bearer $TOKEN"
```

### From JavaScript/Frontend

```javascript
// 1. Register
const response = await fetch('http://localhost:8000/api/auth/register', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    username: 'myuser',
    email: 'user@example.com',
    password: 'pass123'
  })
});

// 2. Login
const loginResponse = await fetch('http://localhost:8000/api/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  body: 'username=myuser&password=pass123'
});
const { access_token } = await loginResponse.json();

// 3. Add member
await fetch('http://localhost:8000/api/team/members', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${access_token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    username: 'leetcode_user',
    name: 'John Doe'
  })
});

// 4. Get team
const teamResponse = await fetch('http://localhost:8000/api/team/members', {
  headers: { 'Authorization': `Bearer ${access_token}` }
});
const team = await teamResponse.json();
console.log(team);
```

---

## 🔧 Common Commands

### Service Management

```bash
# Start
docker compose -f docker-compose.backend.yml up -d

# Stop
docker compose -f docker-compose.backend.yml down

# Restart
docker compose -f docker-compose.backend.yml restart

# Status
docker compose -f docker-compose.backend.yml ps

# Logs
docker compose -f docker-compose.backend.yml logs -f
```

### Maintenance

```bash
# Update code
git pull

# Rebuild
docker compose -f docker-compose.backend.yml build --no-cache

# Restart with new code
docker compose -f docker-compose.backend.yml up -d

# Backup data
tar -czf backup-$(date +%Y%m%d).tar.gz data/
```

---

## 🐛 Troubleshooting

### Can't access API

**Problem:** Browser can't connect to API

**Solution:**
```bash
# 1. Check if containers are running
docker compose -f docker-compose.backend.yml ps

# 2. Check if port is accessible
curl http://localhost:8000/api/health

# 3. If on NAS, use NAS IP instead of localhost
curl http://YOUR-NAS-IP:8000/api/health

# 4. Check firewall allows port 8000
```

### Service won't start

**Problem:** Docker containers failing

**Solution:**
```bash
# 1. Check logs for errors
docker compose -f docker-compose.backend.yml logs api

# 2. Ensure .env file exists
ls -la .env

# 3. Check port 8000 is free
lsof -i :8000

# 4. Try rebuilding
docker compose -f docker-compose.backend.yml down
docker compose -f docker-compose.backend.yml build --no-cache
docker compose -f docker-compose.backend.yml up -d
```

### "Failed to fetch user data"

**Problem:** Can't get LeetCode data

**Solution:**
```bash
# 1. Check LeetCode connectivity from container
docker exec leetcode-api curl -I https://leetcode.com

# 2. Check logs for specific errors
docker compose -f docker-compose.backend.yml logs -f api

# 3. Verify username exists on LeetCode
# Visit: https://leetcode.com/USERNAME
```

---

## 📚 Next Steps

**Explored the basics?** Check out:

- **[README.md](README.md)** - Full feature documentation
- **[README.Docker.md](README.Docker.md)** - Advanced Docker setup
- **[NAS_DEPLOYMENT_GUIDE.md](NAS_DEPLOYMENT_GUIDE.md)** - NAS-specific guides
- **[DEPLOYMENT_SUMMARY.md](DEPLOYMENT_SUMMARY.md)** - All deployment options

**Want to build a frontend?**
- API is CORS-ready for `localhost:3000`
- Use any framework (React, Vue, Flutter, etc.)
- Full API docs at `/api/docs`

**Ready for production?**
- Generate new SECRET_KEY
- Enable HTTPS
- Configure firewall
- Set up automated backups

---

## ✅ Success Checklist

- [ ] Ran `./deploy-nas.sh` successfully
- [ ] Can access http://localhost:8000/api/docs
- [ ] Health check returns `"healthy"`
- [ ] Registered a test user
- [ ] Got JWT token from login
- [ ] Added a team member
- [ ] Can view team members list
- [ ] Data persists after `docker compose restart`

**All checked?** You're ready to go! 🎉

---

## 🆘 Need Help?

**Quick checks:**
```bash
# Health
curl http://localhost:8000/api/health

# Logs
docker compose -f docker-compose.backend.yml logs -f

# Status
docker compose -f docker-compose.backend.yml ps
```

**Documentation:**
- Quick issues: This file
- Docker: [README.Docker.md](README.Docker.md)
- NAS setup: [NAS_DEPLOYMENT_GUIDE.md](NAS_DEPLOYMENT_GUIDE.md)
- Detailed troubleshooting: [NAS_DEPLOYMENT_GUIDE.md#troubleshooting](NAS_DEPLOYMENT_GUIDE.md#troubleshooting)

---

**Happy tracking! 🚀**
