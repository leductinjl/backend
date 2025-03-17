"""
Award DTO module.

This module defines Data Transfer Objects (DTOs) for the Award API,
providing standardized request and response models.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Any
from datetime import date, datetime

class AwardBase(BaseModel):
    """Base model for Award data"""
    candidate_exam_id: str = Field(..., description="ID of the candidate exam this award is linked to")
    award_type: Optional[str] = Field(None, description="Type of award (First, Second, Third, Gold Medal, Silver Medal)")
    achievement: Optional[str] = Field(None, description="Specific achievement if any")
    certificate_image_url: Optional[str] = Field(None, description="URL to the image of the award certificate")
    education_level: Optional[str] = Field(None, description="Education level when the award was earned")
    award_date: Optional[date] = Field(None, description="Date when the award was received")
    additional_info: Optional[str] = Field(None, description="Additional information about the award")

class AwardCreate(AwardBase):
    """Model for creating a new award"""
    pass

class AwardUpdate(BaseModel):
    """Model for updating an existing award"""
    candidate_exam_id: Optional[str] = Field(None, description="ID of the candidate exam this award is linked to")
    award_type: Optional[str] = Field(None, description="Type of award (First, Second, Third, Gold Medal, Silver Medal)")
    achievement: Optional[str] = Field(None, description="Specific achievement if any")
    certificate_image_url: Optional[str] = Field(None, description="URL to the image of the award certificate")
    education_level: Optional[str] = Field(None, description="Education level when the award was earned")
    award_date: Optional[date] = Field(None, description="Date when the award was received")
    additional_info: Optional[str] = Field(None, description="Additional information about the award")

class AwardResponse(AwardBase):
    """Model for award response data"""
    award_id: str = Field(..., description="Unique identifier for the award")
    created_at: datetime = Field(..., description="Timestamp when the award was created")
    updated_at: Optional[datetime] = Field(None, description="Timestamp when the award was last updated")
    # Include related data
    candidate_name: Optional[str] = Field(None, description="Name of the candidate")
    exam_name: Optional[str] = Field(None, description="Name of the exam")

    class Config:
        """Pydantic configuration"""
        from_attributes = True

class AwardListResponse(BaseModel):
    """Model for paginated list of awards"""
    items: List[AwardResponse] = Field(..., description="List of award items")
    total: int = Field(..., description="Total number of items")
    page: int = Field(..., description="Current page number")
    size: int = Field(..., description="Number of items per page") 