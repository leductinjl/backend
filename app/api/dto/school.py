"""
School Data Transfer Objects (DTOs) module.

This module defines the data structures for API requests and responses 
related to schools.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

# Base model with common properties
class SchoolBase(BaseModel):
    school_name: str = Field(..., min_length=1, max_length=150, description="Name of the school")
    address: Optional[str] = Field(None, description="Address of the school")

# Request model for creating a school
class SchoolCreate(SchoolBase):
    pass

# Request model for updating a school
class SchoolUpdate(BaseModel):
    school_name: Optional[str] = Field(None, min_length=1, max_length=150, description="Name of the school")
    address: Optional[str] = Field(None, description="Address of the school")

# Response model for a school
class SchoolResponse(SchoolBase):
    school_id: str = Field(..., description="Unique identifier for the school")
    created_at: datetime = Field(..., description="Timestamp when the school was created")
    updated_at: Optional[datetime] = Field(None, description="Timestamp when the school was last updated")
    
    class Config:
        from_attributes = True
        
# Response model for a list of schools
class SchoolListResponse(BaseModel):
    items: List[SchoolResponse]
    total: int = Field(..., description="Total number of schools")
    page: int = Field(..., description="Current page number")
    size: int = Field(..., description="Number of items per page") 