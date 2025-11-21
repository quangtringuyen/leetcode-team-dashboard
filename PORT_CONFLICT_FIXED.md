# ✅ Port Conflict Fixed!

The port 8000 conflict has been resolved. Your API will now run on **port 8080** instead.

---

## 🔧 What Was Changed

**File:** `docker-compose.backend.yml`

**Change:**
```yaml
# Before:
ports:
  - "8000:8000"

# After:
ports:
  - "8080:8000"  # Changed to port 8080 to avoid conflict
```

---

## 🌐 New Access URLs

After deployment, access your API at:

- **API Documentation:** http://localhost:8080/api/docs
- **ReDoc:** http://localhost:8080/api/redoc
- **Health Check:** http://localhost:8080/api/health

**Or if on NAS:**
- http://YOUR-NAS-IP:8080/api/docs

---

## 🚀 How to Deploy

### Option 1: Fix Docker PATH First (Recommended)

Docker Desktop is installed but not in your PATH. Add it:

```bash
# Add to your ~/.zshrc or ~/.bash_profile
export PATH="/Applications/Docker.app/Contents/Resources/bin:$PATH"

# Reload shell
source ~/.zshrc  # or source ~/.bash_profile

# Verify
docker --version
```

Then run:
```bash
./deploy-nas.sh
```

---

### Option 2: Use Docker Desktop GUI

1. **Open Docker Desktop** application
2. **Stop any existing containers** on port 8000:
   - Go to "Containers" tab
   - Find containers using port 8000
   - Click Stop → Delete

3. **Import project via Docker Desktop:**
   - Click "+" to add
   - Navigate to: `/Users/tringuyen/dev/code/leetcode-team-dashboard`
   - Select `docker-compose.backend.yml`
   - Click "Run"

---

### Option 3: Use Full Docker Path

```bash
# Set docker path
DOCKER="/Applications/Docker.app/Contents/Resources/bin/docker"

# Build and start
$DOCKER compose -f docker-compose.backend.yml up -d

# Check status
$DOCKER compose -f docker-compose.backend.yml ps

# View logs
$DOCKER compose -f docker-compose.backend.yml logs -f
```

---

## ✅ Verify Deployment

Once running, test:

```bash
# Health check (note: port 8080 now!)
curl http://localhost:8080/api/health

# Expected response:
# {"status":"healthy","service":"LeetCode Team Dashboard API","version":"2.0.0"}
```

---

## 🔙 To Switch Back to Port 8000

If you want to use port 8000 later:

1. **Stop the process using port 8000:**
   - Open Docker Desktop → Containers
   - Find and stop the container on port 8000

2. **Edit `docker-compose.backend.yml`:**
   ```yaml
   ports:
     - "8000:8000"  # Back to port 8000
   ```

3. **Restart:**
   ```bash
   docker compose -f docker-compose.backend.yml restart
   ```

---

## 📊 Quick Reference

| Old URL | New URL |
|---------|---------|
| http://localhost:8000/api/docs | http://localhost:8080/api/docs |
| http://localhost:8000/api/health | http://localhost:8080/api/health |
| http://localhost:8000/api/redoc | http://localhost:8080/api/redoc |

**Remember:** Update any frontend code or API calls to use port **8080** instead of 8000!

---

## 🆘 Troubleshooting

### Still getting port conflict?

```bash
# Check what's using port 8080
lsof -i :8080

# Or use another port (e.g., 8090):
# Edit docker-compose.backend.yml:
ports:
  - "8090:8000"
```

### Docker command not found?

1. Make sure Docker Desktop is running (check menu bar)
2. Add Docker to PATH (see Option 1 above)
3. Or use full path (see Option 3 above)

---

**Next Step:** Deploy using one of the options above! 🚀
