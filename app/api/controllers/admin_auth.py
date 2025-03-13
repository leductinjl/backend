"""
Admin authentication controller module.

This module provides endpoints for admin authentication functionality
including login and token refresh operations.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta
import jwt
from typing import Optional

from app.infrastructure.database.connection import get_db
from app.config import settings
from app.api.dto.admin import AdminLoginRequest, AdminLoginResponse, AdminTokenData

router = APIRouter()

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_PREFIX}/admin/login")

def create_jwt_token(data: AdminTokenData, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT token with the provided data.
    
    Args:
        data: Token payload data
        expires_delta: Token expiration time
        
    Returns:
        str: JWT token
    """
    to_encode = data.dict()
    
    # Set expiration time
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=30)  # Default 30 minutes
    
    to_encode.update({"exp": expire})
    
    # Create JWT token
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.SECRET_KEY, 
        algorithm="HS256"
    )
    
    return encoded_jwt

@router.post("/login", response_model=AdminLoginResponse, summary="Admin Login")
async def admin_login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Authenticate an admin user.
    
    This endpoint authenticates admin credentials and returns
    an access token if valid.
    
    Note: In a real application, you would verify credentials against
    the database. This implementation is simplified for demo purposes.
    
    Args:
        form_data: OAuth2 form with username (email) and password
        
    Returns:
        AdminLoginResponse: Login response with access token
        
    Raises:
        HTTPException: If credentials are invalid
    """
    # This is a simplified example - in production, check against database
    # For demo purposes, we'll use hardcoded credentials
    DEMO_ADMIN = {
        "email": "admin@example.com",
        "password": "adminpassword123",
        "user_id": "admin-001",
        "name": "System Administrator"
    }
    
    # Verify credentials
    if form_data.username != DEMO_ADMIN["email"] or form_data.password != DEMO_ADMIN["password"]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create token data
    token_data = AdminTokenData(
        sub=DEMO_ADMIN["user_id"],
        email=DEMO_ADMIN["email"],
        name=DEMO_ADMIN["name"],
        role="admin",
        permissions=["candidates:manage", "exams:manage", "schools:manage"]
    )
    
    # Create access token
    access_token = create_jwt_token(
        data=token_data,
        expires_delta=timedelta(hours=1)  # Token valid for 1 hour
    )
    
    # Return login response
    return AdminLoginResponse(
        access_token=access_token,
        token_type="bearer",
        user_id=DEMO_ADMIN["user_id"],
        email=DEMO_ADMIN["email"],
        name=DEMO_ADMIN["name"],
        role="admin"
    ) 