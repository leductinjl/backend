"""
Certificate model module.

This module defines the Certificate model for certificates earned by candidates
upon successful completion of certain exams.
"""

from sqlalchemy import Column, Integer, String, Text, Date, ForeignKey, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship, validates
from app.infrastructure.database.connection import Base
from app.services.id_service import generate_model_id

class Certificate(Base):
    """
    Model for certificates.
    
    Represents certificates earned by candidates upon successful completion
    of certain exams, including details like certificate number,
    issue date, and expiration.
    """
    __tablename__ = "certificate"
    
    certificate_id = Column(String(50), primary_key=True, index=True)
    candidate_exam_id = Column(String(50), ForeignKey("candidate_exam.candidate_exam_id"), nullable=False)
    certificate_number = Column(String(50))
    issue_date = Column(Date)
    score = Column(String(20))  # Can be a number or text (e.g. IELTS 7.5, TOEIC 850)
    expiry_date = Column(Date)
    certificate_image_url = Column(Text)
    additional_info = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    candidate_exam = relationship("CandidateExam", back_populates="certificates")
    
    @validates('certificate_id')
    def validate_id(self, key, id_value):
        """Validate and generate ID if not provided."""
        if not id_value:
            return generate_model_id("Certificate")
        return id_value
    
    def __repr__(self):
        return f"<Certificate(certificate_id='{self.certificate_id}', certificate_number='{self.certificate_number}')>" 