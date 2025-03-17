"""
Exam Location Mapping Data Transfer Objects (DTOs) module.

This module defines the data structures for API requests and responses 
related to exam location mappings (many-to-many relationship between exams and locations).
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

# Base model with common properties
class ExamLocationMappingBase(BaseModel):
    exam_id: str = Field(..., description="ID of the exam")
    location_id: str = Field(..., description="ID of the exam location")
    is_active: Optional[bool] = Field(True, description="Whether the mapping is active")
    is_primary: Optional[bool] = Field(False, description="Whether this is the primary location for the exam")
    mapping_metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata for the mapping")

# Request model for creating an exam location mapping
class ExamLocationMappingCreate(ExamLocationMappingBase):
    pass

# Request model for updating an exam location mapping
class ExamLocationMappingUpdate(BaseModel):
    is_active: Optional[bool] = Field(None, description="Whether the mapping is active")
    is_primary: Optional[bool] = Field(None, description="Whether this is the primary location for the exam")
    mapping_metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata for the mapping")

# Response model for an exam location mapping
class ExamLocationMappingResponse(ExamLocationMappingBase):
    mapping_id: str = Field(..., description="Unique identifier for the exam location mapping")
    created_at: datetime = Field(..., description="Timestamp when the mapping was created")
    updated_at: Optional[datetime] = Field(None, description="Timestamp when the mapping was last updated")
    
    class Config:
        from_attributes = True

# Enhanced response with exam and location details
class ExamLocationMappingDetailResponse(ExamLocationMappingResponse):
    exam_name: str = Field(..., description="Name of the exam")
    location_name: str = Field(..., description="Name of the exam location")
    
    class Config:
        from_attributes = True
        
# Response model for a list of exam location mappings
class ExamLocationMappingListResponse(BaseModel):
    items: List[ExamLocationMappingDetailResponse]
    total: int = Field(..., description="Total number of exam location mappings")
    page: int = Field(..., description="Current page number")
    size: int = Field(..., description="Number of items per page") 