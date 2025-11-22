"""
Authentication endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import timedelta

from backend.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    get_current_user
)
from backend.core.storage import read_json, write_json
from backend.core.config import settings

router = APIRouter()

class UserRegister(BaseModel):
    username: str
    email: EmailStr
    password: str
    full_name: Optional[str] = None

class UserResponse(BaseModel):
    username: str
    email: str
    full_name: Optional[str] = None

class Token(BaseModel):
    access_token: str
    token_type: str

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user: UserRegister):
    """Register a new user"""
    # Load existing users
    users = read_json(settings.USERS_FILE, default={})

    # Check if user exists
    if user.username in users:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )

    # Check if email exists
    if any(u.get("email") == user.email for u in users.values()):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Create new user
    users[user.username] = {
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name,
        "hashed_password": get_password_hash(user.password),
        "disabled": False
    }

    # Save users
    write_json(settings.USERS_FILE, users)

    return UserResponse(
        username=user.username,
        email=user.email,
        full_name=user.full_name
    )

@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Login and get access token"""
    print(f"[AUTH] Login attempt for username: {form_data.username}")

    # Load users
    users = read_json(settings.USERS_FILE, default={})
    print(f"[AUTH] Loaded {len(users)} users from database")

    user = users.get(form_data.username)
    if not user:
        print(f"[AUTH] User '{form_data.username}' not found")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    print(f"[AUTH] User found: {form_data.username}")

    if not verify_password(form_data.password, user["hashed_password"]):
        print(f"[AUTH] Password verification failed for user: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    print(f"[AUTH] Password verified for user: {form_data.username}")

    if user.get("disabled", False):
        print(f"[AUTH] User account disabled: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User account is disabled"
        )

    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"]},
        expires_delta=access_token_expires
    )

    print(f"[AUTH] Login successful for user: {form_data.username}")

    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """Get current user information"""
    users = read_json(settings.USERS_FILE, default={})
    user = users.get(current_user["username"])

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return UserResponse(
        username=user["username"],
        email=user["email"],
        full_name=user.get("full_name")
    )
