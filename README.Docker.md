# 🐳 Docker Deployment - Quick Start

This guide helps you deploy the LeetCode Team Dashboard backend API using Docker on any platform, including NAS devices.

---

## 🚀 Quick Start (60 seconds)

### Automated Deployment (Recommended)

```bash
# 1. Clone/upload the project to your server
cd leetcode-team-dashboard

# 2. Run the deployment script
./deploy-nas.sh
```

That's it! The script will:
- ✅ Create `.env` file with secure random SECRET_KEY
- ✅ Create data directories
- ✅ Build Docker images
- ✅ Start all services
- ✅ Run health checks

### Manual Deployment

```bash
# 1. Copy environment template
cp .env.backend.example .env

# 2. Generate a secret key
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# 3. Edit .env and set SECRET_KEY
nano .env

# 4. Start services
docker compose -f docker-compose.backend.yml up -d

# 5. Check status
docker compose -f docker-compose.backend.yml ps

# 6. View logs
docker compose -f docker-compose.backend.yml logs -f
```

---

## 📍 Access Your Dashboard

After deployment, access:

- **API Documentation**: http://YOUR-SERVER-IP:8000/api/docs
- **Alternative Docs**: http://YOUR-SERVER-IP:8000/api/redoc
- **Health Check**: http://YOUR-SERVER-IP:8000/api/health

Replace `YOUR-SERVER-IP` with:
- `localhost` if running locally
- Your NAS IP address (e.g., `192.168.1.100`)
- Your domain name if configured

---

## 🏗️ Architecture

The deployment includes:

```
┌─────────────────────────────────────┐
│         Docker Network              │
│                                     │
│  ┌──────────────┐  ┌─────────────┐ │
│  │   API        │  │  Scheduler  │ │
│  │ (Port 8000)  │  │  (Cron)     │ │
│  └──────────────┘  └─────────────┘ │
│         │                 │         │
│         └────────┬────────┘         │
│                  │                  │
│         ┌────────▼────────┐        │
│         │   Shared Data   │        │
│         │   Volume        │        │
│         └─────────────────┘        │
└─────────────────────────────────────┘
```

**Services:**
1. **API Service** (`leetcode-api`)
   - FastAPI REST API
   - Port: 8000
   - Health checks enabled

2. **Scheduler Service** (`leetcode-scheduler`)
   - Weekly snapshot automation
   - Runs in background
   - Shares data with API

**Shared Resources:**
- `./data` - JSON storage for users, teams, history
- `./logs` - Application logs
- Docker network for inter-service communication

---

## 📋 Requirements

### System Requirements
- Docker Engine 20.10+
- Docker Compose 2.0+
- 512MB RAM minimum
- 2GB disk space
- Network access to LeetCode.com

### Compatible Platforms
- ✅ Linux (Ubuntu, Debian, CentOS, etc.)
- ✅ macOS
- ✅ Windows (with Docker Desktop)
- ✅ Synology DSM 7.0+
- ✅ QNAP QTS 4.5+
- ✅ TrueNAS SCALE
- ✅ Unraid
- ✅ Any NAS with Docker support

---

## ⚙️ Configuration

### Environment Variables

Edit `.env` file:

```bash
# REQUIRED: Change this!
SECRET_KEY=your-random-secret-key

# OPTIONAL: S3 Storage (leave empty for local files)
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_DEFAULT_REGION=ap-southeast-1
S3_BUCKET_NAME=
S3_PREFIX=prod

# Application Settings
ENVIRONMENT=production
RUN_ON_STARTUP=false
LOG_LEVEL=info

# CORS (add your frontend URL)
CORS_ORIGINS=http://localhost:3000,http://localhost:8000

# Token expiration (7 days default)
ACCESS_TOKEN_EXPIRE_MINUTES=10080
```

### Port Configuration

Default: Port 8000

To change, edit `docker-compose.backend.yml`:

```yaml
ports:
  - "8080:8000"  # Change 8080 to your preferred port
```

Then restart:
```bash
docker compose -f docker-compose.backend.yml restart
```

### Storage Options

**Option 1: Local Storage (Default)**
- Data stored in `./data` directory
- Automatic backups recommended
- Perfect for small teams

**Option 2: AWS S3 Storage**
- Configure AWS credentials in `.env`
- Automatic cloud backup
- Scalable for large teams

---

## 🔧 Common Commands

### Service Management

```bash
# Start services
docker compose -f docker-compose.backend.yml up -d

# Stop services
docker compose -f docker-compose.backend.yml down

# Restart services
docker compose -f docker-compose.backend.yml restart

# View status
docker compose -f docker-compose.backend.yml ps

# View logs (all services)
docker compose -f docker-compose.backend.yml logs -f

# View logs (specific service)
docker compose -f docker-compose.backend.yml logs -f api
docker compose -f docker-compose.backend.yml logs -f scheduler
```

### Updates

```bash
# Pull latest code
git pull

# Rebuild and restart
docker compose -f docker-compose.backend.yml down
docker compose -f docker-compose.backend.yml build --no-cache
docker compose -f docker-compose.backend.yml up -d
```

### Maintenance

```bash
# Check container health
docker inspect leetcode-api | grep -A 10 Health

# Check resource usage
docker stats

# Clean up unused images
docker system prune -a

# Backup data
tar -czf backup-$(date +%Y%m%d).tar.gz data/

# Restore data
tar -xzf backup-20250101.tar.gz
```

