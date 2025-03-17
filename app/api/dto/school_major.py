"""
School-Major Data Transfer Objects (DTOs) module.

This module defines the data structures for API requests and responses 
related to the relationship between schools and majors.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

# Base model with common properties
class SchoolMajorBase(BaseModel):
    school_id: str = Field(..., description="ID of the school")
    major_id: str = Field(..., description="ID of the major")
    start_year: Optional[int] = Field(None, description="Year when the school started offering this major")
    is_active: bool = Field(True, description="Whether the major is still actively offered by the school")
    additional_info: Optional[str] = Field(None, description="Additional information about the school-major relationship")

# Request model for creating a school-major relationship
class SchoolMajorCreate(SchoolMajorBase):
    pass

# Request model for updating a school-major relationship
class SchoolMajorUpdate(BaseModel):
    start_year: Optional[int] = Field(None, description="Year when the school started offering this major")
    is_active: Optional[bool] = Field(None, description="Whether the major is still actively offered by the school")
    additional_info: Optional[str] = Field(None, description="Additional information about the school-major relationship")

# Response model for a school-major relationship
class SchoolMajorResponse(SchoolMajorBase):
    school_major_id: str = Field(..., description="Unique identifier for the school-major relationship")
    created_at: datetime = Field(..., description="Timestamp when the relationship was created")
    updated_at: Optional[datetime] = Field(None, description="Timestamp when the relationship was last updated")
    
    class Config:
        from_attributes = True

# Enhanced response with school and major details
class SchoolMajorDetailResponse(SchoolMajorResponse):
    school_name: str = Field(..., description="Name of the school")
    major_name: str = Field(..., description="Name of the major")
    
    class Config:
        from_attributes = True
        
# Response model for a list of school-major relationships
class SchoolMajorListResponse(BaseModel):
    items: List[SchoolMajorDetailResponse]
    total: int = Field(..., description="Total number of school-major relationships")
    page: int = Field(..., description="Current page number")
    size: int = Field(..., description="Number of items per page") 