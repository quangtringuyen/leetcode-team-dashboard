# 🏠 Deploy to Your NAS - Complete Guide

## 🚀 Quick Deploy (2 Steps)

### Step 1: Run Deployment Script

```bash
./deploy-nas.sh
```

This deploys **both React frontend and FastAPI backend** automatically!

### Step 2: Access Your Dashboard

- **Frontend UI:** http://YOUR-NAS-IP:3000
- **API Docs:** http://YOUR-NAS-IP:8080/api/docs

Replace `YOUR-NAS-IP` with your actual NAS IP (e.g., `192.168.1.100`)

---

## 📋 What Gets Deployed

✅ **React Frontend** (Port 3000)
- Modern glass morphism UI
- Responsive mobile design
- Smooth animations

✅ **FastAPI Backend** (Port 8080)
- 13 API endpoints
- JWT authentication
- LeetCode data fetching
- S3 or local storage

---

## ⚙️ Before Deploying

### 1. Check `.env` Configuration

Make sure your `.env` file has:

```bash
# Required
SECRET_KEY=7Sj_WCbTO6YBISwDachdPlijS82L8W6dMcm8MQ4oKbg

# Update with your NAS IP
CORS_ORIGINS=http://192.168.1.100:3000,http://192.168.1.100:8080

# Optional: S3 Storage (comment out to use local storage)
# AWS_ACCESS_KEY_ID=your-key
# AWS_SECRET_ACCESS_KEY=your-secret
# S3_BUCKET_NAME=your-bucket
```

### 2. Prerequisites

- ✅ Docker installed on NAS
- ✅ Docker Compose v2+
- ✅ 2GB+ free RAM
- ✅ 5GB+ free disk space

---

## 🎯 Deployment Options

### Option 1: Automated Script (Recommended)

```bash
# Deploy full stack (frontend + backend)
./deploy-nas.sh
```

### Option 2: Docker Compose Manual

```bash
# Build and start all services
docker compose -f docker-compose.fullstack.yml up -d --build

# Check status
docker compose -f docker-compose.fullstack.yml ps

# View logs
docker compose -f docker-compose.fullstack.yml logs -f
```

### Option 3: Backend Only

If you just want the API:

```bash
docker compose -f docker-compose.backend.yml up -d --build
```

---

## 📡 After Deployment

### 1. Access Frontend

Open in your browser:
```
http://YOUR-NAS-IP:3000
```

### 2. Register First User

Click "Sign up" and create your account.

### 3. Add Team Members

- Go to "Team" page
- Click "Add Member"
- Enter LeetCode username

### 4. Record Snapshot

- Dashboard → "Record Snapshot"
- Fetches live data from LeetCode

---

## 🔧 Useful Commands

### View Logs
```bash
docker compose -f docker-compose.fullstack.yml logs -f
```

### Restart Services
```bash
docker compose -f docker-compose.fullstack.yml restart
```

### Stop Everything
```bash
docker compose -f docker-compose.fullstack.yml down
```

### Update Application
```bash
# Pull latest code
git pull

# Rebuild and restart
docker compose -f docker-compose.fullstack.yml up -d --build
```

---

## 🐛 Troubleshooting

### Frontend Can't Connect to Backend

1. Check CORS in `.env`:
   ```bash
   CORS_ORIGINS=http://YOUR-NAS-IP:3000
   ```

2. Restart backend:
   ```bash
   docker compose -f docker-compose.fullstack.yml restart api
   ```

### Port Already in Use

Change ports in `docker-compose.fullstack.yml`:

```yaml
services:
  frontend:
    ports:
      - "8080:3000"  # Change 8080 to available port

  api:
    ports:
      - "8000:8000"  # Change 8000 to available port
```

### Can't Login

- Make sure you registered an account first
- Check backend logs for errors
- Verify `data/users.json` exists (if using local storage)

---

## 📊 Supported NAS Systems

| NAS System | Tested | Notes |
|------------|--------|-------|
| Synology DSM 7.0+ | ✅ | Full support |
| QNAP QTS 5.0+ | ✅ | Full support |
| TrueNAS Scale | ✅ | Full support |
| Unraid 6.9+ | ✅ | Full support |
| Generic Linux | ✅ | With Docker |

---

## 💾 Data Storage

### Local Storage (Default)

Data stored in `./data/`:
```
data/
├── users.json       # User accounts
├── members.json     # Team members
└── history.json     # Weekly snapshots
```

### S3 Storage (Optional)

Uncomment in `.env`:
```bash
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret
S3_BUCKET_NAME=your-bucket
S3_PREFIX=prod
```

---

## 🎉 Success Checklist

After deployment, verify:

- [ ] Frontend loads at http://YOUR-NAS-IP:3000
- [ ] Can register a new account
- [ ] Can login successfully
- [ ] API docs work at http://YOUR-NAS-IP:8080/api/docs
- [ ] Can add team members
- [ ] Can record snapshots
- [ ] Charts display data

---

## 📞 Need Help?

### Check Container Status
```bash
docker compose -f docker-compose.fullstack.yml ps
docker compose -f docker-compose.fullstack.yml logs --tail=50
```

### Health Checks
```bash
# Backend
curl http://localhost:8080/api/health

# Should return: {"status":"healthy","storage":"local"} or "s3"
```

---

## 🔐 Security Tips

1. **Change Secret Key** in `.env` before deploying to production
2. **Use HTTPS** with a reverse proxy (Nginx/Traefik)
3. **Firewall Rules** - Only expose to local network
4. **Regular Backups** of `data/` directory

---

**Your modern dashboard is ready!** 🚀

Questions? Check the full guide: [NAS_DEPLOYMENT_GUIDE.md](NAS_DEPLOYMENT_GUIDE.md)
