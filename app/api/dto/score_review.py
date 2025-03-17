"""
Score Review Data Transfer Objects (DTOs) module.

This module defines the data structures for API requests and responses 
related to score reviews (requests to review and potentially change exam scores).
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class ReviewStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELED = "canceled"
    COMPLETED = "completed"

class ReviewPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

# Base model with common properties
class ScoreReviewBase(BaseModel):
    score_id: str = Field(..., description="ID of the exam score being reviewed")
    requested_by: str = Field(..., description="ID of the user who requested the review")
    reason: str = Field(..., description="Reason for requesting the review")
    expected_score: Optional[float] = Field(None, description="Expected score after review")
    status: ReviewStatus = Field(ReviewStatus.PENDING, description="Status of the review")
    priority: ReviewPriority = Field(ReviewPriority.MEDIUM, description="Priority of the review")
    assigned_to: Optional[str] = Field(None, description="ID of the user assigned to handle the review")
    resolution_notes: Optional[str] = Field(None, description="Notes about the resolution of the review")
    resolved_at: Optional[datetime] = Field(None, description="Timestamp when the review was resolved")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata for the review")

# Request model for creating a score review
class ScoreReviewCreate(ScoreReviewBase):
    pass

# Request model for updating a score review
class ScoreReviewUpdate(BaseModel):
    reason: Optional[str] = Field(None, description="Reason for requesting the review")
    expected_score: Optional[float] = Field(None, description="Expected score after review")
    status: Optional[ReviewStatus] = Field(None, description="Status of the review")
    priority: Optional[ReviewPriority] = Field(None, description="Priority of the review")
    assigned_to: Optional[str] = Field(None, description="ID of the user assigned to handle the review")
    resolution_notes: Optional[str] = Field(None, description="Notes about the resolution of the review")
    resolved_at: Optional[datetime] = Field(None, description="Timestamp when the review was resolved")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata for the review")

# Response model for a score review
class ScoreReviewResponse(ScoreReviewBase):
    review_id: str = Field(..., description="Unique identifier for the score review")
    created_at: datetime = Field(..., description="Timestamp when the review was created")
    updated_at: Optional[datetime] = Field(None, description="Timestamp when the review was last updated")
    
    class Config:
        from_attributes = True

# Enhanced response with related entity details
class ScoreReviewDetailResponse(ScoreReviewResponse):
    candidate_name: str = Field(..., description="Name of the candidate")
    candidate_code: Optional[str] = Field(None, description="Code of the candidate")
    exam_name: str = Field(..., description="Name of the exam")
    subject_name: str = Field(..., description="Name of the subject")
    current_score: Optional[float] = Field(None, description="Current score before review")
    max_score: Optional[float] = Field(None, description="Maximum possible score for this subject")
    requested_by_name: Optional[str] = Field(None, description="Name of the user who requested the review")
    assigned_to_name: Optional[str] = Field(None, description="Name of the user assigned to handle the review")
    
    class Config:
        from_attributes = True
        
# Response model for a list of score reviews
class ScoreReviewListResponse(BaseModel):
    items: List[ScoreReviewDetailResponse]
    total: int = Field(..., description="Total number of score reviews")
    page: int = Field(..., description="Current page number")
    size: int = Field(..., description="Number of items per page") 