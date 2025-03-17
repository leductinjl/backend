"""
Recognition DTO module.

This module defines Data Transfer Objects (DTOs) for the Recognition API,
providing standardized request and response models.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Any
from datetime import date, datetime

class RecognitionBase(BaseModel):
    """Base model for Recognition data"""
    title: str = Field(..., description="Title of the recognition")
    issuing_organization: str = Field(..., description="Organization that issued the recognition")
    issue_date: Optional[date] = Field(None, description="Date when recognition was issued")
    recognition_type: Optional[str] = Field(None, description="Type of recognition (Completion, Participation, Appreciation)")
    candidate_exam_id: str = Field(..., description="ID of the candidate exam this recognition is linked to")
    recognition_image_url: Optional[str] = Field(None, description="URL to the image of the recognition")
    description: Optional[str] = Field(None, description="Description of the recognition")
    additional_info: Optional[str] = Field(None, description="Additional information about the recognition")

class RecognitionCreate(RecognitionBase):
    """Model for creating a new recognition"""
    pass

class RecognitionUpdate(BaseModel):
    """Model for updating an existing recognition"""
    title: Optional[str] = Field(None, description="Title of the recognition")
    issuing_organization: Optional[str] = Field(None, description="Organization that issued the recognition")
    issue_date: Optional[date] = Field(None, description="Date when recognition was issued")
    recognition_type: Optional[str] = Field(None, description="Type of recognition (Completion, Participation, Appreciation)")
    candidate_exam_id: Optional[str] = Field(None, description="ID of the candidate exam this recognition is linked to")
    recognition_image_url: Optional[str] = Field(None, description="URL to the image of the recognition")
    description: Optional[str] = Field(None, description="Description of the recognition")
    additional_info: Optional[str] = Field(None, description="Additional information about the recognition")

class RecognitionResponse(RecognitionBase):
    """Model for recognition response data"""
    recognition_id: str = Field(..., description="Unique identifier for the recognition")
    created_at: datetime = Field(..., description="Timestamp when the recognition was created")
    updated_at: Optional[datetime] = Field(None, description="Timestamp when the recognition was last updated")
    # Include related data
    candidate_name: Optional[str] = Field(None, description="Name of the candidate")
    exam_name: Optional[str] = Field(None, description="Name of the exam")

    class Config:
        """Pydantic configuration"""
        from_attributes = True

class RecognitionListResponse(BaseModel):
    """Model for paginated list of recognitions"""
    items: List[RecognitionResponse] = Field(..., description="List of recognition items")
    total: int = Field(..., description="Total number of items")
    page: int = Field(..., description="Current page number")
    size: int = Field(..., description="Number of items per page") 