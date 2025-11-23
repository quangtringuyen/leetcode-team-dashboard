# Quick Reference: Production Deployment

## 🎯 Your Configuration

- **Frontend URL**: https://quangtringuyen.cloud
- **API URL**: https://api.quangtringuyen.cloud
- **Ports**: 
  - Frontend: 3000 (internal) → 443 (external via reverse proxy)
  - API: 8090 (internal) → 443 (external via reverse proxy)

## 🚀 Deploy to Production (3 Steps)

### 1️⃣ Create Production Config
```bash
cp .env.production.example .env.production
nano .env.production  # Edit with your actual values
```

**Must update in `.env.production`**:
- `SECRET_KEY` - Generate: `python3 -c "import secrets; print(secrets.token_urlsafe(32))"`
- `AWS_ACCESS_KEY_ID` - Your AWS key
- `AWS_SECRET_ACCESS_KEY` - Your AWS secret
- `S3_BUCKET_NAME` - Your bucket name

**Already configured** (no changes needed):
- ✅ `VITE_API_URL=https://api.quangtringuyen.cloud`
- ✅ `CORS_ORIGINS=https://quangtringuyen.cloud,https://api.quangtringuyen.cloud,...`

### 2️⃣ Run Deployment Script
```bash
./deploy-production.sh
```

### 3️⃣ Configure Reverse Proxy
See `PRODUCTION_DEPLOYMENT.md` for Nginx/Traefik setup.

## 🔧 Common Commands

### Deploy
```bash
./deploy-production.sh
```

### View Logs
```bash
docker-compose -f docker-compose.fullstack.yml logs -f
```

### Restart Services
```bash
docker-compose -f docker-compose.fullstack.yml --env-file .env.production restart
```

### Rebuild Everything
```bash
docker-compose -f docker-compose.fullstack.yml --env-file .env.production build --no-cache
docker-compose -f docker-compose.fullstack.yml --env-file .env.production up -d
```

### Stop Services
```bash
docker-compose -f docker-compose.fullstack.yml down
```

## ✅ Verification Checklist

After deployment:

- [ ] Containers running: `docker-compose -f docker-compose.fullstack.yml ps`
- [ ] API health: `curl http://localhost:8090/api/health`
- [ ] Reverse proxy configured for both domains
- [ ] SSL certificates installed
- [ ] DNS records pointing to NAS
- [ ] External access works: `https://quangtringuyen.cloud`
- [ ] API accessible: `https://api.quangtringuyen.cloud/api/health`
- [ ] No CORS errors in browser console

## 🐛 Troubleshooting

### Frontend still calling localhost
```bash
# Rebuild frontend with production config
docker-compose -f docker-compose.fullstack.yml --env-file .env.production build frontend --no-cache
docker-compose -f docker-compose.fullstack.yml --env-file .env.production up -d frontend
```

### CORS errors
```bash
# Verify CORS settings in container
docker-compose -f docker-compose.fullstack.yml exec api env | grep CORS
```

### Can't access from external network
1. Check port forwarding (80, 443) on router
2. Check firewall rules
3. Verify DNS: `nslookup quangtringuyen.cloud`
4. Check reverse proxy is running

## 📚 Documentation

- **Full deployment guide**: `PRODUCTION_DEPLOYMENT.md`
- **Changes summary**: `CORS_AND_API_FIX.md` (in artifacts)
- **Environment examples**: `.env.production.example`

## 🔐 Security Notes

- Never commit `.env.production` to git (already in .gitignore)
- Use HTTPS only in production
- Keep SECRET_KEY secret and unique
- Regularly update Docker images
