"""
Exam Score History Data Transfer Objects (DTOs) module.

This module defines the data structures for API requests and responses 
related to exam score history (tracking changes to exam scores).
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class ChangeType(str, Enum):
    CREATED = "created"
    UPDATED = "updated"
    GRADED = "graded"
    REVISED = "revised"
    SYSTEM = "system"
    REVIEW = "review"

# Base model with common properties
class ExamScoreHistoryBase(BaseModel):
    score_id: str = Field(..., description="ID of the exam score that was changed")
    previous_score: Optional[float] = Field(None, description="Previous score value before the change")
    new_score: Optional[float] = Field(None, description="New score value after the change")
    changed_by: Optional[str] = Field(None, description="ID of the user who made the change")
    change_reason: Optional[str] = Field(None, description="Reason for the change")
    change_date: datetime = Field(..., description="Date when the change occurred")

# Request model for creating a score history entry
class ExamScoreHistoryCreate(ExamScoreHistoryBase):
    pass

# Response model for a score history entry
class ExamScoreHistoryResponse(ExamScoreHistoryBase):
    history_id: str = Field(..., description="Unique identifier for the score history entry")
    created_at: datetime = Field(..., description="Timestamp when the history entry was created")
    updated_at: Optional[datetime] = Field(None, description="Timestamp when the history entry was last updated")
    
    class Config:
        from_attributes = True

# Enhanced response with related entity details
class ExamScoreHistoryDetailResponse(ExamScoreHistoryResponse):
    candidate_name: str = Field(..., description="Name of the candidate")
    candidate_code: Optional[str] = Field(None, description="Code of the candidate")
    exam_name: str = Field(..., description="Name of the exam")
    subject_name: str = Field(..., description="Name of the subject")
    changed_by_name: Optional[str] = Field(None, description="Name of the user who made the change")
    
    class Config:
        from_attributes = True
        
# Response model for a list of score history entries
class ExamScoreHistoryListResponse(BaseModel):
    items: List[ExamScoreHistoryDetailResponse]
    total: int = Field(..., description="Total number of score history entries")
    page: int = Field(..., description="Current page number")
    size: int = Field(..., description="Number of items per page") 