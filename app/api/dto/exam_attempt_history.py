"""
Exam Attempt History Data Transfer Objects (DTOs) module.

This module provides Data Transfer Objects for exam attempt history operations.
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from enum import Enum

class ExamAttemptHistoryBase(BaseModel):
    """Base Exam Attempt History model with common attributes."""
    candidate_exam_id: str = Field(..., description="ID of the candidate exam relationship")
    attempt_number: int = Field(..., description="Attempt number for this candidate and exam")
    attempt_date: date = Field(..., description="Date of the exam attempt")
    result: Optional[str] = Field(None, description="Result of the attempt (Pass, Fail)")
    notes: Optional[str] = Field(None, description="Additional notes about the attempt")

    @validator('attempt_number')
    def attempt_number_must_be_positive(cls, v):
        """Validate that attempt number is positive."""
        if v <= 0:
            raise ValueError('Attempt number must be a positive integer')
        return v

# Request model for creating an attempt history entry
class ExamAttemptHistoryCreate(ExamAttemptHistoryBase):
    """Model for exam attempt history creation requests."""
    pass

# Request model for updating an attempt history entry
class ExamAttemptHistoryUpdate(BaseModel):
    """Model for exam attempt history update requests."""
    attempt_date: Optional[date] = Field(None, description="Date of the exam attempt")
    result: Optional[str] = Field(None, description="Result of the attempt (Pass, Fail)")
    notes: Optional[str] = Field(None, description="Additional notes about the attempt")

# Response model for an attempt history entry
class ExamAttemptHistoryResponse(ExamAttemptHistoryBase):
    """Model for exam attempt history responses."""
    attempt_history_id: str = Field(..., description="Unique identifier for the attempt")
    created_at: datetime = Field(..., description="Timestamp when the attempt record was created")
    updated_at: Optional[datetime] = Field(None, description="Timestamp when the attempt record was last updated")
    
    class Config:
        """Pydantic configuration."""
        from_attributes = True

# Enhanced response with related entity details
class ExamAttemptHistoryDetailResponse(ExamAttemptHistoryResponse):
    """Enhanced exam attempt history response with related entity details."""
    candidate_name: Optional[str] = Field(None, description="Name of the candidate")
    candidate_code: Optional[str] = Field(None, description="Code of the candidate")
    exam_name: Optional[str] = Field(None, description="Name of the exam")
    exam_type: Optional[str] = Field(None, description="Type of the exam")
    
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
    pages: int = Field(1, description="Total number of pages")

# Request model for registering a new attempt
class RegisterAttemptRequest(BaseModel):
    """Model for registering a new attempt."""
    candidate_exam_id: str = Field(..., description="ID of the candidate exam relationship")
    attempt_date: date = Field(..., description="Date of the exam attempt")
    notes: Optional[str] = Field(None, description="Additional notes about the attempt") 