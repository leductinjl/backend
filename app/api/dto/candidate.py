from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Dict, Any
from datetime import date

# Base model với các thuộc tính chung
class CandidateBase(BaseModel):
    full_name: str = Field(..., min_length=1, max_length=100)

# Model cho thông tin cá nhân
class PersonalInfoBase(BaseModel):
    birth_date: Optional[date] = None
    id_number: Optional[str] = Field(None, max_length=12)
    phone_number: Optional[str] = Field(None, max_length=15)
    email: Optional[EmailStr] = None
    primary_address: Optional[str] = None
    secondary_address: Optional[str] = None

# Request model cho tạo thí sinh mới
class CandidateCreate(CandidateBase):
    candidate_id: str = Field(..., min_length=1, max_length=20)
    personal_info: Optional[PersonalInfoBase] = None

# Request model cho cập nhật thí sinh
class CandidateUpdate(BaseModel):
    full_name: Optional[str] = Field(None, min_length=1, max_length=100)
    personal_info: Optional[PersonalInfoBase] = None

# Response model cho danh sách thí sinh
class CandidateResponse(CandidateBase):
    candidate_id: str

    class Config:
        from_attributes = True

# Response model cho chi tiết thí sinh
class CandidateDetailResponse(CandidateResponse):
    personal_info: Optional[PersonalInfoBase] = None

    class Config:
        from_attributes = True

# Response model cho thông tin lịch sử học tập
class EducationHistoryResponse(BaseModel):
    school_id: int
    school_name: str
    education_level: str
    start_year: Optional[int] = None
    end_year: Optional[int] = None
    academic_performance: Optional[str] = None

# Response model cho thông tin môn thi
class SubjectScore(BaseModel):
    subject_id: int
    subject_name: str
    score: Optional[float] = None

# Response model cho lịch sử thi
class ExamHistoryResponse(BaseModel):
    exam_id: int
    exam_name: str
    registration_number: Optional[str] = None
    registration_date: Optional[date] = None
    status: Optional[str] = None
    subjects: List[SubjectScore] = [] 