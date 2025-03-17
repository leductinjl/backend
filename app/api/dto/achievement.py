"""
Achievement DTO module.

This module defines Data Transfer Objects (DTOs) for the Achievement API,
providing standardized request and response models.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Any
from datetime import date, datetime

class AchievementBase(BaseModel):
    """Base model for Achievement data"""
    candidate_exam_id: str = Field(..., description="ID of the candidate exam this achievement is linked to")
    achievement_name: str = Field(..., description="Name of the achievement")
    achievement_type: Optional[str] = Field(None, description="Type of achievement (Research, Community Service, Sports, Arts)")
    description: Optional[str] = Field(None, description="Description of the achievement")
    achievement_date: Optional[date] = Field(None, description="Date when the achievement was accomplished")
    organization: Optional[str] = Field(None, description="Organization recognizing the achievement")
    proof_url: Optional[str] = Field(None, description="URL to proof of achievement")
    education_level: Optional[str] = Field(None, description="Education level when achieved")
    additional_info: Optional[str] = Field(None, description="Additional information about the achievement")

class AchievementCreate(AchievementBase):
    """Model for creating a new achievement"""
    pass

class AchievementUpdate(BaseModel):
    """Model for updating an existing achievement"""
    candidate_exam_id: Optional[str] = Field(None, description="ID of the candidate exam this achievement is linked to")
    achievement_name: Optional[str] = Field(None, description="Name of the achievement")
    achievement_type: Optional[str] = Field(None, description="Type of achievement (Research, Community Service, Sports, Arts)")
    description: Optional[str] = Field(None, description="Description of the achievement")
    achievement_date: Optional[date] = Field(None, description="Date when the achievement was accomplished")
    organization: Optional[str] = Field(None, description="Organization recognizing the achievement")
    proof_url: Optional[str] = Field(None, description="URL to proof of achievement")
    education_level: Optional[str] = Field(None, description="Education level when achieved")
    additional_info: Optional[str] = Field(None, description="Additional information about the achievement")

class AchievementResponse(AchievementBase):
    """Model for achievement response data"""
    achievement_id: str = Field(..., description="Unique identifier for the achievement")
    created_at: datetime = Field(..., description="Timestamp when the achievement was created")
    updated_at: Optional[datetime] = Field(None, description="Timestamp when the achievement was last updated")
    # Include related data
    candidate_name: Optional[str] = Field(None, description="Name of the candidate")
    exam_name: Optional[str] = Field(None, description="Name of the exam")

    class Config:
        """Pydantic configuration"""
        from_attributes = True

class AchievementListResponse(BaseModel):
    """Model for paginated list of achievements"""
    items: List[AchievementResponse] = Field(..., description="List of achievement items")
    total: int = Field(..., description="Total number of items")
    page: int = Field(..., description="Current page number")
    size: int = Field(..., description="Number of items per page") 