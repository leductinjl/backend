"""
Degree DTO module.

This module contains Data Transfer Objects for the Degree API.
These DTOs define the shape of data for requests and responses related to degree operations.
"""

from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List
from datetime import datetime

# Base model with common attributes
class DegreeBase(BaseModel):
    major_id: str = Field(..., description="ID of the major associated with this degree")
    start_year: Optional[int] = Field(None, description="Year when the degree program started")
    end_year: Optional[int] = Field(None, description="Year when the degree was completed")
    academic_performance: Optional[str] = Field(None, description="Academic performance (e.g., Good, Excellent)")
    degree_image_url: Optional[str] = Field(None, description="URL to the image of the degree certificate")
    additional_info: Optional[str] = Field(None, description="Additional information about the degree")

# Request model for creating a new degree
class DegreeCreate(DegreeBase):
    pass

# Request model for updating a degree
class DegreeUpdate(BaseModel):
    major_id: Optional[str] = Field(None, description="ID of the major associated with this degree")
    start_year: Optional[int] = Field(None, description="Year when the degree program started")
    end_year: Optional[int] = Field(None, description="Year when the degree was completed")
    academic_performance: Optional[str] = Field(None, description="Academic performance (e.g., Good, Excellent)")
    degree_image_url: Optional[str] = Field(None, description="URL to the image of the degree certificate")
    additional_info: Optional[str] = Field(None, description="Additional information about the degree")

# Response model for a degree
class DegreeResponse(DegreeBase):
    degree_id: str = Field(..., description="Unique identifier for the degree")
    created_at: Optional[datetime] = Field(None, description="Timestamp when the degree was created")
    updated_at: Optional[datetime] = Field(None, description="Timestamp when the degree was last updated")
    
    # Additional fields for related data
    major_name: Optional[str] = Field(None, description="Name of the major associated with this degree")
    candidate_id: Optional[str] = Field(None, description="ID of the candidate who earned this degree")
    candidate_name: Optional[str] = Field(None, description="Name of the candidate who earned this degree")
    
    class Config:
        from_attributes = True

# Response model for a list of degrees with pagination
class DegreeListResponse(BaseModel):
    items: List[DegreeResponse]
    total: int
    page: int
    size: int
    
    class Config:
        from_attributes = True 