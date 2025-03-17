"""
Degree model module.

This module defines the Degree model for higher education qualifications
achieved by candidates, such as Bachelor's, Master's, or PhD degrees.
"""

from sqlalchemy import Column, String, Text, ForeignKey, DateTime, Date
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship, validates
from app.infrastructure.database.connection import Base
from app.services.id_service import generate_model_id

class Degree(Base):
    """
    Model for higher education degrees.
    
    Represents degrees earned by candidates at higher education levels,
    including Bachelor, Master, and PhD.
    """
    __tablename__ = "degree"
    
    degree_id = Column(String(50), primary_key=True, index=True)
    major_id = Column(String(50), ForeignKey("major.major_id"), nullable=False)
    start_year = Column(Date)
    end_year = Column(Date)
    academic_performance = Column(String(20))  # Good, Excellent
    degree_image_url = Column(Text)
    additional_info = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    major = relationship("Major", back_populates="degrees")
    
    @validates('degree_id')
    def validate_id(self, key, id_value):
        """Validate and generate ID if not provided."""
        if not id_value:
            return generate_model_id("Degree")
        return id_value
    
    def __repr__(self):
        return f"<Degree(degree_id='{self.degree_id}', major_id='{self.major_id}')>" 