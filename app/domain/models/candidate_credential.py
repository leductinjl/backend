"""
Candidate Credential model module.

This module defines the CandidateCredential model for storing external certificates,
awards, recognitions, and achievements obtained by candidates outside the system.
"""

from sqlalchemy import Column, String, Text, Date, ForeignKey, DateTime, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship, validates
from app.infrastructure.database.connection import Base
from app.services.id_service import generate_model_id
import enum

class CredentialType(str, enum.Enum):
    """Enum for credential types."""
    CERTIFICATE = "CERTIFICATE"
    AWARD = "AWARD" 
    RECOGNITION = "RECOGNITION"
    ACHIEVEMENT = "ACHIEVEMENT"

class CandidateCredential(Base):
    """
    Model for candidate external credentials.
    
    Represents certificates, awards, recognitions and achievements 
    obtained by candidates from external sources/organizations.
    """
    __tablename__ = "candidate_credential"
    
    credential_id = Column(String(60), primary_key=True, index=True)
    candidate_id = Column(String(50), ForeignKey("candidate.candidate_id"), nullable=False)
    credential_type = Column(String(20), nullable=False)  # CERTIFICATE, AWARD, RECOGNITION, ACHIEVEMENT
    title = Column(String(200), nullable=False)
    issuing_organization = Column(String(100))
    issue_date = Column(Date)
    description = Column(Text)
    proof_url = Column(Text)  # URL to credential image/document
    external_reference = Column(String(100))  # External reference number (if any)
    additional_info = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    candidate = relationship("Candidate", back_populates="credentials")
    
    @validates('credential_id')
    def validate_id(self, key, id_value):
        """Validate and generate ID if not provided."""
        if not id_value:
            return generate_model_id("CandidateCredential")
        return id_value
    
    @validates('credential_type')
    def validate_credential_type(self, key, value):
        """Validate credential type."""
        if value not in [t.value for t in CredentialType]:
            valid_types = ", ".join([t.value for t in CredentialType])
            raise ValueError(f"Invalid credential type. Must be one of: {valid_types}")
        return value
    
    def __repr__(self):
        return f"<CandidateCredential(credential_id='{self.credential_id}', credential_type='{self.credential_type}', title='{self.title}')>" 