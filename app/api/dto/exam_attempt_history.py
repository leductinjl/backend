"""
Exam Attempt History Data Transfer Objects (DTOs) module.

This module defines the data structures for API requests and responses
related to exam attempt history (tracking attempts of candidates taking exams).
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from enum import Enum

class AttemptStatus(str, Enum):
    """Attempt status enumeration."""
    REGISTERED = "registered"
    CHECKED_IN = "checked_in"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ABSENT = "absent"
    DISQUALIFIED = "disqualified"
    CANCELLED = "cancelled"

class AttemptResult(str, Enum):
    """Attempt result enumeration."""
    PENDING = "pending"
    PASSED = "passed"
    FAILED = "failed"
    INCONCLUSIVE = "inconclusive"

# Base model with common properties
class ExamAttemptHistoryBase(BaseModel):
    """Base Exam Attempt History model with common attributes."""
    candidate_id: str = Field(..., description="ID of the candidate")
    exam_id: str = Field(..., description="ID of the exam")
    attempt_number: int = Field(..., description="Attempt number for this candidate and exam")
    attempt_date: date = Field(..., description="Date of the exam attempt")
    status: AttemptStatus = Field(AttemptStatus.REGISTERED, description="Status of the attempt")
    result: AttemptResult = Field(AttemptResult.PENDING, description="Result of the attempt")
    check_in_time: Optional[datetime] = Field(None, description="Time when the candidate checked in")
    start_time: Optional[datetime] = Field(None, description="Time when the candidate started the exam")
    end_time: Optional[datetime] = Field(None, description="Time when the candidate completed the exam")
    total_score: Optional[float] = Field(None, description="Total score achieved in this attempt")
    attendance_verified_by: Optional[str] = Field(None, description="ID of the user who verified attendance")
    disqualification_reason: Optional[str] = Field(None, description="Reason for disqualification if applicable")
    cancellation_reason: Optional[str] = Field(None, description="Reason for cancellation if applicable")
    notes: Optional[str] = Field(None, description="Additional notes about the attempt")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata for the attempt")

    @validator('attempt_number')
    def attempt_number_must_be_positive(cls, v):
        """Validate that attempt number is positive."""
        if v <= 0:
            raise ValueError('Attempt number must be a positive integer')
        return v

    @validator('end_time')
    def end_time_must_be_after_start_time(cls, v, values):
        """Validate that end time is after start time."""
        if v and 'start_time' in values and values['start_time'] and v < values['start_time']:
            raise ValueError('End time must be after start time')
        return v

# Request model for creating an attempt history entry
class ExamAttemptHistoryCreate(ExamAttemptHistoryBase):
    """Model for exam attempt history creation requests."""
    pass

# Request model for updating an attempt history entry
class ExamAttemptHistoryUpdate(BaseModel):
    """Model for exam attempt history update requests."""
    attempt_date: Optional[date] = Field(None, description="Date of the exam attempt")
    status: Optional[AttemptStatus] = Field(None, description="Status of the attempt")
    result: Optional[AttemptResult] = Field(None, description="Result of the attempt")
    check_in_time: Optional[datetime] = Field(None, description="Time when the candidate checked in")
    start_time: Optional[datetime] = Field(None, description="Time when the candidate started the exam")
    end_time: Optional[datetime] = Field(None, description="Time when the candidate completed the exam")
    total_score: Optional[float] = Field(None, description="Total score achieved in this attempt")
    attendance_verified_by: Optional[str] = Field(None, description="ID of the user who verified attendance")
    disqualification_reason: Optional[str] = Field(None, description="Reason for disqualification if applicable")
    cancellation_reason: Optional[str] = Field(None, description="Reason for cancellation if applicable")
    notes: Optional[str] = Field(None, description="Additional notes about the attempt")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata for the attempt")

    @validator('end_time')
    def end_time_must_be_after_start_time(cls, v, values):
        """Validate that end time is after start time."""
        if v and 'start_time' in values and values['start_time'] and v < values['start_time']:
            raise ValueError('End time must be after start time')
        return v

# Response model for an attempt history entry
class ExamAttemptHistoryResponse(ExamAttemptHistoryBase):
    """Model for exam attempt history responses."""
    attempt_id: str = Field(..., description="Unique identifier for the attempt")
    created_at: datetime = Field(..., description="Timestamp when the attempt record was created")
    updated_at: Optional[datetime] = Field(None, description="Timestamp when the attempt record was last updated")
    
    class Config:
        """Pydantic configuration."""
        from_attributes = True

# Enhanced response with related entity details
class ExamAttemptHistoryDetailResponse(ExamAttemptHistoryResponse):
    """Enhanced exam attempt history response with related entity details."""
    candidate_name: str = Field(..., description="Name of the candidate")
    candidate_code: Optional[str] = Field(None, description="Code of the candidate")
    exam_name: str = Field(..., description="Name of the exam")
    exam_type: Optional[str] = Field(None, description="Type of the exam")
    attendance_verified_by_name: Optional[str] = Field(None, description="Name of the user who verified attendance")
    subject_scores: Optional[List[Dict[str, Any]]] = Field(None, description="List of subject scores for this attempt")
    
    class Config:
        """Pydantic configuration."""
        from_attributes = True

# Response model for a list of attempt history entries
class ExamAttemptHistoryListResponse(BaseModel):
    """Response model for a paginated list of attempt history entries."""
    items: List[ExamAttemptHistoryDetailResponse]
    total: int = Field(..., description="Total number of attempt history entries")
    page: int = Field(..., description="Current page number")
    size: int = Field(..., description="Number of items per page")

# Request model for checking in a candidate
class CheckInRequest(BaseModel):
    """Model for checking in a candidate for an exam."""
    check_in_time: Optional[datetime] = Field(None, description="Time of check-in (defaults to current time)")
    notes: Optional[str] = Field(None, description="Additional notes about the check-in")

# Request model for starting an exam
class StartExamRequest(BaseModel):
    """Model for starting an exam for a candidate."""
    start_time: Optional[datetime] = Field(None, description="Time of exam start (defaults to current time)")
    notes: Optional[str] = Field(None, description="Additional notes about the exam start")

# Request model for completing an exam
class CompleteExamRequest(BaseModel):
    """Model for completing an exam for a candidate."""
    end_time: Optional[datetime] = Field(None, description="Time of exam completion (defaults to current time)")
    notes: Optional[str] = Field(None, description="Additional notes about the exam completion")

# Request model for marking a candidate as absent
class MarkAbsentRequest(BaseModel):
    """Model for marking a candidate as absent for an exam."""
    attendance_verified_by: Optional[str] = Field(None, description="ID of the user who verified absence")
    notes: Optional[str] = Field(None, description="Additional notes about the absence")

# Request model for disqualifying a candidate
class DisqualifyRequest(BaseModel):
    """Model for disqualifying a candidate from an exam."""
    disqualification_reason: str = Field(..., description="Reason for disqualification")
    attendance_verified_by: Optional[str] = Field(None, description="ID of the user who verified disqualification")
    notes: Optional[str] = Field(None, description="Additional notes about the disqualification")

# Request model for cancelling an attempt
class CancelAttemptRequest(BaseModel):
    """Model for cancelling an exam attempt."""
    cancellation_reason: str = Field(..., description="Reason for cancellation")
    notes: Optional[str] = Field(None, description="Additional notes about the cancellation") 