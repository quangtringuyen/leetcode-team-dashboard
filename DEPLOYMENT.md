# Docker Deployment Guide for NAS

This guide will help you deploy the LeetCode Team Dashboard on your NAS using Docker.

## Prerequisites

- Docker installed on your NAS
- Docker Compose installed (optional but recommended)
- Access to your NAS terminal/SSH
- AWS S3 bucket (if using S3 storage)

## Important: Secrets Configuration

Before deploying, you **MUST** configure the `.streamlit/secrets.toml` file with your credentials. This file contains:
- AWS credentials for S3 storage
- Authentication configuration

The secrets file is already created with the following structure:
```toml
[aws]
AWS_ACCESS_KEY_ID = "your_key"
AWS_SECRET_ACCESS_KEY = "your_secret"
AWS_DEFAULT_REGION = "ap-southeast-1"
S3_BUCKET = "leetcode-team-dashboard"
S3_PREFIX = "prod"

[auth]
COOKIE_NAME = "leetdash_auth"
COOKIE_KEY = "leetcode_dashboard_signature_key_2024"
COOKIE_EXPIRY_DAYS = 30
```

**Security Note:** Never commit `secrets.toml` to version control. Keep it secure on your NAS.

## Quick Start

### Using Docker Compose (Recommended)

1. **Transfer files to your NAS**
   ```bash
   # Upload the entire project directory to your NAS
   # Example path: /volume1/docker/leetcode-dashboard/
   ```

2. **Navigate to the project directory**
   ```bash
   cd /volume1/docker/leetcode-dashboard/
   ```

3. **Verify secrets file exists**
   ```bash
   # Check if secrets file exists
   ls -la .streamlit/secrets.toml

   # The file should already be configured with your AWS credentials
   # If you need to edit it:
   # nano .streamlit/secrets.toml
   ```

4. **Create data directory for persistent storage**
   ```bash
   mkdir -p data
   ```

5. **Start the application**
   ```bash
   docker-compose up -d
   ```

6. **Access the dashboard**
   - Open your browser and navigate to: `http://your-nas-ip:8501`
   - Default login: `admin` / `admin123` (change this in production!)

### Using Docker CLI

If you prefer using Docker commands directly:

```bash
# Build the image
docker build -t leetcode-dashboard .

# Run the container
docker run -d \
  --name leetcode-dashboard \
  -p 8501:8501 \
  -v $(pwd)/data:/app/.s3_cache \
  -v $(pwd)/.streamlit/secrets.toml:/app/.streamlit/secrets.toml:ro \
  --restart unless-stopped \
  leetcode-dashboard
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

### AWS S3 Configuration

AWS S3 credentials are configured in `.streamlit/secrets.toml`. The current configuration uses:
- **Bucket:** `leetcode-team-dashboard`
- **Region:** `ap-southeast-1`
- **Prefix:** `prod`

All team data, snapshots, and configurations are automatically stored in S3.

To modify S3 settings:
1. Edit `.streamlit/secrets.toml`
2. Update the `[aws]` section
3. Restart the container:
   ```bash
   docker-compose down
   docker-compose up -d
   ```

**Note:** The app will fall back to local storage if S3 is unavailable.

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
