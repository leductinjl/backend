"""
Candidate Credential DTO module.

This module contains Data Transfer Objects for the Candidate Credential API,
used for validation and serialization of external credentials data.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, date

class CandidateCredentialBase(BaseModel):
    """Base model with common attributes for candidate credentials"""
    candidate_id: str = Field(..., description="ID of the candidate")
    credential_type: str = Field(..., description="Type of credential (CERTIFICATE, AWARD, RECOGNITION, ACHIEVEMENT)")
    title: str = Field(..., description="Title of the credential")
    issuing_organization: Optional[str] = Field(None, description="Organization that issued the credential")
    issue_date: Optional[date] = Field(None, description="Date when the credential was issued")
    description: Optional[str] = Field(None, description="Detailed description of the credential")
    proof_url: Optional[str] = Field(None, description="URL to the credential image/document")
    external_reference: Optional[str] = Field(None, description="External reference number")
    additional_info: Optional[str] = Field(None, description="Any additional information")

class CandidateCredentialCreate(CandidateCredentialBase):
    """Model for creating a new candidate credential"""
    pass

class CandidateCredentialUpdate(BaseModel):
    """Model for updating a candidate credential"""
    credential_type: Optional[str] = Field(None, description="Type of credential (CERTIFICATE, AWARD, RECOGNITION, ACHIEVEMENT)")
    title: Optional[str] = Field(None, description="Title of the credential")
    issuing_organization: Optional[str] = Field(None, description="Organization that issued the credential")
    issue_date: Optional[date] = Field(None, description="Date when the credential was issued")
    description: Optional[str] = Field(None, description="Detailed description of the credential")
    proof_url: Optional[str] = Field(None, description="URL to the credential image/document")
    external_reference: Optional[str] = Field(None, description="External reference number")
    additional_info: Optional[str] = Field(None, description="Any additional information")

class CandidateCredentialResponse(CandidateCredentialBase):
    """Model for candidate credential in API responses"""
    credential_id: str = Field(..., description="Unique identifier for the credential")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class CandidateCredentialListResponse(BaseModel):
    """Model for paginated list of candidate credentials"""
    items: List[CandidateCredentialResponse]
    total: int
    page: int
    size: int
    
    class Config:
        from_attributes = True 