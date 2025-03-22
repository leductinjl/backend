"""
Candidate Exam Subject DTO module.

This module contains Data Transfer Objects for the Candidate Exam Subject API,
used for validation and serialization of candidate exam subject data.
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
import enum

class RegistrationStatusEnum(str, enum.Enum):
    """Enum for candidate exam subject registration status."""
    REGISTERED = "REGISTERED"
    CONFIRMED = "CONFIRMED"
    WITHDRAWN = "WITHDRAWN"
    ABSENT = "ABSENT"
    COMPLETED = "COMPLETED"

class CandidateExamSubjectBase(BaseModel):
    """Base model with common attributes for candidate exam subjects."""
    candidate_exam_id: str = Field(..., description="ID of the candidate exam association")
    exam_subject_id: str = Field(..., description="ID of the exam subject")
    status: Optional[str] = Field(RegistrationStatusEnum.REGISTERED, description="Registration status for this subject")
    is_required: Optional[bool] = Field(True, description="Whether this subject is mandatory for the candidate")
    notes: Optional[str] = Field(None, description="Additional notes about this registration")

class CandidateExamSubjectCreate(CandidateExamSubjectBase):
    """Model for creating a new candidate exam subject registration."""
    pass

class CandidateExamSubjectUpdate(BaseModel):
    """Model for updating a candidate exam subject registration."""
    status: Optional[str] = Field(None, description="Registration status for this subject")
    is_required: Optional[bool] = Field(None, description="Whether this subject is mandatory for the candidate")
    notes: Optional[str] = Field(None, description="Additional notes about this registration")

class CandidateExamSubjectResponse(CandidateExamSubjectBase):
    """Model for candidate exam subject in API responses."""
    candidate_exam_subject_id: str = Field(..., description="Unique identifier for the candidate exam subject")
    registration_date: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    # Additional fields from related entities
    candidate_id: Optional[str] = Field(None, description="ID of the candidate")
    candidate_name: Optional[str] = Field(None, description="Name of the candidate")
    exam_id: Optional[str] = Field(None, description="ID of the exam")
    exam_name: Optional[str] = Field(None, description="Name of the exam")
    subject_id: Optional[str] = Field(None, description="ID of the subject")
    subject_name: Optional[str] = Field(None, description="Name of the subject")
    
    class Config:
        from_attributes = True

class CandidateExamSubjectDetailResponse(CandidateExamSubjectResponse):
    """Enhanced model with additional schedule information."""
    exam_date: Optional[datetime] = Field(None, description="Date of the exam")
    start_time: Optional[datetime] = Field(None, description="Start time of the exam")
    end_time: Optional[datetime] = Field(None, description="End time of the exam")
    room_id: Optional[str] = Field(None, description="ID of the exam room")
    room_name: Optional[str] = Field(None, description="Name of the exam room")
    location_id: Optional[str] = Field(None, description="ID of the exam location")
    location_name: Optional[str] = Field(None, description="Name of the exam location")
    
    class Config:
        from_attributes = True

class CandidateExamSubjectListResponse(BaseModel):
    """Model for paginated list of candidate exam subjects."""
    items: List[CandidateExamSubjectResponse]
    total: int
    page: int
    size: int
    
    class Config:
        from_attributes = True
