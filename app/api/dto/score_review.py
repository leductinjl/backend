"""
Score Review DTO module.

This module provides Data Transfer Objects for score review operations.
"""

from datetime import date, datetime
from typing import Dict, List, Optional, Any, Union
from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict, field_validator, condecimal

class ScoreReviewBase(BaseModel):
    """Base DTO for score review operations."""
    
    score_id: str = Field(..., description="ID of the exam score")
    request_date: date = Field(default=None, description="Date when the review was requested")
    review_status: str = Field(default="pending", description="Status of the review")
    original_score: Optional[Decimal] = Field(
        default=None, 
        description="Original score before review",
        json_schema_extra={"max_digits": 5, "decimal_places": 2}
    )
    reviewed_score: Optional[Decimal] = Field(
        default=None, 
        description="Reviewed score after evaluation",
        json_schema_extra={"max_digits": 5, "decimal_places": 2}
    )
    review_result: Optional[str] = Field(default=None, description="Result of the review")
    review_date: Optional[date] = Field(default=None, description="Date when the review was completed")
    additional_info: Optional[str] = Field(default=None, description="Additional information about the review")
    score_review_metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata for the review")

    model_config = ConfigDict(from_attributes=True)

class ScoreReviewCreate(ScoreReviewBase):
    """DTO for creating a score review."""
    
    pass

class ScoreReviewUpdate(BaseModel):
    """DTO for updating a score review."""
    
    review_status: Optional[str] = Field(default=None, description="Status of the review")
    reviewed_score: Optional[Decimal] = Field(
        default=None, 
        description="Reviewed score after evaluation",
        json_schema_extra={"max_digits": 5, "decimal_places": 2}
    )
    review_result: Optional[str] = Field(default=None, description="Result of the review")
    review_date: Optional[date] = Field(default=None, description="Date when the review was completed")
    additional_info: Optional[str] = Field(default=None, description="Additional information about the review")
    score_review_metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata for the review")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

class ExamScoreInfo(BaseModel):
    """Exam score information included in score review responses."""
    
    score_id: str
    candidate_id: str
    exam_id: str
    subject_id: str
    score: Optional[float] = None
    scoring_date: Optional[date] = None
    status: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class CandidateInfo(BaseModel):
    """Candidate information included in score review responses."""
    
    candidate_id: str
    candidate_code: str
    name: str

    model_config = ConfigDict(from_attributes=True)

class ExamInfo(BaseModel):
    """Exam information included in score review responses."""
    
    exam_id: str
    name: str

    model_config = ConfigDict(from_attributes=True)

class SubjectInfo(BaseModel):
    """Subject information included in score review responses."""
    
    subject_id: str
    subject_code: str
    name: str

    model_config = ConfigDict(from_attributes=True)

class ScoreReviewResponse(ScoreReviewBase):
    """DTO for score review response."""
    
    score_review_id: str = Field(..., description="Unique identifier of the score review")
    created_at: datetime = Field(..., description="Date and time when the review was created")
    updated_at: Optional[datetime] = Field(default=None, description="Date and time when the review was last updated")

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_orm(cls, obj):
        """Convert database object to DTO."""
        if isinstance(obj, dict):
            return cls(**obj)
        return super().from_orm(obj)

class ScoreReviewDetailResponse(ScoreReviewResponse):
    """DTO for detailed score review response with related information."""
    
    exam_score: Optional[ExamScoreInfo] = None
    candidate: Optional[CandidateInfo] = None
    exam: Optional[ExamInfo] = None
    subject: Optional[SubjectInfo] = None

    @classmethod
    def from_orm(cls, obj):
        """Convert database object to DTO with related information."""
        if isinstance(obj, dict):
            return cls(**obj)
        return super().from_orm(obj)

class PaginationMeta(BaseModel):
    """DTO for pagination metadata."""
    
    total: int = Field(..., description="Total number of records")
    page: int = Field(..., description="Current page number")
    size: int = Field(..., description="Number of records per page")
    pages: int = Field(..., description="Total number of pages")

    @field_validator('pages', mode='after')
    @classmethod
    def compute_pages(cls, v: int, values: Dict) -> int:
        """Compute total number of pages."""
        if 'total' in values.data and 'size' in values.data:
            total = values.data['total']
            size = values.data['size']
            if size > 0:
                return (total + size - 1) // size
        return v or 1

class ScoreReviewListResponse(BaseModel):
    """DTO for paginated score review list response."""
    
    items: List[ScoreReviewResponse] = Field(..., description="List of score reviews")
    total: int = Field(..., description="Total number of records")
    page: int = Field(..., description="Current page number")
    size: int = Field(..., description="Number of records per page")
    pages: int = Field(1, description="Total number of pages")

    @field_validator('pages', mode='after')
    @classmethod
    def compute_pages(cls, v: int, values: Dict) -> int:
        """Compute total number of pages."""
        if 'total' in values.data and 'size' in values.data:
            total = values.data['total']
            size = values.data['size']
            if size > 0:
                return (total + size - 1) // size
        return v or 1 