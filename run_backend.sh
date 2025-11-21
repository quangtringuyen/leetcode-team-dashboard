#!/bin/bash

# Run FastAPI Backend

echo "🚀 Starting LeetCode Team Dashboard Backend..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements_backend.txt

# Create data directory
mkdir -p data

# Run server
echo "Starting server on http://localhost:8000"
echo "API Documentation: http://localhost:8000/api/docs"
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
