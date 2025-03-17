"""
Certificate Data Transfer Objects (DTOs) module.

This module defines the data structures for API requests and responses
related to certificates issued to candidates after completing exams.
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import date, datetime
from enum import Enum
from uuid import UUID

class CertificateStatus(str, Enum):
    """Certificate status enumeration."""
    PENDING = "pending"
    ISSUED = "issued"
    REVOKED = "revoked"
    EXPIRED = "expired"

# Base model with common properties
class CertificateBase(BaseModel):
    """Base Certificate model with common attributes."""
    candidate_exam_id: str = Field(..., description="ID of the candidate exam registration")
    certificate_number: Optional[str] = Field(None, description="Unique certificate number/identifier")
    issue_date: Optional[date] = Field(None, description="Date when the certificate was issued")
    score: Optional[str] = Field(None, description="Score achieved (can be numeric or text, e.g. IELTS 7.5)")
    expiry_date: Optional[date] = Field(None, description="Date when the certificate expires")
    certificate_image_url: Optional[str] = Field(None, description="URL to the certificate image")
    additional_info: Optional[str] = Field(None, description="Additional information about the certificate")

    @validator('expiry_date')
    def expiry_date_must_be_after_issue_date(cls, v, values):
        """Validate that expiry date is after issue date."""
        if v and 'issue_date' in values and values['issue_date'] and v <= values['issue_date']:
            raise ValueError('Expiry date must be after issue date')
        return v

# Request model for creating a certificate
class CertificateCreate(CertificateBase):
    """Model for certificate creation requests."""
    pass

# Request model for updating a certificate
class CertificateUpdate(BaseModel):
    """Model for certificate update requests."""
    certificate_number: Optional[str] = Field(None, description="Unique certificate number/identifier")
    issue_date: Optional[date] = Field(None, description="Date when the certificate was issued")
    score: Optional[str] = Field(None, description="Score achieved (can be numeric or text, e.g. IELTS 7.5)")
    expiry_date: Optional[date] = Field(None, description="Date when the certificate expires")
    certificate_image_url: Optional[str] = Field(None, description="URL to the certificate image")
    additional_info: Optional[str] = Field(None, description="Additional information about the certificate")

    @validator('expiry_date')
    def expiry_date_must_be_after_issue_date(cls, v, values):
        """Validate that expiry date is after issue date."""
        if v and 'issue_date' in values and values['issue_date'] and v <= values['issue_date']:
            raise ValueError('Expiry date must be after issue date')
        return v

# Response model for a certificate
class CertificateResponse(CertificateBase):
    """Model for certificate responses."""
    certificate_id: str = Field(..., description="Unique identifier for the certificate")
    created_at: datetime = Field(..., description="Timestamp when the certificate was created")
    updated_at: Optional[datetime] = Field(None, description="Timestamp when the certificate was last updated")
    
    class Config:
        """Pydantic configuration."""
        from_attributes = True

# Enhanced response with related entity details
class CertificateDetailResponse(CertificateResponse):
    """Enhanced certificate response with related entity details."""
    candidate_name: str = Field(..., description="Name of the candidate")
    exam_name: str = Field(..., description="Name of the exam")
    
    class Config:
        """Pydantic configuration."""
        from_attributes = True

# Response model for a list of certificates
class CertificateListResponse(BaseModel):
    """Response model for a paginated list of certificates."""
    items: List[CertificateDetailResponse]
    total: int = Field(..., description="Total number of certificates")
    page: int = Field(..., description="Current page number")
    size: int = Field(..., description="Number of items per page")

# Request model for issuing a certificate
class IssueCertificateRequest(BaseModel):
    """Model for issuing a certificate request."""
    issue_date: Optional[date] = Field(None, description="Date when the certificate is issued")
    expiry_date: Optional[date] = Field(None, description="Date when the certificate expires")
    certificate_number: Optional[str] = Field(None, description="Unique certificate number/identifier")
    grade: Optional[str] = Field(None, description="Grade or classification achieved")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata for the certificate")
    
    @validator('expiry_date')
    def expiry_date_must_be_after_issue_date(cls, v, values):
        """Validate that expiry date is after issue date."""
        if v and 'issue_date' in values and values['issue_date'] and v <= values['issue_date']:
            raise ValueError('Expiry date must be after issue date')
        return v

# Request model for revoking a certificate
class RevokeCertificateRequest(BaseModel):
    """Model for revoking a certificate request."""
    revocation_reason: str = Field(..., description="Reason for certificate revocation")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata about the revocation") 