---

## 🐛 Troubleshooting

### Service won't start

**Check logs:**
```bash
docker compose -f docker-compose.backend.yml logs api
```

**Common issues:**
1. Port 8000 already in use
   ```bash
   # Find what's using the port
   lsof -i :8000
   # Kill the process or change port in docker-compose
   ```

2. Permission denied on data directory
   ```bash
   chmod -R 755 data/
   chown -R 1000:1000 data/
   ```

### Can't access API

**Test from server:**
```bash
curl http://localhost:8000/api/health
```

**Check firewall:**
- Ensure port 8000 is open
- For NAS: Check firewall settings in control panel

**Check container:**
```bash
docker compose -f docker-compose.backend.yml ps
# Should show "Up" and "healthy" status
```

### LeetCode API errors

**Test connectivity:**
```bash
docker exec leetcode-api curl -I https://leetcode.com
```

**Check DNS:**
- Already configured with public DNS (8.8.8.8, 1.1.1.1)
- Should work on most networks

---

## 🔐 Security Best Practices

1. **Change SECRET_KEY**
   ```bash
   python3 -c "import secrets; print(secrets.token_urlsafe(32))"
   # Update .env with generated key
   ```

2. **Use HTTPS** (Production)
   - Enable nginx service (uncommented in docker-compose)
   - Add SSL certificates
   - Or use NAS reverse proxy with Let's Encrypt

3. **Firewall Configuration**
   - Only allow port 8000 from trusted IPs
   - Use VPN for remote access
   - Enable fail2ban if available

4. **Regular Updates**
   ```bash
   git pull
   docker compose -f docker-compose.backend.yml build --no-cache
   docker compose -f docker-compose.backend.yml up -d
   ```

---

## 📊 Monitoring

### Health Checks

```bash
# API health
curl http://localhost:8000/api/health

# Container health
docker inspect leetcode-api | grep -A 10 Health

# Check all containers
docker compose -f docker-compose.backend.yml ps
```

### Logs

```bash
# Real-time logs
docker compose -f docker-compose.backend.yml logs -f --tail=100

# Save logs to file
docker logs leetcode-api > api.log 2>&1
docker logs leetcode-scheduler > scheduler.log 2>&1
```

---

## 🔄 Backup & Restore

### Manual Backup

```bash
# Backup data
tar -czf leetcode-backup-$(date +%Y%m%d).tar.gz data/

# Backup with environment
tar -czf leetcode-full-backup-$(date +%Y%m%d).tar.gz data/ .env
```

### Restore

```bash
# Stop services
docker compose -f docker-compose.backend.yml down

# Restore data
tar -xzf leetcode-backup-20250101.tar.gz

# Start services
docker compose -f docker-compose.backend.yml up -d
```

### Automated Backups

Add to crontab:
```bash
# Daily backup at 2 AM
0 2 * * * cd /path/to/leetcode-team-dashboard && tar -czf /backups/leetcode-$(date +\%Y\%m\%d).tar.gz data/

# Keep only last 30 days
0 3 * * * find /backups -name "leetcode-*.tar.gz" -mtime +30 -delete
```

---

## 🌐 Advanced Setup

### Using Nginx Reverse Proxy

Uncomment nginx service in `docker-compose.backend.yml`:

```yaml
nginx:
  image: nginx:alpine
  container_name: leetcode-nginx
  restart: unless-stopped
  ports:
    - "80:80"
    - "443:443"
  volumes:
    - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
    - ./nginx/ssl:/etc/nginx/ssl:ro
  depends_on:
    - api
  networks:
    - leetcode-network
```

Access via: http://your-domain.com/api/docs

### Resource Limits

Edit `docker-compose.backend.yml`:

```yaml
services:
  api:
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 512M
        reservations:
          cpus: '0.5'
          memory: 256M
```

---

## 📚 Additional Documentation

- **[NAS_DEPLOYMENT_GUIDE.md](NAS_DEPLOYMENT_GUIDE.md)** - Detailed NAS-specific instructions
- **[NO_STREAMLIT_MIGRATION.md](NO_STREAMLIT_MIGRATION.md)** - Migration guide from Streamlit
- **[API Documentation](http://localhost:8000/api/docs)** - Interactive API docs (after deployment)

---

## 🆘 Getting Help

**Check logs:**
```bash
docker compose -f docker-compose.backend.yml logs -f
```

**Run tests:**
```bash
docker exec leetcode-api python test_backend.py
```

**Verify API:**
```bash
curl -X GET http://localhost:8000/api/health
```

---

## 🎉 Success Checklist

- [ ] Docker services running (`docker compose ps` shows "Up")
- [ ] Health check passing (http://localhost:8000/api/health)
- [ ] Can access API docs (http://localhost:8000/api/docs)
- [ ] Can register a user via API
- [ ] Can login and get access token
- [ ] Can add team members
- [ ] Scheduler container running
- [ ] Data persists after restart (`docker compose restart`)

---

## 📞 Support

**Documentation:** All `.md` files in project root

**API Reference:** http://YOUR-IP:8000/api/docs

**Testing:** `docker exec leetcode-api python test_backend.py`

**Logs:** `docker compose -f docker-compose.backend.yml logs -f`

---

**Ready to deploy? Run `./deploy-nas.sh` and you're live in 60 seconds! 🚀**
