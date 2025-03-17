"""
Education Level DTO module.

This module defines Data Transfer Objects for education level data,
used for validation and serialization in the API.
"""

from pydantic import BaseModel, Field
from typing import Optional, List

class EducationLevelBase(BaseModel):
    """Base DTO with common fields for education level"""
    code: str = Field(..., min_length=2, max_length=20, description="Unique code for the education level")
    name: str = Field(..., min_length=2, max_length=100, description="Display name of the education level")
    description: Optional[str] = Field(None, description="Detailed description of the education level")
    display_order: Optional[int] = Field(None, description="Order for display purposes")

class EducationLevelCreate(EducationLevelBase):
    """DTO for creating a new education level"""
    pass

class EducationLevelUpdate(BaseModel):
    """DTO for updating an education level"""
    code: Optional[str] = Field(None, min_length=2, max_length=20, description="Unique code for the education level")
    name: Optional[str] = Field(None, min_length=2, max_length=100, description="Display name of the education level")
    description: Optional[str] = Field(None, description="Detailed description of the education level")
    display_order: Optional[int] = Field(None, description="Order for display purposes")

class EducationLevelResponse(EducationLevelBase):
    """DTO for education level in responses"""
    education_level_id: str = Field(..., description="Unique identifier for the education level")
    
    class Config:
        from_attributes = True

class EducationLevelListResponse(BaseModel):
    """DTO for paginated list of education levels"""
    items: List[EducationLevelResponse]
    total: int
    page: int
    size: int
    
    class Config:
        from_attributes = True 