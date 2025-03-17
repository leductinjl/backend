"""
Exam Schedule DTO module.

This module contains Data Transfer Objects for the Exam Schedule API,
used for validation and serialization of exam schedule data.
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
import pytz

class ExamScheduleBase(BaseModel):
    """Base model with common attributes for exam schedules"""
    exam_subject_id: str = Field(..., description="ID of the exam subject")
    start_time: datetime = Field(..., description="Start time of the exam")
    end_time: datetime = Field(..., description="End time of the exam")
    description: Optional[str] = Field(None, description="Additional information about the exam schedule")
    status: Optional[str] = Field("SCHEDULED", description="Status of the exam schedule (SCHEDULED, ONGOING, COMPLETED, CANCELLED)")

    @validator('end_time')
    def end_time_must_be_after_start_time(cls, v, values):
        """Validate that end_time is after start_time."""
        if 'start_time' in values and v <= values['start_time']:
            raise ValueError('End time must be after start time')
        return v

class ExamScheduleCreate(ExamScheduleBase):
    """Model for creating a new exam schedule"""
    pass

class ExamScheduleUpdate(BaseModel):
    """Model for updating an exam schedule"""
    start_time: Optional[datetime] = Field(None, description="Start time of the exam")
    end_time: Optional[datetime] = Field(None, description="End time of the exam")
    description: Optional[str] = Field(None, description="Additional information about the exam schedule")
    status: Optional[str] = Field(None, description="Status of the exam schedule (SCHEDULED, ONGOING, COMPLETED, CANCELLED)")

    @validator('end_time')
    def end_time_must_be_after_start_time(cls, v, values):
        """Validate that end_time is after start_time if both are provided."""
        if v and 'start_time' in values and values['start_time'] and v <= values['start_time']:
            raise ValueError('End time must be after start time')
        return v

class ExamScheduleResponse(ExamScheduleBase):
    """Model for exam schedule in API responses"""
    exam_schedule_id: str = Field(..., description="Unique identifier for the exam schedule")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    # Additional fields from related entities
    exam_id: Optional[str] = Field(None, description="ID of the related exam")
    exam_name: Optional[str] = Field(None, description="Name of the related exam")
    subject_id: Optional[str] = Field(None, description="ID of the related subject")
    subject_name: Optional[str] = Field(None, description="Name of the related subject")
    
    class Config:
        from_attributes = True
        
    @classmethod
    def from_orm(cls, obj):
        """Create an instance of ExamScheduleResponse from an ORM object with proper mapping of nested fields."""
        # Create the response with fields directly from the model
        response = super().from_orm(obj)
        
        # Map nested relationship fields if they exist
        if hasattr(obj, 'exam_subject') and obj.exam_subject:
            # Get exam info
            if hasattr(obj.exam_subject, 'exam_id'):
                response.exam_id = obj.exam_subject.exam_id
                
            if hasattr(obj.exam_subject, 'exam') and obj.exam_subject.exam:
                response.exam_name = obj.exam_subject.exam.exam_name
                
            # Get subject info
            if hasattr(obj.exam_subject, 'subject_id'):
                response.subject_id = obj.exam_subject.subject_id
                
            if hasattr(obj.exam_subject, 'subject') and obj.exam_subject.subject:
                response.subject_name = obj.exam_subject.subject.subject_name
                
        return response

class ExamScheduleListResponse(BaseModel):
    """Model for paginated list of exam schedules"""
    items: List[ExamScheduleResponse]
    total: int
    page: int
    size: int
    
    class Config:
        from_attributes = True 