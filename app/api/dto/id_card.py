from pydantic import BaseModel, Field
from typing import Optional
from datetime import date

class IdCardBase(BaseModel):
    """Base model for ID card data"""
    id_number: str = Field(..., description="ID number (CMND/CCCD)")
    full_name: str = Field(..., description="Full name")
    birth_date: date = Field(..., description="Birth date")
    gender: str = Field(..., description="Gender (M/F)")
    address: str = Field(..., description="Address")
    issue_date: Optional[date] = Field(None, description="Issue date")
    expiry_date: Optional[date] = Field(None, description="Expiry date")
    issue_place: Optional[str] = Field(None, description="Issue place")
    nationality: Optional[str] = Field(None, description="Nationality")
    ethnicity: Optional[str] = Field(None, description="Ethnicity")
    religion: Optional[str] = Field(None, description="Religion")
    features: Optional[str] = Field(None, description="Distinguishing features")

class IdCardCreate(IdCardBase):
    """Model for creating a new ID card"""
    pass

class IdCardUpdate(BaseModel):
    """Model for updating an ID card"""
    id_number: Optional[str] = Field(None, description="ID number (CMND/CCCD)")
    full_name: Optional[str] = Field(None, description="Full name")
    birth_date: Optional[date] = Field(None, description="Birth date")
    gender: Optional[str] = Field(None, description="Gender (M/F)")
    address: Optional[str] = Field(None, description="Address")
    issue_date: Optional[date] = Field(None, description="Issue date")
    expiry_date: Optional[date] = Field(None, description="Expiry date")
    issue_place: Optional[str] = Field(None, description="Issue place")
    nationality: Optional[str] = Field(None, description="Nationality")
    ethnicity: Optional[str] = Field(None, description="Ethnicity")
    religion: Optional[str] = Field(None, description="Religion")
    features: Optional[str] = Field(None, description="Distinguishing features")

class IdCardResponse(IdCardBase):
    """Model for ID card response"""
    id_card_id: str = Field(..., description="ID card ID")
    created_at: date = Field(..., description="Creation date")
    updated_at: date = Field(..., description="Last update date")
    image_url: Optional[str] = Field(None, description="URL of the ID card image")

    class Config:
        from_attributes = True 