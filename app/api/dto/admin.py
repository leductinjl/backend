"""
Admin Data Transfer Objects (DTOs) module.

This module defines the data structures used for admin authentication
and API responses related to admin functionality.
"""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Dict, Any

# Admin login request model
class AdminLoginRequest(BaseModel):
    """Data model for admin login requests."""
    email: EmailStr = Field(..., description="Admin email address")
    password: str = Field(..., min_length=8, description="Admin password")

# Admin login response model
class AdminLoginResponse(BaseModel):
    """Data model for admin login responses."""
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field("bearer", description="Token type")
    user_id: str = Field(..., description="Admin user ID")
    email: EmailStr = Field(..., description="Admin email address")
    name: str = Field(..., description="Admin name")
    role: str = Field("admin", description="User role")

# Admin token data model (internal use)
class AdminTokenData(BaseModel):
    """Data model for JWT token payload (internal use)."""
    sub: str  # User ID
    email: EmailStr
    name: str
    role: str = "admin"
    permissions: List[str] = []

# Admin dashboard stats model
class DashboardStats(BaseModel):
    """Data model for admin dashboard statistics."""
    candidate_count: int = Field(..., description="Total candidate count")
    exam_count: int = Field(..., description="Total exam count")
    school_count: int = Field(..., description="Total school count")
    recent_activities: Optional[List[Dict[str, Any]]] = Field(
        None, 
        description="Recent system activities"
    ) 