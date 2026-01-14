"""
LeetCode Team Dashboard - FastAPI Backend
Main application entry point
"""

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from typing import List, Optional
import os
from dotenv import load_dotenv

from backend.api import auth, team, leetcode, analytics, notifications, settings, weekly_progress, notifications_log
from backend.core.config import settings as config_settings
from backend.core.database import init_db

# Load environment variables
load_dotenv()

# Create FastAPI app
app = FastAPI(
    title="LeetCode Team Dashboard API",
    description="Track and analyze your team's LeetCode progress",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    root_path=os.getenv("ROOT_PATH", "")
)

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    """Initialize database and other startup tasks"""
    init_db()
    print("Database initialized successfully")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=config_settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers (no /api prefix since it's handled by Caddy handle_path)
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(team.router, prefix="/team", tags=["Team Management"])
app.include_router(leetcode.router, prefix="/leetcode", tags=["LeetCode Data"])
app.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])
app.include_router(settings.router, prefix="/settings", tags=["System Settings"])
app.include_router(weekly_progress.router, prefix="/analytics", tags=["Analytics"])
print("Loading notifications router...")
app.include_router(notifications.router, prefix="/notifications", tags=["Notifications"])
app.include_router(notifications_log.router, prefix="/notifications-log", tags=["Notifications Log"])

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "LeetCode Team Dashboard API",
        "version": "2.0.0",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "storage": "s3" if os.getenv("AWS_ACCESS_KEY_ID") else "local"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
