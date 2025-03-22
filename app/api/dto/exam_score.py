"""
Exam Score Data Transfer Objects (DTOs) module.

This module defines the data structures for API requests and responses 
related to exam scores (scores of candidates for exam subjects).
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class ScoreStatus(str, Enum):
    PENDING = "pending"
    GRADED = "graded"
    REVISED = "revised"
    CANCELED = "canceled"
    UNDER_REVIEW = "under_review"

# Base model with common properties
class ExamScoreBase(BaseModel):
    exam_subject_id: str = Field(..., description="ID of the exam subject")
    candidate_exam_subject_id: str = Field(..., description="ID of the candidate's registration for this exam subject")
    score: Optional[float] = Field(None, description="Score obtained by the candidate")
    status: ScoreStatus = Field(ScoreStatus.PENDING, description="Status of the score")
    graded_by: Optional[str] = Field(None, description="ID of the user who graded the exam")
    graded_at: Optional[datetime] = Field(None, description="Timestamp when the exam was graded")
    notes: Optional[str] = Field(None, description="Additional notes about the score")
    score_metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata for the score")

# Request model for creating an exam score
class ExamScoreCreate(ExamScoreBase):
    pass

# Request model for updating an exam score
class ExamScoreUpdate(BaseModel):
    score: Optional[float] = Field(None, description="Score obtained by the candidate")
    status: Optional[ScoreStatus] = Field(None, description="Status of the score")
    graded_by: Optional[str] = Field(None, description="ID of the user who graded the exam")
    graded_at: Optional[datetime] = Field(None, description="Timestamp when the exam was graded")
    notes: Optional[str] = Field(None, description="Additional notes about the score")
    score_metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata for the score")

# Response model for an exam score
class ExamScoreResponse(ExamScoreBase):
    exam_score_id: str = Field(..., description="Unique identifier for the exam score")
    created_at: datetime = Field(..., description="Timestamp when the exam score was created")
    updated_at: Optional[datetime] = Field(None, description="Timestamp when the exam score was last updated")
    
    class Config:
        from_attributes = True

# Enhanced response with candidate, exam, and subject details
class ExamScoreDetailResponse(ExamScoreResponse):
    candidate_id: str = Field(..., description="ID of the candidate")
    candidate_name: str = Field(..., description="Name of the candidate")
    candidate_code: Optional[str] = Field(None, description="Code of the candidate")
    exam_id: str = Field(..., description="ID of the exam")
    exam_name: str = Field(..., description="Name of the exam")
    subject_id: str = Field(..., description="ID of the subject")
    subject_name: str = Field(..., description="Name of the subject")
    subject_code: Optional[str] = Field(None, description="Code of the subject")
    exam_date: Optional[datetime] = Field(None, description="Date of the exam")
    max_score: Optional[float] = Field(None, description="Maximum possible score for this subject")
    passing_score: Optional[float] = Field(None, description="Minimum score required to pass this subject")
    
    class Config:
        from_attributes = True
        
# Response model for a list of exam scores
class ExamScoreListResponse(BaseModel):
    items: List[ExamScoreDetailResponse]
    total: int = Field(..., description="Total number of exam scores")
    page: int = Field(..., description="Current page number")
    size: int = Field(..., description="Number of items per page") 