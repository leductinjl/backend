"""
Admin authentication module.

This module provides endpoint handlers for admin authentication functionality
including login, registration and token refresh operations. These functions
are used by the admin router.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import jwt
import passlib.hash
from sqlalchemy import select, and_
import pytz

from app.infrastructure.database.connection import get_db
from app.config import settings
from app.api.dto.admin import AdminLoginRequest, AdminLoginResponse, AdminTokenData, AdminRegisterRequest
from app.domain.models.user import User
from app.domain.models.invitation import Invitation
from app.domain.models.security_log import SecurityLog
from app.services.id_service import generate_model_id

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
        expire = datetime.now(pytz.UTC) + expires_delta
    else:
        expire = datetime.now(pytz.UTC) + timedelta(minutes=30)  # Default 30 minutes
    
    to_encode.update({"exp": expire})
    
    # Create JWT token
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.SECRET_KEY, 
        algorithm="HS256"
    )
    
    return encoded_jwt

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.
    
    Args:
        plain_password: The plain-text password
        hashed_password: The hashed password to check against
        
    Returns:
        bool: True if password matches, False otherwise
    """
    return passlib.hash.bcrypt.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """
    Hash a password for storage.
    
    Args:
        password: The plain-text password to hash
        
    Returns:
        str: Hashed password
    """
    return passlib.hash.bcrypt.hash(password)

async def admin_register(
    register_data: AdminRegisterRequest,
    db: AsyncSession = Depends(get_db)
) -> AdminLoginResponse:
    """
    Register a new admin user.
    
    This endpoint creates a new admin user in the system with the provided
    credentials and returns an access token. Requires a valid invitation code.
    
    Args:
        register_data: Registration information
        db: Database session
        
    Returns:
        AdminLoginResponse: Login response with access token
        
    Raises:
        HTTPException: If email already exists or invitation code is invalid
    """
    # Check if email already exists
    user_result = await db.execute(
        select(User).where(User.email == register_data.email)
    )
    if user_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Validate invitation code
    invitation_result = await db.execute(
        select(Invitation).where(
            and_(
                Invitation.code == register_data.invitation_code,
                Invitation.is_used == False,
                Invitation.revoked == False
            )
        )
    )
    invitation = invitation_result.scalar_one_or_none()
    
    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or already used invitation code"
        )
    
    # Check if invitation has expired
    if invitation.expires_at and invitation.expires_at < datetime.now(pytz.UTC):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invitation code has expired"
        )
    
    # Check if invitation is restricted to specific email
    if invitation.email and invitation.email != register_data.email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This invitation code is not valid for your email"
        )
    
    # Create new user
    new_user = User(
        user_id=generate_model_id("User"),
        email=register_data.email,
        name=register_data.name,
        password_hash=get_password_hash(register_data.password),
        role="admin",
        role_id=invitation.role_id,  # Use the role ID from invitation if available
        is_active=True,
        created_at=datetime.now(pytz.UTC)
    )
    
    # Mark invitation as used
    invitation.is_used = True
    invitation.used_by = new_user.user_id
    invitation.used_at = datetime.now(pytz.UTC)
    
    # Create security log
    log_entry = SecurityLog(
        log_id=generate_model_id("SecurityLog"),
        user_id=new_user.user_id,
        action="user_register",
        ip_address="0.0.0.0",  # Replace with actual IP address if available
        user_agent="",  # Replace with actual user agent if available
        description=f"User registered with email {new_user.email}",
        timestamp=datetime.now(pytz.UTC),
        success=True
    )
    
    # Save changes to database
    db.add(new_user)
    db.add(invitation)
    db.add(log_entry)
    await db.commit()
    await db.refresh(new_user)
    
    # Create token data
    token_data = AdminTokenData(
        sub=new_user.user_id,
        email=new_user.email,
        name=new_user.name,
        role=new_user.role,
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
        user_id=new_user.user_id,
        email=new_user.email,
        name=new_user.name,
        role=new_user.role
    )

async def admin_login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
) -> AdminLoginResponse:
    """
    Authenticate an admin user.
    
    This endpoint authenticates admin credentials against the database
    and returns an access token if valid.
    
    Args:
        form_data: OAuth2 form with username (email) and password
        db: Database session
        
    Returns:
        AdminLoginResponse: Login response with access token
        
    Raises:
        HTTPException: If credentials are invalid
    """
    # Get user from database
    result = await db.execute(
        select(User).where(User.email == form_data.username)
    )
    user = result.scalar_one_or_none()
    
    # Prepare success status to track authentication outcome
    success = False
    error_msg = "Invalid credentials"
    
    try:
        # Verify user exists and password is correct
        if not user or not verify_password(form_data.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Verify user is active
        if not user.is_active:
            error_msg = "User account is inactive"
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is inactive",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Handle account lockout if too many failed attempts
        if user.locked_until and user.locked_until > datetime.now(pytz.UTC):
            error_msg = "Account is temporarily locked"
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account is temporarily locked. Try again later.",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        # Authentication successful
        success = True
        
        # Reset failed login attempts
        user.failed_login_attempts = 0
        user.last_login = datetime.now(pytz.UTC)
        user.last_login_ip = "0.0.0.0"  # Replace with actual IP address if available
        
        # Create token data
        token_data = AdminTokenData(
            sub=user.user_id,
            email=user.email,
            name=user.name,
            role=user.role,
            permissions=["candidates:manage", "exams:manage", "schools:manage"]
        )
        
        # Create access token
        access_token = create_jwt_token(
            data=token_data,
            expires_delta=timedelta(hours=1)  # Token valid for 1 hour
        )
        
        # Log the login attempt
        log_entry = SecurityLog(
            log_id=generate_model_id("SecurityLog"),
            user_id=user.user_id,
            action="user_login",
            ip_address="0.0.0.0",  # Replace with actual IP address
            user_agent="",         # Replace with actual user agent
            description="Successful login",
            timestamp=datetime.now(pytz.UTC),
            success=True
        )
        
        db.add(log_entry)
        await db.commit()
        
        # Return login response
        return AdminLoginResponse(
            access_token=access_token,
            token_type="bearer",
            user_id=user.user_id,
            email=user.email,
            name=user.name,
            role=user.role
        )
        
    except HTTPException as e:
        # Increment failed login attempts if user exists
        if user:
            user.failed_login_attempts = (user.failed_login_attempts or 0) + 1
            
            # Lock account after 5 failed attempts
            if user.failed_login_attempts >= 5:
                user.locked_until = datetime.now(pytz.UTC) + timedelta(minutes=15)
                error_msg = "Too many failed attempts. Account locked temporarily."
        
        # Log failed login attempt
        log_entry = SecurityLog(
            log_id=generate_model_id("SecurityLog"),
            user_id=user.user_id if user else None,
            action="user_login",
            ip_address="0.0.0.0",  # Replace with actual IP address
            user_agent="",         # Replace with actual user agent
            description=f"Failed login: {error_msg}",
            timestamp=datetime.now(pytz.UTC),
            success=False
        )
        
        db.add(log_entry)
        await db.commit()
        
        # Re-raise the exception
        raise 