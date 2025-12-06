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

from backend.api import auth, team, leetcode, analytics, notifications, settings
from backend.core.config import settings as config_settings

# Load environment variables
load_dotenv()

# Create FastAPI app
app = FastAPI(
    title="LeetCode Team Dashboard API",
    description="Track and analyze your team's LeetCode progress",
    version="2.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=config_settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(team.router, prefix="/api/team", tags=["Team Management"])
app.include_router(leetcode.router, prefix="/api/leetcode", tags=["LeetCode Data"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["Analytics"])
app.include_router(settings.router, prefix="/api/settings", tags=["System Settings"])
print("Loading notifications router...")
app.include_router(notifications.router, prefix="/api/notifications", tags=["Notifications"])

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "LeetCode Team Dashboard API",
        "version": "2.0.0",
        "docs": "/api/docs"
    }

@app.get("/api/health")
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
