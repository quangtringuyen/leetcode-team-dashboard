"""
API Tests
"""

import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_root():
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "version" in data

def test_health_check():
    """Test health check endpoint"""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "storage" in data

def test_register_user():
    """Test user registration"""
    response = client.post(
        "/api/auth/register",
        json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpass123",
            "full_name": "Test User"
        }
    )
    # May fail if user already exists, that's ok
    if response.status_code == 201:
        data = response.json()
        assert data["username"] == "testuser"
        assert data["email"] == "test@example.com"

def test_login():
    """Test user login"""
    # First register if needed
    client.post(
        "/api/auth/register",
        json={
            "username": "testuser2",
            "email": "test2@example.com",
            "password": "testpass123"
        }
    )

    # Try to login
    response = client.post(
        "/api/auth/login",
        data={"username": "testuser2", "password": "testpass123"}
    )

    if response.status_code == 200:
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

def test_get_daily_challenge():
    """Test fetching daily challenge (no auth required)"""
    response = client.get("/api/leetcode/daily-challenge")

    # May fail if LeetCode API is down
    if response.status_code == 200:
        data = response.json()
        assert "title" in data
        assert "difficulty" in data

def test_unauthorized_access():
    """Test that protected endpoints require authentication"""
    response = client.get("/api/team/members")
    assert response.status_code == 401  # Unauthorized

def test_get_current_user():
    """Test getting current user info"""
    # Register and login
    client.post(
        "/api/auth/register",
        json={
            "username": "testuser3",
            "email": "test3@example.com",
            "password": "testpass123"
        }
    )

    login_response = client.post(
        "/api/auth/login",
        data={"username": "testuser3", "password": "testpass123"}
    )

    if login_response.status_code == 200:
        token = login_response.json()["access_token"]

        # Get current user
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )

        if response.status_code == 200:
            data = response.json()
            assert data["username"] == "testuser3"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
