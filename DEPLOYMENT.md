# Docker Deployment Guide

This guide will help you deploy the LeetCode Team Dashboard using Docker on NAS, VPS, or any server with Docker support.

## Prerequisites

- Docker installed on your server/NAS
- Docker Compose installed (recommended)
- Terminal/SSH access
- AWS S3 bucket (optional - for cloud storage)

## Important: Environment Configuration

Before deploying, you **MUST** configure the `.env` file with your credentials:

1. **Copy the example file:**
   ```bash
   cp .env.example .env
   ```

2. **Edit `.env` with your credentials:**
   ```bash
   nano .env  # or use your preferred editor
   ```

The `.env` file contains:
- AWS credentials for S3 storage (optional)
- Authentication configuration
- Scheduler settings

**Security Note:** Never commit `.env` to version control. The `.gitignore` file already excludes it.

## Quick Start

### Using Docker Compose (Recommended)

1. **Clone or transfer the repository**
   ```bash
   git clone <your-repo-url>
   cd leetcode-team-dashboard
   # Or upload the directory to your server
   ```

2. **Configure environment variables**
   ```bash
   cp .env.example .env
   nano .env  # Edit with your credentials
   ```

3. **Create data directory for persistent storage**
   ```bash
   mkdir -p data
   ```

4. **Start the application**
   ```bash
   docker-compose up -d
   ```

5. **Access the dashboard**
   - Open your browser: `http://your-server-ip:8501`
   - Create your first account via the registration form

### Using Docker CLI

If you prefer using Docker commands directly:

```bash
# Build the image
docker build -t leetcode-dashboard .

# Run the dashboard container
docker run -d \
  --name leetcode-dashboard \
  -p 8501:8501 \
  -v $(pwd)/data:/app/.s3_cache \
  --env-file .env \
  --dns 8.8.8.8 \
  --dns 8.8.4.4 \
  --restart unless-stopped \
  leetcode-dashboard

# Run the scheduler container
docker run -d \
  --name leetcode-scheduler \
  -v $(pwd)/data:/app/.s3_cache \
  --env-file .env \
  --dns 8.8.8.8 \
  --dns 8.8.4.4 \
  --restart unless-stopped \
  leetcode-dashboard \
  python scheduler.py
```

## Configuration

### Port Configuration

By default, the app runs on port `8501`. To change the port:

**Docker Compose:**
```yaml
ports:
  - "8080:8501"  # Access via port 8080
```

**Docker CLI:**
```bash
docker run -d -p 8080:8501 ...
```

### AWS S3 Configuration (Optional)

AWS S3 credentials are configured in `.env`. To enable S3 storage:

1. Edit `.env` and configure:
   ```bash
   AWS_ACCESS_KEY_ID=your_key
   AWS_SECRET_ACCESS_KEY=your_secret
   AWS_DEFAULT_REGION=ap-southeast-1
   S3_BUCKET_NAME=your-bucket-name
   S3_PREFIX=prod
   ```

2. Restart the containers:
   ```bash
   docker-compose down
   docker-compose up -d
   ```

**Note:** If S3 credentials are not provided, the app will use local file storage in the `./data` directory.

### Persistent Data Storage

Data is stored in the `./data` directory which is mounted to the container. This ensures your team data persists across container restarts.

**Important:** Make sure this directory has proper permissions:
```bash
chmod -R 755 data
```

## Management Commands

### View logs
```bash
docker-compose logs -f
# or
docker logs -f leetcode-dashboard
```

### Stop the application
```bash
docker-compose down
# or
docker stop leetcode-dashboard
```

### Restart the application
```bash
docker-compose restart
# or
docker restart leetcode-dashboard
```

### Update the application
```bash
# Pull latest code changes
git pull

# Rebuild and restart
docker-compose down
docker-compose up -d --build
```

### Remove everything (including data)
```bash
docker-compose down -v
rm -rf data/
```

## NAS-Specific Setup

### Synology NAS

1. **Using Container Manager (GUI)**
   - Open Container Manager
   - Go to "Project" tab
   - Click "Create"
   - Select your project folder
   - Choose `docker-compose.yml`
   - Click "Start"

2. **Accessing via DSM Reverse Proxy**
   - Open DSM > Control Panel > Login Portal > Advanced > Reverse Proxy
   - Click "Create"
   - Configure:
     - Source: `leetcode` (subdomain) or custom URL
     - Destination: `http://localhost:8501`

### QNAP NAS

1. **Using Container Station**
   - Open Container Station
   - Go to "Create Container"
   - Select "Create Application"
   - Paste the `docker-compose.yml` content
   - Click "Create"

### TrueNAS/FreeNAS

1. **Using Jails or Docker plugin**
   - Install Docker via plugins
   - Follow the Docker Compose quick start steps

## Troubleshooting

### "Website is categorized as Miscellaneous or Unknown" Error

This error occurs when the container cannot access leetcode.com due to DNS or network issues.

**Solution:** The `docker-compose.yml` has been configured with public DNS servers (Google DNS and Cloudflare DNS) to fix this issue. If you still encounter problems:

1. **Test network connectivity:**
   ```bash
   # Run the network test script inside the container
   docker exec -it leetcode-team-dashboard python test_network.py
   ```

2. **Check DNS resolution:**
   ```bash
   docker exec -it leetcode-team-dashboard nslookup leetcode.com
   ```

3. **If DNS fails, manually set DNS in docker-compose.yml:**
   ```yaml
   services:
     leetcode-dashboard:
       dns:
         - 8.8.8.8
         - 8.8.4.4
         - 1.1.1.1
   ```

4. **For more solutions, see [TROUBLESHOOTING.md](TROUBLESHOOTING.md)**

### Container won't start
```bash
# Check logs
docker-compose logs

# Check if port is already in use
netstat -tulpn | grep 8501
```

### Permission issues with data directory
```bash
# Fix permissions
sudo chown -R 1000:1000 data/
chmod -R 755 data/
```

### Can't access from other devices
- Check NAS firewall settings
- Ensure port 8501 is open
- Verify the container is running: `docker ps`

### Memory issues on NAS
```yaml
# Add memory limits to docker-compose.yml
services:
  leetcode-dashboard:
    mem_limit: 512m
    memswap_limit: 1g
```

## Security Recommendations

1. **Use reverse proxy** (nginx, Traefik) for HTTPS
2. **Set up authentication** if exposing to internet
3. **Regular backups** of the `data/` directory
4. **Keep Docker images updated**:
   ```bash
   docker-compose pull
   docker-compose up -d
   ```

## Resource Requirements

- **CPU:** Minimal (0.5 cores recommended)
- **RAM:** 256MB-512MB
- **Storage:** ~500MB for image + data

## Support

For issues specific to this application, check the logs:
```bash
docker-compose logs -f leetcode-dashboard
```

For Docker-related issues on your NAS, consult your NAS manufacturer's documentation.
