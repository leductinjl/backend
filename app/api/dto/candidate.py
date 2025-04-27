from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Dict, Any
from datetime import date, datetime

# Base model with common attributes
class CandidateBase(BaseModel):
    full_name: str = Field(..., min_length=1, max_length=100)

# Model for personal information
class PersonalInfoBase(BaseModel):
    birth_date: date = Field(..., description="Date of birth")
    id_number: Optional[str] = Field(None, max_length=12)
    phone_number: Optional[str] = Field(None, max_length=15)
    email: Optional[EmailStr] = None
    primary_address: Optional[str] = None
    secondary_address: Optional[str] = None
    id_card_image_url: Optional[str] = None
    candidate_card_image_url: Optional[str] = None
    face_recognition_data_url: Optional[str] = None

# Request model for creating a new candidate
class CandidateCreate(CandidateBase):
    candidate_id: Optional[str] = Field(None, min_length=1, max_length=20)
    personal_info: Optional[PersonalInfoBase] = None

# Request model for updating a candidate
class CandidateUpdate(BaseModel):
    full_name: Optional[str] = Field(None, min_length=1, max_length=100)
    personal_info: Optional[PersonalInfoBase] = None

# Request model for updating only personal information
class PersonalInfoUpdate(BaseModel):
    birth_date: Optional[date] = Field(None, description="Date of birth")
    id_number: Optional[str] = Field(None, max_length=12)
    phone_number: Optional[str] = Field(None, max_length=15)
    email: Optional[EmailStr] = None
    primary_address: Optional[str] = None
    secondary_address: Optional[str] = None
    id_card_image_url: Optional[str] = None
    candidate_card_image_url: Optional[str] = None
    face_recognition_data_url: Optional[str] = None

# Response model for candidate list
class CandidateResponse(CandidateBase):
    candidate_id: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    personal_info: Optional[PersonalInfoBase] = None

    class Config:
        from_attributes = True

# Response model for candidate details
class CandidateDetailResponse(CandidateResponse):
    education_histories: Optional[List[Dict[str, Any]]] = None
    candidate_exams: Optional[List[Dict[str, Any]]] = None
    credentials: Optional[List[Dict[str, Any]]] = None

    class Config:
        from_attributes = True

class ImageUploadRequest(BaseModel):
    """Request model for uploading candidate images."""
    image_type: str = Field(..., description="Type of image (id_card, candidate_card, direct_face)")
    source: str = Field(..., description="Source of the image (upload, camera, etc.)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "image_type": "id_card",
                "source": "upload"
            }
        } 