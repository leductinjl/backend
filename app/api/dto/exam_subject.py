"""
Exam Subject Data Transfer Objects (DTOs) module.

This module defines the data structures for API requests and responses 
related to exam subjects (subjects that are part of an exam).
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

# Base model with common properties
class ExamSubjectBase(BaseModel):
    exam_id: str = Field(..., description="ID of the exam")
    subject_id: str = Field(..., description="ID of the subject")
    weight: Optional[float] = Field(1.0, description="Weight/importance of the subject in the exam")
    passing_score: Optional[float] = Field(None, description="Minimum score required to pass this subject")
    max_score: Optional[float] = Field(100.0, description="Maximum possible score for this subject")
    is_required: Optional[bool] = Field(True, description="Whether this subject is required to pass the exam")
    exam_date: Optional[datetime] = Field(None, description="Date and time when this subject will be examined")
    duration_minutes: Optional[int] = Field(None, description="Duration of the exam for this subject in minutes")
    subject_metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata for the exam subject")

# Request model for creating an exam subject
class ExamSubjectCreate(ExamSubjectBase):
    pass

# Request model for updating an exam subject
class ExamSubjectUpdate(BaseModel):
    weight: Optional[float] = Field(None, description="Weight/importance of the subject in the exam")
    passing_score: Optional[float] = Field(None, description="Minimum score required to pass this subject")
    max_score: Optional[float] = Field(None, description="Maximum possible score for this subject")
    is_required: Optional[bool] = Field(None, description="Whether this subject is required to pass the exam")
    exam_date: Optional[datetime] = Field(None, description="Date and time when this subject will be examined")
    duration_minutes: Optional[int] = Field(None, description="Duration of the exam for this subject in minutes")
    subject_metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata for the exam subject")

# Response model for an exam subject
class ExamSubjectResponse(ExamSubjectBase):
    exam_subject_id: str = Field(..., description="Unique identifier for the exam subject")
    created_at: datetime = Field(..., description="Timestamp when the exam subject was created")
    updated_at: Optional[datetime] = Field(None, description="Timestamp when the exam subject was last updated")
    
    class Config:
        from_attributes = True

# Enhanced response with exam and subject details
class ExamSubjectDetailResponse(ExamSubjectResponse):
    exam_name: str = Field(..., description="Name of the exam")
    subject_name: str = Field(..., description="Name of the subject")
    subject_code: Optional[str] = Field(None, description="Code of the subject")
    
    class Config:
        from_attributes = True
        
# Response model for a list of exam subjects
class ExamSubjectListResponse(BaseModel):
    items: List[ExamSubjectDetailResponse]
    total: int = Field(..., description="Total number of exam subjects")
    page: int = Field(..., description="Current page number")
    size: int = Field(..., description="Number of items per page") 