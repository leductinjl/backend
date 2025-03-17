"""
Major Data Transfer Objects (DTOs) module.

This module defines the data structures for API requests and responses 
related to majors (fields of study).
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

# Base model with common properties
class MajorBase(BaseModel):
    major_name: str = Field(..., min_length=1, max_length=150, description="Name of the major")
    ministry_code: Optional[str] = Field(None, max_length=20, description="Ministry's major code (if any)")
    description: Optional[str] = Field(None, description="Description of the major")

# Request model for creating a major
class MajorCreate(MajorBase):
    pass

# Request model for updating a major
class MajorUpdate(BaseModel):
    major_name: Optional[str] = Field(None, min_length=1, max_length=150, description="Name of the major")
    ministry_code: Optional[str] = Field(None, max_length=20, description="Ministry's major code")
    description: Optional[str] = Field(None, description="Description of the major")

# Response model for a major
class MajorResponse(MajorBase):
    major_id: str = Field(..., description="Unique identifier for the major")
    created_at: datetime = Field(..., description="Timestamp when the major was created")
    updated_at: Optional[datetime] = Field(None, description="Timestamp when the major was last updated")
    
    class Config:
        from_attributes = True
        
# Response model for a list of majors
class MajorListResponse(BaseModel):
    items: List[MajorResponse]
    total: int = Field(..., description="Total number of majors")
    page: int = Field(..., description="Current page number")
    size: int = Field(..., description="Number of items per page") 