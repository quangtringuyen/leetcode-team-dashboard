# 🚀 NAS Deployment Guide - Docker

Complete guide for deploying LeetCode Team Dashboard to your NAS using Docker.

---

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Deployment](#quick-deployment)
3. [NAS-Specific Setup](#nas-specific-setup)
4. [Configuration](#configuration)
5. [Troubleshooting](#troubleshooting)
6. [Maintenance](#maintenance)

---

## ✅ Prerequisites

### What You Need
- NAS with Docker support (Synology, QNAP, TrueNAS, etc.)
- SSH access to your NAS
- At least 512MB RAM available
- ~2GB storage space

### Supported NAS Platforms
- ✅ Synology DSM 7.0+
- ✅ QNAP QTS 4.5+
- ✅ TrueNAS SCALE
- ✅ Unraid
- ✅ Any NAS with Docker

---

## 🚀 Quick Deployment

### Step 1: Upload Files to NAS

```bash
# From your local machine, upload to NAS
scp -r leetcode-team-dashboard username@nas-ip:/volume1/docker/

# Or use your NAS web interface to upload the folder
```

### Step 2: SSH into NAS

```bash
ssh username@nas-ip
cd /volume1/docker/leetcode-team-dashboard
```

### Step 3: Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit configuration
nano .env
```

Required settings:
```bash
# Security (REQUIRED - change this!)
SECRET_KEY=your-random-secret-key-here

# AWS S3 (Optional - leave empty for local storage)
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_DEFAULT_REGION=ap-southeast-1
S3_BUCKET_NAME=
S3_PREFIX=prod

# Scheduler
RUN_ON_STARTUP=false
ENVIRONMENT=production
```

### Step 4: Deploy

```bash
# Build and start services
docker-compose -f docker-compose.backend.yml up -d

# Check status
docker-compose -f docker-compose.backend.yml ps

# View logs
docker-compose -f docker-compose.backend.yml logs -f
```

### Step 5: Verify

```bash
# Test API health
curl http://localhost:8000/api/health

# Or from browser:
# http://your-nas-ip:8000/api/docs
```

---

## 🏢 NAS-Specific Setup

### Synology NAS

#### Method 1: Container Manager (GUI)

1. **Open Container Manager**
   - Go to Package Center
   - Install "Container Manager" (formerly Docker)

2. **Create Project**
   - Container Manager → Project
   - Click "Create"
   - Name: `leetcode-dashboard`
   - Path: `/docker/leetcode-team-dashboard`
   - Source: `docker-compose.backend.yml`
   - Click "Create"

3. **Configure Ports**
   - Port 8000 → 8000 (API)
   - Click "Apply"

4. **Start Services**
   - Select project
   - Click "Start"

#### Method 2: SSH Terminal

```bash
# SSH into Synology
ssh admin@synology-ip

# Navigate to docker folder
cd /volume1/docker/leetcode-team-dashboard

# Deploy
sudo docker-compose -f docker-compose.backend.yml up -d
```

#### Synology Reverse Proxy Setup

1. **Control Panel → Login Portal → Advanced → Reverse Proxy**
2. Click "Create"
3. Configure:
   ```
   Description: LeetCode Dashboard API
   Source:
     Protocol: HTTP/HTTPS
     Hostname: leetcode.yournas.com (or use IP)
     Port: 80 (or 443 for HTTPS)

   Destination:
     Protocol: HTTP
     Hostname: localhost
     Port: 8000
   ```
4. Save

Now access via: `http://leetcode.yournas.com/api/docs`

---

### QNAP NAS

#### Using Container Station

1. **Open Container Station**
   - App Center → Install Container Station

2. **Create Container**
   - Container Station → Create
   - Search: "Create Application"
   - Choose "Create with docker-compose.yml"

3. **Upload Configuration**
   - Copy contents of `docker-compose.backend.yml`
   - Paste into editor
   - Click "Validate and Apply"

4. **Start Application**
   - Click "Start"

#### Using SSH

```bash
# SSH into QNAP
ssh admin@qnap-ip

# Navigate to docker folder
cd /share/Container/leetcode-team-dashboard

# Deploy
docker-compose -f docker-compose.backend.yml up -d
```

---

### TrueNAS SCALE

1. **Navigate to Apps**
   - Apps → Available Applications

2. **Launch Custom App**
   - Click "Launch Docker Image"
   - Or use "Custom App" with docker-compose

3. **Configure Application**
   ```
   Application Name: leetcode-api
   Image Repository: (build from Dockerfile.backend)
   Port Forwarding: 8000:8000
   Storage: Add volume /mnt/pool/data -> /app/data
   Environment Variables: (add from .env)
   ```

4. **Deploy**
   - Click "Save" to deploy

---

### Unraid

1. **Docker Tab**
   - Navigate to Docker tab

2. **Add Container**
   ```
   Name: leetcode-api
   Repository: (build from Dockerfile.backend)
   Port: 8000 -> 8000
   Path: /mnt/user/appdata/leetcode/data -> /app/data
   Environment Variables: (from .env)
   ```

3. **Apply**
   - Click "Apply" to start

---

## ⚙️ Configuration

### Environment Variables

Create or edit `.env` file:

```bash
# ===========================================
# SECURITY (REQUIRED)
# ===========================================
SECRET_KEY=generate-a-random-secret-key-here

# Generate a secret key:
# python -c "import secrets; print(secrets.token_urlsafe(32))"

# ===========================================
# AWS S3 STORAGE (OPTIONAL)
# ===========================================
# Leave empty to use local storage
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_DEFAULT_REGION=ap-southeast-1
S3_BUCKET_NAME=
S3_PREFIX=prod

# ===========================================
# APPLICATION SETTINGS
# ===========================================
ENVIRONMENT=production
RUN_ON_STARTUP=false

# CORS Origins (if using custom domain)
CORS_ORIGINS=http://localhost:3000,http://your-nas-ip:8000

# Token expiration (in minutes)
ACCESS_TOKEN_EXPIRE_MINUTES=10080
```

### Port Configuration

Default ports in `docker-compose.backend.yml`:

```yaml
ports:
  - "8000:8000"  # API port
```

To change:
```yaml
ports:
  - "8080:8000"  # Access API on port 8080
```

### Storage Configuration

#### Local Storage (Default)
```yaml
volumes:
  - ./data:/app/data
```

Data stored in: `/volume1/docker/leetcode-team-dashboard/data`

#### S3 Storage
Configure in `.env`:
```bash
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
S3_BUCKET_NAME=your-bucket
```

---

## 🔧 Docker Commands

### Basic Operations

```bash
# Navigate to project directory
cd /volume1/docker/leetcode-team-dashboard

# Start services
docker-compose -f docker-compose.backend.yml up -d

# Stop services
docker-compose -f docker-compose.backend.yml down

# Restart services
docker-compose -f docker-compose.backend.yml restart

# View logs
docker-compose -f docker-compose.backend.yml logs -f

# View specific service logs
docker-compose -f docker-compose.backend.yml logs -f api
docker-compose -f docker-compose.backend.yml logs -f scheduler

# Check status
docker-compose -f docker-compose.backend.yml ps
```

### Maintenance

```bash
# Update and rebuild
docker-compose -f docker-compose.backend.yml down
docker-compose -f docker-compose.backend.yml build --no-cache
docker-compose -f docker-compose.backend.yml up -d

# View resource usage
docker stats

# Clean up unused images
docker system prune -a

# Backup data
tar -czf backup-$(date +%Y%m%d).tar.gz data/
```

---

## 🐛 Troubleshooting

### Service Won't Start

**Check logs:**
```bash
docker-compose -f docker-compose.backend.yml logs api
```

**Common issues:**
- Port 8000 already in use
  ```bash
  # Check what's using the port
  sudo lsof -i :8000
  # Kill process or change port in docker-compose
  ```

- Permission issues
  ```bash
  # Fix data directory permissions
  sudo chmod -R 755 data/
  sudo chown -R 1000:1000 data/
  ```

### Cannot Access API

**Check container status:**
```bash
docker-compose -f docker-compose.backend.yml ps
```

**Test from NAS:**
```bash
curl http://localhost:8000/api/health
```

**Check firewall:**
- Ensure port 8000 is open on your NAS firewall
- Synology: Control Panel → Security → Firewall
- QNAP: Control Panel → Security → Firewall

### LeetCode API Errors

**DNS issues:**
Already configured with public DNS (8.8.8.8, 1.1.1.1)

**Test connectivity:**
```bash
docker exec leetcode-api curl -I https://leetcode.com
```

**Check logs:**
```bash
docker logs leetcode-api | grep ERROR
```

### High Memory Usage

**Limit resources:**
Edit `docker-compose.backend.yml`:
```yaml
services:
  api:
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: '0.5'
```

### Scheduler Not Running

**Check scheduler logs:**
```bash
docker logs leetcode-scheduler
```

**Restart scheduler:**
```bash
docker-compose -f docker-compose.backend.yml restart scheduler
```

---

## 🔐 Security Best Practices

### 1. Change Default Secret Key

```bash
# Generate new secret key
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Update .env
SECRET_KEY=your-new-secret-key
```

### 2. Enable HTTPS (Optional)

**Using Nginx:**
```bash
# Uncomment nginx service in docker-compose.backend.yml
# Add SSL certificates to nginx/ssl/
# Update nginx.conf to enable HTTPS
```

**Using NAS Reverse Proxy:**
- Use Synology/QNAP built-in reverse proxy
- Enable Let's Encrypt certificate
- Configure HTTPS redirect

### 3. Firewall Configuration

**Synology:**
- Control Panel → Security → Firewall
- Allow port 8000 from trusted IPs only

**QNAP:**
- Control Panel → Security → Firewall
- Add rule for port 8000

### 4. Regular Updates

```bash
# Pull latest code
git pull

# Rebuild containers
docker-compose -f docker-compose.backend.yml build --no-cache
docker-compose -f docker-compose.backend.yml up -d
```

---

## 📊 Monitoring

### Health Checks

```bash
# API health
curl http://your-nas-ip:8000/api/health

# Container health
docker inspect leetcode-api | grep -A 10 Health
```

### Logs

```bash
# Real-time logs
docker-compose -f docker-compose.backend.yml logs -f --tail=100

# Save logs to file
docker logs leetcode-api > api.log 2>&1

# Configure log rotation (in docker-compose.backend.yml)
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

---

## 🔄 Backup & Restore

### Backup Data

```bash
# Backup data directory
tar -czf leetcode-backup-$(date +%Y%m%d).tar.gz data/

# Or use NAS backup features
# Synology: Hyper Backup
# QNAP: Hybrid Backup Sync
```

### Restore Data

```bash
# Stop services
docker-compose -f docker-compose.backend.yml down

# Restore data
tar -xzf leetcode-backup-20250101.tar.gz

# Start services
docker-compose -f docker-compose.backend.yml up -d
```

### Automated Backups

Add to NAS scheduled tasks:

**Synology:**
```bash
# Control Panel → Task Scheduler → Create → Scheduled Task
# Script:
cd /volume1/docker/leetcode-team-dashboard
tar -czf /volume1/backups/leetcode-$(date +%Y%m%d).tar.gz data/
find /volume1/backups -name "leetcode-*.tar.gz" -mtime +30 -delete
```

**QNAP:**
```bash
# Control Panel → System → Task Scheduler
# Add task with same script above
```

---

## 📈 Performance Tuning

### Resource Limits

```yaml
# docker-compose.backend.yml
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

### Database Optimization

For high-traffic scenarios, consider:
- Adding Redis for caching
- Using PostgreSQL instead of JSON files
- Enabling database connection pooling

---

## 🌐 Access URLs

After deployment:

- **API Docs**: http://your-nas-ip:8000/api/docs
- **ReDoc**: http://your-nas-ip:8000/api/redoc
- **Health Check**: http://your-nas-ip:8000/api/health

With reverse proxy:
- http://leetcode.yournas.com/api/docs

---

## ✅ Quick Verification Checklist

- [ ] Files uploaded to NAS
- [ ] `.env` configured with SECRET_KEY
- [ ] Docker containers running
- [ ] Can access http://nas-ip:8000/api/health
- [ ] API docs load at /api/docs
- [ ] Can register a user
- [ ] Can login and get token
- [ ] Scheduler container running
- [ ] Data persists after restart
- [ ] Firewall configured (if needed)
- [ ] Backups configured

---

## 🆘 Getting Help

### Check Logs
```bash
docker-compose -f docker-compose.backend.yml logs -f
```

### Run Tests
```bash
docker exec leetcode-api python test_backend.py
```

### Debug Mode
```bash
# Enable debug logging
docker-compose -f docker-compose.backend.yml down
# Edit .env: LOG_LEVEL=debug
docker-compose -f docker-compose.backend.yml up
```

---

## 📞 Support

- **Documentation**: Check all `.md` files in project
- **API Docs**: http://your-nas-ip:8000/api/docs
- **Test Script**: `docker exec leetcode-api python test_backend.py`
- **Logs**: `docker-compose -f docker-compose.backend.yml logs -f`

---

## 🎉 Success!

Your LeetCode Team Dashboard is now running on your NAS! 🚀

**Next Steps:**
1. Access API docs: http://your-nas-ip:8000/api/docs
2. Register your first user
3. Add team members
4. Start tracking progress!

**Building a frontend?**
- The API is ready for any frontend (React, Vue, Mobile apps)
- Check API documentation for all available endpoints
- CORS is configured for local development

---

**Need to build the frontend?** The backend API is ready and waiting! 🎯
