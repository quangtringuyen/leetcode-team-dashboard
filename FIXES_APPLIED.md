# 🔧 Fixes Applied - Scheduler & CORS Issues

Two critical issues have been fixed:

---

## ✅ Fix 1: Scheduler File Missing

**Problem:**
```
python: can't open file '/app/scheduler.py': [Errno 2] No such file or directory
```

**Solution:**
Updated `Dockerfile.backend` to copy `scheduler.py` into the Docker image.

**Change:**
```dockerfile
# Before:
COPY backend/ backend/
COPY utils/ utils/
COPY .env* ./

# After:
COPY backend/ backend/
COPY utils/ utils/
COPY scheduler.py .    # ← Added this line
COPY .env* ./
```

---

## ✅ Fix 2: CORS_ORIGINS Parsing Error (UPDATED FIX)

**Problem:**
```
json.decoder.JSONDecodeError: Expecting value: line 1 column 1 (char 0)
pydantic_settings.exceptions.SettingsError: error parsing value for field "CORS_ORIGINS"
```

**Root Cause:**
- `.env` file has: `CORS_ORIGINS=http://localhost:3000,http://localhost:8000`
- Pydantic v2 tries to parse `List[str]` fields as JSON first
- Comma-separated string is not valid JSON, causing parse error before validator runs

**Solution:**
Updated `backend/core/config.py` with improved Pydantic v2 configuration:

```python
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator, Field
import json

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_file='.env',
        env_file_encoding='utf-8',
        extra='ignore'
    )

    CORS_ORIGINS: List[str] = Field(
        default=[
            "http://localhost:3000",
            "http://localhost:8000",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:8000",
        ]
    )

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Any) -> List[str]:
        """Parse CORS_ORIGINS from various formats"""
        if isinstance(v, list):
            return v
        if isinstance(v, str):
            v = v.strip()
            if not v:
                return []
            # Try JSON first
            if v.startswith('['):
                try:
                    return json.loads(v)
                except json.JSONDecodeError:
                    pass
            # Parse as comma-separated
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return []
```

Now it supports all formats:
- ✅ Comma-separated: `CORS_ORIGINS=http://localhost:3000,http://localhost:8000`
- ✅ JSON array: `CORS_ORIGINS=["http://localhost:3000", "http://localhost:8000"]`
- ✅ Python list (programmatic use)

---

## 🚀 How to Apply Fixes

### Option 1: Using Docker Desktop GUI

1. **Open Docker Desktop**
2. **Go to Containers** tab
3. **Stop and delete** existing containers:
   - Find `leetcode-api`
   - Find `leetcode-scheduler`
   - Click Stop → Delete for each

4. **Rebuild:**
   - Go to Images tab
   - Delete old images (optional)
   - Go back to project folder

5. **Start fresh:**
   - Import `docker-compose.backend.yml` again
   - Or use terminal (see Option 2)

---

### Option 2: Using Terminal (If Docker is in PATH)

```bash
# Navigate to project
cd /Users/tringuyen/dev/code/leetcode-team-dashboard

# Stop and remove old containers
docker compose -f docker-compose.backend.yml down

# Rebuild with no cache
docker compose -f docker-compose.backend.yml build --no-cache

# Start services
docker compose -f docker-compose.backend.yml up -d

# Check status
docker compose -f docker-compose.backend.yml ps

# View logs
docker compose -f docker-compose.backend.yml logs -f
```

---

### Option 3: Add Docker to PATH First

If `docker` command not found, add it to PATH:

```bash
# Find Docker location
ls -la /usr/local/bin/docker

# If not there, Docker Desktop might be at:
# /Applications/Docker.app/Contents/Resources/bin/docker

# Add to PATH (add to ~/.zshrc or ~/.bash_profile)
export PATH="/usr/local/bin:$PATH"

# Or if using Docker Desktop:
export PATH="/Applications/Docker.app/Contents/Resources/bin:$PATH"

# Reload shell
source ~/.zshrc  # or source ~/.bash_profile

# Verify
docker --version
```

Then use Option 2 commands above.

---

## ✅ Verification After Fix

### 1. Check Containers Are Running

```bash
docker compose -f docker-compose.backend.yml ps
```

**Expected output:**
```
NAME                  STATUS              PORTS
leetcode-api         Up (healthy)        0.0.0.0:8080->8000/tcp
leetcode-scheduler   Up (healthy)
```

### 2. Check API Health

```bash
curl http://localhost:8080/api/health
```

**Expected response:**
```json
{
  "status": "healthy",
  "service": "LeetCode Team Dashboard API",
  "version": "2.0.0"
}
```

### 3. Check Logs for Errors

```bash
# API logs
docker compose -f docker-compose.backend.yml logs api | grep -i error

# Scheduler logs
docker compose -f docker-compose.backend.yml logs scheduler | grep -i error
```

**Expected:** No error messages about missing files or CORS parsing

---

## 🎯 Access Your API

After successful deployment:

- **API Docs:** http://localhost:8080/api/docs
- **ReDoc:** http://localhost:8080/api/redoc
- **Health Check:** http://localhost:8080/api/health

**Remember:** Port is **8080** (not 8000) due to earlier port conflict fix!

---

## 📝 What Changed

### Files Modified:
1. **Dockerfile.backend** - Added `COPY scheduler.py .`
2. **backend/core/config.py** - Added CORS_ORIGINS validator

### No Changes Needed To:
- ✅ `.env` file (keep as-is)
- ✅ `docker-compose.backend.yml` (keep port 8080)
- ✅ `scheduler.py` (unchanged)
- ✅ All other backend files (unchanged)

---

## 🐛 Troubleshooting

### Still Getting Scheduler Error?

**Check if scheduler.py exists:**
```bash
ls -la scheduler.py
```

If missing, the scheduler won't work. Ensure the file exists in project root.

---

### Still Getting CORS Error?

**Check your .env file format:**
```bash
cat .env | grep CORS_ORIGINS
```

**Should be:**
```
CORS_ORIGINS=http://localhost:3000,http://localhost:8000,http://localhost:8501
```

**NOT:**
```
CORS_ORIGINS="http://localhost:3000,http://localhost:8000"  # Remove quotes!
```

---

### Docker Command Not Found?

1. Check if Docker Desktop is running (menu bar icon)
2. Add Docker to PATH (see Option 3 above)
3. Or use Docker Desktop GUI (see Option 1 above)

---

## ✅ Success Checklist

After applying fixes:

- [ ] Containers rebuilt (`docker compose build --no-cache`)
- [ ] Containers running (`docker compose ps` shows "Up")
- [ ] No "scheduler.py" error in logs
- [ ] No "CORS_ORIGINS" error in logs
- [ ] API health check returns "healthy"
- [ ] Can access http://localhost:8080/api/docs

**All checked?** You're good to go! 🎉

---

## 📚 Next Steps

1. **Test the API:** Use the Swagger UI at http://localhost:8080/api/docs
2. **Register a user:** Create your first account
3. **Add team members:** Start tracking LeetCode progress
4. **Check scheduler:** Verify it runs on Monday at midnight

---

**Issues resolved! Ready to use your LeetCode Team Dashboard! 🚀**
