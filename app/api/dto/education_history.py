"""
Education History DTO module.

This module contains Data Transfer Objects for the Education History API.
These DTOs define the shape of data for requests and responses related to education history operations.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

# Base model with common attributes
class EducationHistoryBase(BaseModel):
    candidate_id: str = Field(..., description="ID of the candidate")
    school_id: str = Field(..., description="ID of the school")
    education_level_id: str = Field(..., description="ID of the education level")
    start_year: Optional[int] = Field(None, description="Year when education started")
    end_year: Optional[int] = Field(None, description="Year when education ended")
    academic_performance: Optional[str] = Field(None, description="Academic performance (e.g., Good, Excellent)")
    additional_info: Optional[str] = Field(None, description="Additional information about the education")

# Request model for creating a new education history entry
class EducationHistoryCreate(EducationHistoryBase):
    pass

# Request model for updating an education history entry
class EducationHistoryUpdate(BaseModel):
    school_id: Optional[str] = Field(None, description="ID of the school")
    education_level_id: Optional[str] = Field(None, description="ID of the education level")
    start_year: Optional[int] = Field(None, description="Year when education started")
    end_year: Optional[int] = Field(None, description="Year when education ended")
    academic_performance: Optional[str] = Field(None, description="Academic performance (e.g., Good, Excellent)")
    additional_info: Optional[str] = Field(None, description="Additional information about the education")

# Response model for an education history entry
class EducationHistoryResponse(EducationHistoryBase):
    education_history_id: str = Field(..., description="Unique identifier for the education history entry")
    created_at: Optional[datetime] = Field(None, description="Timestamp when the entry was created")
    updated_at: Optional[datetime] = Field(None, description="Timestamp when the entry was last updated")
    
    # Additional fields for related data
    candidate_name: Optional[str] = Field(None, description="Name of the candidate")
    school_name: Optional[str] = Field(None, description="Name of the school")
    education_level_name: Optional[str] = Field(None, description="Name of the education level")
    
    class Config:
        from_attributes = True

# Response model for a list of education history entries with pagination
class EducationHistoryListResponse(BaseModel):
    items: List[EducationHistoryResponse]
    total: int
    page: int
    size: int
    
    class Config:
        from_attributes = True 