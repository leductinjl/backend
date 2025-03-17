"""
Exam Data Transfer Objects (DTOs) module.

This module defines the data structures for API requests and responses 
related to exams.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, date

# Base model with common properties
class ExamBase(BaseModel):
    type_id: str = Field(..., description="ID of the exam type")
    exam_name: str = Field(..., min_length=1, max_length=200, description="Name of the exam")
    additional_info: Optional[str] = Field(None, description="Additional information about the exam")
    start_date: date = Field(..., description="Start date of the exam")
    end_date: date = Field(..., description="End date of the exam")
    scope: Optional[str] = Field(None, description="Scope of the exam (School, Provincial, National, International)")
    organizing_unit_id: str = Field(..., description="ID of the management unit responsible for the exam")
    is_active: Optional[bool] = Field(True, description="Whether the exam is active")
    exam_metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata for the exam")

# Request model for creating an exam
class ExamCreate(ExamBase):
    pass

# Request model for updating an exam
class ExamUpdate(BaseModel):
    type_id: Optional[str] = Field(None, description="ID of the exam type")
    exam_name: Optional[str] = Field(None, min_length=1, max_length=200, description="Name of the exam")
    additional_info: Optional[str] = Field(None, description="Additional information about the exam")
    start_date: Optional[date] = Field(None, description="Start date of the exam")
    end_date: Optional[date] = Field(None, description="End date of the exam")
    scope: Optional[str] = Field(None, description="Scope of the exam (School, Provincial, National, International)")
    organizing_unit_id: Optional[str] = Field(None, description="ID of the management unit responsible for the exam")
    is_active: Optional[bool] = Field(None, description="Whether the exam is active")
    exam_metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata for the exam")

# Response model for an exam
class ExamResponse(ExamBase):
    exam_id: str = Field(..., description="Unique identifier for the exam")
    created_at: datetime = Field(..., description="Timestamp when the exam was created")
    updated_at: Optional[datetime] = Field(None, description="Timestamp when the exam was last updated")
    
    class Config:
        from_attributes = True

# Enhanced response with exam type and management unit details
class ExamDetailResponse(ExamResponse):
    exam_type_name: str = Field(..., description="Name of the exam type")
    management_unit_name: str = Field(..., description="Name of the management unit")
    
    class Config:
        from_attributes = True
        
# Response model for a list of exams
class ExamListResponse(BaseModel):
    items: List[ExamDetailResponse]
    total: int = Field(..., description="Total number of exams")
    page: int = Field(..., description="Current page number")
    size: int = Field(..., description="Number of items per page") 