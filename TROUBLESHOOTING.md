# Troubleshooting Guide

This document provides solutions to common issues you may encounter when running the LeetCode Team Dashboard.

## "Website is categorized as Miscellaneous or Unknown" Error

### Problem
When running the application in Docker, you may see errors like:
```
website is categorized as Miscellaneous or Unknown
```

This happens when the Docker container cannot access leetcode.com due to DNS resolution issues or network filtering.

### Solutions

#### Solution 1: Use Public DNS Servers (Recommended - Already Configured)

The [docker-compose.yml](docker-compose.yml) has been configured to use public DNS servers:
- Google DNS: 8.8.8.8, 8.8.4.4
- Cloudflare DNS: 1.1.1.1

After updating the configuration, restart the containers:

```bash
docker-compose down
docker-compose up -d --build
```

#### Solution 2: Configure Network Mode

If DNS changes don't help, you can try using the host's network directly. Edit `docker-compose.yml`:

```yaml
services:
  leetcode-dashboard:
    network_mode: "host"
    # Remove the 'ports' section when using host network
```

**Note:** When using `network_mode: "host"`, the application will be accessible at the same port on your host machine.

#### Solution 3: Use a VPN or Proxy

If you're behind a corporate firewall or in a restricted network:

1. **VPN**: Connect to a VPN that allows access to leetcode.com
2. **HTTP Proxy**: Set proxy environment variables in `.env`:

```bash
# Add to .env
HTTP_PROXY=http://your-proxy-server:port
HTTPS_PROXY=http://your-proxy-server:port
NO_PROXY=localhost,127.0.0.1
```

Then update `docker-compose.yml` to use the proxy:

```yaml
services:
  leetcode-dashboard:
    environment:
      - HTTP_PROXY=${HTTP_PROXY}
      - HTTPS_PROXY=${HTTPS_PROXY}
      - NO_PROXY=${NO_PROXY}
```

#### Solution 4: Test DNS Resolution

Test if the container can resolve leetcode.com:

```bash
# Enter the container
docker exec -it leetcode-team-dashboard bash

# Test DNS resolution
nslookup leetcode.com

# Test connection
curl -I https://leetcode.com

# Exit the container
exit
```

If DNS resolution fails, check your Docker daemon configuration at `/etc/docker/daemon.json`:

```json
{
  "dns": ["8.8.8.8", "8.8.4.4", "1.1.1.1"]
}
```

After editing, restart Docker:
```bash
sudo systemctl restart docker
```

---

## Other Common Issues

### Container Won't Start

**Check logs:**
```bash
docker-compose logs -f leetcode-dashboard
docker-compose logs -f scheduler
```

**Common causes:**
- Port 8501 already in use
- Invalid environment variables in `.env`
- Missing dependencies

**Solutions:**
1. Check if port is in use: `lsof -i :8501`
2. Verify `.env` file exists and is properly configured
3. Rebuild containers: `docker-compose up -d --build`

### S3 Connection Issues

**Error:** Cannot connect to S3 or access denied

**Solutions:**
1. Verify AWS credentials in `.env`:
   - `AWS_ACCESS_KEY_ID`
   - `AWS_SECRET_ACCESS_KEY`
   - `AWS_DEFAULT_REGION`
   - `S3_BUCKET_NAME`

2. Check S3 bucket permissions
3. Verify bucket exists in the specified region
4. Test with local storage first by leaving S3 credentials empty

### Scheduler Not Running

**Check scheduler status:**
```bash
docker-compose ps scheduler
docker-compose logs -f scheduler
```

**Common causes:**
- Scheduler container crashed
- Python errors in scheduler.py
- No team members configured

**Solutions:**
1. Check scheduler logs for errors
2. Verify team members are added in the dashboard
3. Restart scheduler: `docker-compose restart scheduler`
4. Test immediate run by setting `RUN_ON_STARTUP=true` in `.env`

### Authentication Issues

**Problem:** Cannot login or register

**Solutions:**
1. Check if `data/users.json` exists and is writable
2. Verify cookie settings in `.env`:
   - `COOKIE_NAME`
   - `COOKIE_KEY`
   - `COOKIE_EXPIRY_DAYS`

3. Clear browser cookies for localhost:8501
4. Try incognito/private browsing mode

### Data Not Persisting

**Problem:** Data is lost when containers restart

**Solutions:**
1. Verify volume mount in `docker-compose.yml`: `./data:/app/.s3_cache`
2. Check directory permissions: `ls -la ./data`
3. Ensure data directory exists: `mkdir -p ./data`
4. Check Docker volume: `docker volume ls`

---

## Getting Help

If you're still experiencing issues:

1. **Check the logs:** Most errors are visible in the logs
   ```bash
   docker-compose logs -f
   ```

2. **Verify configuration:** Ensure `.env` file is properly configured
   ```bash
   cat .env
   ```

3. **Test components individually:**
   - Test dashboard: `docker-compose up leetcode-dashboard`
   - Test scheduler: `docker-compose up scheduler`

4. **Report issues:** If the problem persists, create an issue on GitHub with:
   - Error messages from logs
   - Your `docker-compose.yml` (remove sensitive data)
   - Steps to reproduce the issue
   - System information (OS, Docker version)

---

## Useful Commands

```bash
# View all logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f leetcode-dashboard
docker-compose logs -f scheduler

# Restart all services
docker-compose restart

# Rebuild and restart
docker-compose up -d --build

# Stop all services
docker-compose down

# Stop and remove volumes
docker-compose down -v

# Check service status
docker-compose ps

# Execute command in container
docker exec -it leetcode-team-dashboard bash

# View container resource usage
docker stats
```
