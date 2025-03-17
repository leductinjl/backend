"""
Management Unit Data Transfer Objects (DTOs) module.

This module defines the data structures for API requests and responses 
related to management units.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

# Base model with common properties
class ManagementUnitBase(BaseModel):
    unit_name: str = Field(..., min_length=1, max_length=100, description="Name of the management unit")
    unit_type: str = Field(..., description="Type of management unit (Department, Ministry, University Group)")
    additional_info: Optional[str] = Field(None, description="Additional information about the unit")

# Request model for creating a management unit
class ManagementUnitCreate(ManagementUnitBase):
    pass

# Request model for updating a management unit
class ManagementUnitUpdate(BaseModel):
    unit_name: Optional[str] = Field(None, min_length=1, max_length=100, description="Name of the management unit")
    unit_type: Optional[str] = Field(None, description="Type of management unit")
    additional_info: Optional[str] = Field(None, description="Additional information about the unit")

# Response model for a management unit
class ManagementUnitResponse(ManagementUnitBase):
    unit_id: str = Field(..., description="Unique identifier for the management unit")
    created_at: datetime = Field(..., description="Timestamp when the unit was created")
    updated_at: Optional[datetime] = Field(None, description="Timestamp when the unit was last updated")
    
    class Config:
        from_attributes = True
        
# Response model for a list of management units
class ManagementUnitListResponse(BaseModel):
    items: List[ManagementUnitResponse]
    total: int = Field(..., description="Total number of management units")
    page: int = Field(..., description="Current page number")
    size: int = Field(..., description="Number of items per page") 