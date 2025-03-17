"""
Candidate Exam Data Transfer Objects (DTOs) module.

This module defines the data structures for API requests and responses 
related to candidate exams (registrations of candidates for exams).
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from enum import Enum

class ExamStatus(str, Enum):
    REGISTERED = "Registered"
    ATTENDED = "Attended"
    ABSENT = "Absent"

# Base model with common properties
class CandidateExamBase(BaseModel):
    candidate_id: str = Field(..., description="ID of the candidate")
    exam_id: str = Field(..., description="ID of the exam")
    registration_number: Optional[str] = Field(None, description="Registration number for the exam")
    registration_date: Optional[date] = Field(None, description="Date when the candidate registered for the exam")
    status: Optional[ExamStatus] = Field(None, description="Status of the exam (Registered, Attended, Absent)")
    attempt_number: Optional[int] = Field(1, description="Number of attempts for this exam")

# Request model for creating a candidate exam registration
class CandidateExamCreate(CandidateExamBase):
    pass

# Request model for updating a candidate exam registration
class CandidateExamUpdate(BaseModel):
    registration_number: Optional[str] = Field(None, description="Registration number for the exam")
    registration_date: Optional[date] = Field(None, description="Date when the candidate registered for the exam")
    status: Optional[ExamStatus] = Field(None, description="Status of the exam (Registered, Attended, Absent)")
    attempt_number: Optional[int] = Field(None, description="Number of attempts for this exam")

# Response model for a candidate exam registration
class CandidateExamResponse(CandidateExamBase):
    candidate_exam_id: str = Field(..., description="Unique identifier for the candidate exam registration")
    created_at: datetime = Field(..., description="Timestamp when the registration was created")
    updated_at: Optional[datetime] = Field(None, description="Timestamp when the registration was last updated")
    
    class Config:
        from_attributes = True

# Enhanced response with candidate and exam details
class CandidateExamDetailResponse(CandidateExamResponse):
    candidate_name: str = Field(..., description="Name of the candidate")
    exam_name: str = Field(..., description="Name of the exam")
    
    class Config:
        from_attributes = True
        
# Response model for a list of candidate exam registrations
class CandidateExamListResponse(BaseModel):
    items: List[CandidateExamDetailResponse]
    total: int = Field(..., description="Total number of candidate exam registrations")
    page: int = Field(..., description="Current page number")
    size: int = Field(..., description="Number of items per page") 