"""
Personal Information model module.

This module defines the PersonalInfo model for storing detailed personal information
about candidates, including contact information and identification details.
"""

from sqlalchemy import Column, String, Date, ForeignKey, DateTime, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.infrastructure.database.connection import Base

class PersonalInfo(Base):
    """
    Model for storing detailed personal information about candidates.
    
    This model includes contact information, identification, and addresses
    for each candidate in the system.
    """
    __tablename__ = "personal_info"
    
    candidate_id = Column(String(20), ForeignKey("candidate.candidate_id"), primary_key=True)
    birth_date = Column(Date, nullable=False)
    gender = Column(String(10), nullable=True)
    id_number = Column(String(12), unique=True)
    phone_number = Column(String(15))
    email = Column(String(100))
    primary_address = Column(String)
    secondary_address = Column(String)
    id_card_image_url = Column(String)
    candidate_card_image_url = Column(String)
    face_recognition_data_url = Column(String)
    
    # Face embedding fields
    face_embedding = Column(JSON, nullable=True, comment="Vector đặc trưng khuôn mặt được mã hóa dưới dạng JSON")
    face_embedding_model = Column(String(50), nullable=True, comment="Tên mô hình được sử dụng để tạo embedding")
    face_embedding_date = Column(DateTime(timezone=True), nullable=True, comment="Thời điểm tạo embedding")
    face_embedding_source = Column(String(20), nullable=True, comment="Nguồn ảnh (id_card, candidate_card, direct_face)")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationship to Candidate
    candidate = relationship("Candidate", back_populates="personal_info")
    
    def __repr__(self):
        return f"<PersonalInfo(candidate_id='{self.candidate_id}', id_number='{self.id_number}')>" 