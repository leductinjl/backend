"""
Exam Location Data Transfer Objects (DTOs) module.

This module defines the data structures for API requests and responses 
related to exam locations.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime

# Base model with common properties
class ExamLocationBase(BaseModel):
    location_name: str = Field(..., min_length=1, max_length=200, description="Name of the exam location")
    address: str = Field(..., min_length=1, max_length=500, description="Address of the exam location")
    city: str = Field(..., min_length=1, max_length=100, description="City of the exam location")
    state_province: Optional[str] = Field(None, max_length=100, description="State or province of the exam location")
    country: str = Field(..., min_length=1, max_length=100, description="Country of the exam location")
    postal_code: Optional[str] = Field(None, max_length=20, description="Postal code of the exam location")
    capacity: Optional[int] = Field(None, ge=0, description="Total capacity of the exam location")
    contact_info: Optional[Dict] = Field(None, description="Contact information for the exam location")
    additional_info: Optional[str] = Field(None, description="Additional information about the exam location")
    is_active: Optional[bool] = Field(True, description="Whether the exam location is active")

# Request model for creating an exam location
class ExamLocationCreate(ExamLocationBase):
    exam_id: Optional[str] = Field(None, description="Optional: ID of an exam to immediately map this location to")

# Request model for updating an exam location
class ExamLocationUpdate(BaseModel):
    location_name: Optional[str] = Field(None, min_length=1, max_length=200, description="Name of the exam location")
    address: Optional[str] = Field(None, min_length=1, max_length=500, description="Address of the exam location")
    city: Optional[str] = Field(None, min_length=1, max_length=100, description="City of the exam location")
    state_province: Optional[str] = Field(None, max_length=100, description="State or province of the exam location")
    country: Optional[str] = Field(None, min_length=1, max_length=100, description="Country of the exam location")
    postal_code: Optional[str] = Field(None, max_length=20, description="Postal code of the exam location")
    capacity: Optional[int] = Field(None, ge=0, description="Total capacity of the exam location")
    contact_info: Optional[Dict] = Field(None, description="Contact information for the exam location")
    additional_info: Optional[str] = Field(None, description="Additional information about the exam location")
    is_active: Optional[bool] = Field(None, description="Whether the exam location is active")
    exam_id: Optional[str] = Field(None, description="Optional: ID of an exam to map this location to")

# Response model for an exam location
class ExamLocationResponse(ExamLocationBase):
    location_id: str = Field(..., description="Unique identifier for the exam location")
    created_at: datetime = Field(..., description="Timestamp when the exam location was created")
    updated_at: Optional[datetime] = Field(None, description="Timestamp when the exam location was last updated")
    
    class Config:
        from_attributes = True

# Enhanced response with exam details
class ExamLocationDetailResponse(ExamLocationResponse):
    exams: List[Dict] = Field(default_factory=list, description="List of exams associated with this location")
    
    class Config:
        from_attributes = True
        
# Response model for a list of exam locations
class ExamLocationListResponse(BaseModel):
    items: List[ExamLocationDetailResponse]
    total: int = Field(..., description="Total number of exam locations")
    page: int = Field(..., description="Current page number")
    size: int = Field(..., description="Number of items per page") 