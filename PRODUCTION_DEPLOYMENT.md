# Production Deployment Guide for NAS

This guide will help you deploy your LeetCode Team Dashboard to your NAS with the domain `quangtringuyen.cloud` and API endpoint `api.quangtringuyen.cloud`.

## Prerequisites

✅ Domain `quangtringuyen.cloud` pointing to your NAS
✅ SSL certificate for HTTPS (Let's Encrypt recommended)
✅ Reverse proxy configured (Nginx/Traefik) on your NAS
✅ Ports 80 and 443 accessible from external network

## Step 1: Create Production Environment File

Copy the production example to create your actual production environment file:

```bash
cp .env.production.example .env.production
```

Edit `.env.production` and update these critical values:

```bash
# Update with your actual AWS credentials (if using S3)
AWS_ACCESS_KEY_ID=your-actual-key
AWS_SECRET_ACCESS_KEY=your-actual-secret
S3_BUCKET_NAME=your-actual-bucket

# Generate a new secret key
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")

# CORS origins (already configured for your domain)
CORS_ORIGINS=https://quangtringuyen.cloud,https://api.quangtringuyen.cloud,http://quangtringuyen.cloud,http://api.quangtringuyen.cloud

# Frontend API URL (already configured)
VITE_API_URL=https://api.quangtringuyen.cloud
```

## Step 2: Configure Reverse Proxy

### Option A: Nginx Configuration

Create `/etc/nginx/sites-available/leetcode-dashboard`:

```nginx
# Frontend - quangtringuyen.cloud
server {
    listen 80;
    listen [::]:80;
    server_name quangtringuyen.cloud;
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name quangtringuyen.cloud;

    # SSL Configuration
    ssl_certificate /path/to/your/fullchain.pem;
    ssl_certificate_key /path/to/your/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }
}

# API - api.quangtringuyen.cloud
server {
    listen 80;
    listen [::]:80;
    server_name api.quangtringuyen.cloud;
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name api.quangtringuyen.cloud;

    # SSL Configuration
    ssl_certificate /path/to/your/fullchain.pem;
    ssl_certificate_key /path/to/your/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    location / {
        proxy_pass http://localhost:8090;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        
        # CORS headers (optional, backend handles CORS)
        add_header Access-Control-Allow-Origin * always;
    }
}
```

Enable the configuration:

```bash
sudo ln -s /etc/nginx/sites-available/leetcode-dashboard /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### Option B: Traefik Configuration (if using Traefik)

Add labels to your `docker-compose.fullstack.yml`:

```yaml
services:
  api:
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.leetcode-api.rule=Host(`api.quangtringuyen.cloud`)"
      - "traefik.http.routers.leetcode-api.entrypoints=websecure"
      - "traefik.http.routers.leetcode-api.tls.certresolver=letsencrypt"
      - "traefik.http.services.leetcode-api.loadbalancer.server.port=8000"

  frontend:
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.leetcode-frontend.rule=Host(`quangtringuyen.cloud`)"
      - "traefik.http.routers.leetcode-frontend.entrypoints=websecure"
      - "traefik.http.routers.leetcode-frontend.tls.certresolver=letsencrypt"
      - "traefik.http.services.leetcode-frontend.loadbalancer.server.port=3000"
```

## Step 3: Deploy to NAS

### Build and Deploy

```bash
# Stop any running containers
docker-compose -f docker-compose.fullstack.yml down

# Build with production environment
docker-compose -f docker-compose.fullstack.yml --env-file .env.production build --no-cache

# Start services
docker-compose -f docker-compose.fullstack.yml --env-file .env.production up -d

# Check logs
docker-compose -f docker-compose.fullstack.yml logs -f
```

### Verify Deployment

```bash
# Check container status
docker-compose -f docker-compose.fullstack.yml ps

# Check API health
curl https://api.quangtringuyen.cloud/api/health

# Check frontend
curl https://quangtringuyen.cloud
```

## Step 4: DNS Configuration

Ensure your DNS records are set up correctly:

```
A Record:
quangtringuyen.cloud → Your NAS Public IP

A Record or CNAME:
api.quangtringuyen.cloud → Your NAS Public IP (or CNAME to quangtringuyen.cloud)
```

## Step 5: SSL Certificate Setup (Let's Encrypt)

If you haven't set up SSL certificates yet:

```bash
# Install certbot
sudo apt-get update
sudo apt-get install certbot python3-certbot-nginx

# Get certificates
sudo certbot --nginx -d quangtringuyen.cloud -d api.quangtringuyen.cloud

# Auto-renewal is set up automatically
# Test renewal with:
sudo certbot renew --dry-run
```

## Troubleshooting

### Issue: Frontend still calling localhost:8090

**Solution**: Rebuild the frontend container with the production environment:

```bash
docker-compose -f docker-compose.fullstack.yml --env-file .env.production build frontend --no-cache
docker-compose -f docker-compose.fullstack.yml --env-file .env.production up -d frontend
```

### Issue: CORS errors

**Solution**: Verify your `.env.production` has the correct CORS_ORIGINS:

```bash
docker-compose -f docker-compose.fullstack.yml --env-file .env.production exec api env | grep CORS
```

Should show:
```
CORS_ORIGINS=https://quangtringuyen.cloud,https://api.quangtringuyen.cloud,...
```

### Issue: Cannot access from external network

**Checklist**:
- [ ] Port forwarding configured on router (80, 443)
- [ ] Firewall allows incoming connections
- [ ] DNS records propagated (check with `nslookup quangtringuyen.cloud`)
- [ ] Reverse proxy running and configured correctly

### Issue: SSL certificate errors

**Solution**: Check certificate paths in Nginx config and ensure they're readable:

```bash
sudo ls -la /etc/letsencrypt/live/quangtringuyen.cloud/
```

## Maintenance

### Update Application

```bash
# Pull latest changes
git pull

# Rebuild and restart
docker-compose -f docker-compose.fullstack.yml --env-file .env.production build
docker-compose -f docker-compose.fullstack.yml --env-file .env.production up -d
```

### View Logs

```bash
# All services
docker-compose -f docker-compose.fullstack.yml logs -f

# Specific service
docker-compose -f docker-compose.fullstack.yml logs -f api
docker-compose -f docker-compose.fullstack.yml logs -f frontend
```

### Backup Data

```bash
# Backup data directory
tar -czf leetcode-backup-$(date +%Y%m%d).tar.gz ./data ./logs

# If using S3, data is already backed up in the cloud
```

## Security Recommendations

1. **Keep .env.production secure**: Never commit it to git
2. **Use strong SECRET_KEY**: Generate a new one for production
3. **Enable HTTPS only**: Redirect all HTTP to HTTPS
4. **Regular updates**: Keep Docker images and system packages updated
5. **Monitor logs**: Check for suspicious activity regularly

## Quick Reference

### Local Development
```bash
docker-compose -f docker-compose.fullstack.yml up -d
```

### Production Deployment
```bash
docker-compose -f docker-compose.fullstack.yml --env-file .env.production up -d
```

### Stop Services
```bash
docker-compose -f docker-compose.fullstack.yml down
```

### Rebuild Everything
```bash
docker-compose -f docker-compose.fullstack.yml --env-file .env.production build --no-cache
docker-compose -f docker-compose.fullstack.yml --env-file .env.production up -d
```
