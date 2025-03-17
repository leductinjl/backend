"""
Subject Data Transfer Objects (DTOs) module.

This module defines the data structures for API requests and responses 
related to subjects (academic courses).
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

# Base model with common properties
class SubjectBase(BaseModel):
    subject_name: str = Field(..., min_length=1, max_length=100, description="Name of the subject")
    description: Optional[str] = Field(None, description="Description of the subject")

# Request model for creating a subject
class SubjectCreate(SubjectBase):
    pass

# Request model for updating a subject
class SubjectUpdate(BaseModel):
    subject_name: Optional[str] = Field(None, min_length=1, max_length=100, description="Name of the subject")
    description: Optional[str] = Field(None, description="Description of the subject")

# Response model for a subject
class SubjectResponse(SubjectBase):
    subject_id: str = Field(..., description="Unique identifier for the subject")
    created_at: datetime = Field(..., description="Timestamp when the subject was created")
    updated_at: Optional[datetime] = Field(None, description="Timestamp when the subject was last updated")
    
    class Config:
        from_attributes = True
        
# Response model for a list of subjects
class SubjectListResponse(BaseModel):
    items: List[SubjectResponse]
    total: int = Field(..., description="Total number of subjects")
    page: int = Field(..., description="Current page number")
    size: int = Field(..., description="Number of items per page") 