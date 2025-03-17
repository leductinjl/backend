"""
Exam Type Data Transfer Objects (DTOs) module.

This module defines the data structures for API requests and responses 
related to exam types.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

# Base model with common properties
class ExamTypeBase(BaseModel):
    type_name: str = Field(..., min_length=1, max_length=100, description="Name of the exam type")
    description: Optional[str] = Field(None, description="Description of the exam type")
    is_active: Optional[bool] = Field(True, description="Whether the exam type is active")

# Request model for creating an exam type
class ExamTypeCreate(ExamTypeBase):
    pass

# Request model for updating an exam type
class ExamTypeUpdate(BaseModel):
    type_name: Optional[str] = Field(None, min_length=1, max_length=100, description="Name of the exam type")
    description: Optional[str] = Field(None, description="Description of the exam type")
    is_active: Optional[bool] = Field(None, description="Whether the exam type is active")

# Response model for an exam type
class ExamTypeResponse(ExamTypeBase):
    type_id: str = Field(..., description="Unique identifier for the exam type")
    created_at: datetime = Field(..., description="Timestamp when the exam type was created")
    updated_at: Optional[datetime] = Field(None, description="Timestamp when the exam type was last updated")
    
    class Config:
        from_attributes = True
        
# Response model for a list of exam types
class ExamTypeListResponse(BaseModel):
    items: List[ExamTypeResponse]
    total: int = Field(..., description="Total number of exam types")
    page: int = Field(..., description="Current page number")
    size: int = Field(..., description="Number of items per page") 