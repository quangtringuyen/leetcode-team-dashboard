#!/bin/bash
# Start backend with S3 configuration

cd "$(dirname "$0")"

# Load environment variables from .env
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | grep -v '^\s*$' | xargs)
fi

# Start the backend from project root (so imports work)
echo "Starting backend with S3 storage..."
echo "S3 Bucket: $S3_BUCKET_NAME"
echo "S3 Prefix: $S3_PREFIX"

python3 -m uvicorn backend.main:app --reload --port 8090 --host 0.0.0.0
