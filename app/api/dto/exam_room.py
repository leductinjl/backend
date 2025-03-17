"""
Exam Room Data Transfer Objects (DTOs) module.

This module defines the data structures for API requests and responses 
related to exam rooms.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

# Base model with common properties
class ExamRoomBase(BaseModel):
    room_name: str = Field(..., min_length=1, max_length=100, description="Name of the exam room")
    capacity: int = Field(..., ge=1, description="Capacity of the exam room (number of seats)")
    floor: Optional[int] = Field(None, description="Floor number where the room is located")
    room_number: Optional[str] = Field(None, max_length=20, description="Room number or identifier")
    description: Optional[str] = Field(None, description="Additional description of the room")
    is_active: Optional[bool] = Field(True, description="Whether the exam room is active")
    equipment: Optional[List[str]] = Field(None, description="List of equipment available in the room")
    special_requirements: Optional[str] = Field(None, description="Special requirements or notes about the room")
    location_id: str = Field(..., description="ID of the exam location this room belongs to")
    room_metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata for the exam room")

# Request model for creating an exam room
class ExamRoomCreate(ExamRoomBase):
    pass

# Request model for updating an exam room
class ExamRoomUpdate(BaseModel):
    room_name: Optional[str] = Field(None, min_length=1, max_length=100, description="Name of the exam room")
    capacity: Optional[int] = Field(None, ge=1, description="Capacity of the exam room (number of seats)")
    floor: Optional[int] = Field(None, description="Floor number where the room is located")
    room_number: Optional[str] = Field(None, max_length=20, description="Room number or identifier")
    description: Optional[str] = Field(None, description="Additional description of the room")
    is_active: Optional[bool] = Field(None, description="Whether the exam room is active")
    equipment: Optional[List[str]] = Field(None, description="List of equipment available in the room")
    special_requirements: Optional[str] = Field(None, description="Special requirements or notes about the room")
    location_id: Optional[str] = Field(None, description="ID of the exam location this room belongs to")
    room_metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata for the exam room")

# Schema for an exam summary
class ExamSummary(BaseModel):
    exam_id: str = Field(..., description="ID of the exam")
    exam_name: str = Field(..., description="Name of the exam")

# Response model for an exam room
class ExamRoomResponse(ExamRoomBase):
    room_id: str = Field(..., description="Unique identifier for the exam room")
    created_at: datetime = Field(..., description="Timestamp when the exam room was created")
    updated_at: Optional[datetime] = Field(None, description="Timestamp when the exam room was last updated")
    
    class Config:
        from_attributes = True

# Enhanced response with exam location details
class ExamRoomDetailResponse(ExamRoomResponse):
    location_name: str = Field(..., description="Name of the exam location")
    exam_id: Optional[str] = Field(None, description="ID of the exam (if linked to only one exam)")
    exam_name: Optional[str] = Field(None, description="Name of the exam (if linked to only one exam)")
    
    class Config:
        from_attributes = True

# Full detail response showing all linked exams
class ExamRoomFullDetailResponse(ExamRoomResponse):
    location_name: str = Field(..., description="Name of the exam location")
    exams: List[ExamSummary] = Field(default_factory=list, description="List of exams linked to this room's location")
    
    class Config:
        from_attributes = True
        
# Response model for a list of exam rooms
class ExamRoomListResponse(BaseModel):
    items: List[ExamRoomDetailResponse]
    total: int = Field(..., description="Total number of exam rooms")
    page: int = Field(..., description="Current page number")
    size: int = Field(..., description="Number of items per page") 