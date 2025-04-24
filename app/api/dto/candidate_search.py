from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import date

# DTO cho kết quả tìm kiếm cơ bản
class CandidateBasicInfo(BaseModel):
    candidate_id: str
    full_name: str
    birth_date: Optional[date] = None
    id_number: Optional[str] = None
    phone_number: Optional[str] = None
    email: Optional[str] = None
    primary_address: Optional[str] = None
    secondary_address: Optional[str] = None
    id_card_image_url: Optional[str] = None
    candidate_card_image_url: Optional[str] = None

# DTO cho thông tin trường học
class SchoolInfo(BaseModel):
    school_id: str
    school_name: str
    start_year: Optional[int] = None
    end_year: Optional[int] = None
    education_level: Optional[str] = None
    academic_performance: Optional[str] = None
    additional_info: Optional[str] = None

# DTO cho thông tin ngành học
class MajorInfo(BaseModel):
    major_id: str
    major_name: str
    school_id: Optional[str] = None
    school_name: Optional[str] = None
    start_year: Optional[int] = None
    end_year: Optional[int] = None

# DTO cho thông tin bằng cấp
class DegreeInfo(BaseModel):
    degree_id: str
    degree_name: str
    issue_date: Optional[date] = None
    issuing_organization: Optional[str] = None
    major_id: Optional[str] = None
    major_name: Optional[str] = None
    school_id: Optional[str] = None
    school_name: Optional[str] = None

# DTO cho nhóm thông tin học vấn
class EducationInfo(BaseModel):
    schools: List[SchoolInfo] = []
    majors: List[MajorInfo] = []
    degrees: List[DegreeInfo] = []

# DTO cho thông tin kỳ thi
class ExamInfo(BaseModel):
    exam_id: str
    exam_name: str
    registration_number: Optional[str] = None
    registration_date: Optional[date] = None
    status: Optional[str] = None

# DTO cho thông tin lịch thi
class ExamScheduleInfo(BaseModel):
    exam_schedule_id: str
    exam_id: str
    exam_name: str
    subject_id: str
    subject_name: str
    room_id: Optional[str] = None
    room_name: Optional[str] = None
    exam_date: Optional[date] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None

# DTO cho thông tin điểm thi
class ScoreInfo(BaseModel):
    exam_score_id: str
    exam_id: str
    exam_name: str
    subject_id: str
    subject_name: str
    score: float
    max_score: float = 10.0
    min_score: float = 0.0
    is_final: bool = True

# DTO cho thông tin phúc khảo
class ScoreReviewInfo(BaseModel):
    review_id: str
    exam_score_id: str
    subject_name: str
    original_score: float
    reviewed_score: Optional[float] = None
    status: str
    request_date: date
    completion_date: Optional[date] = None

# DTO cho nhóm thông tin kỳ thi
class ExamsInfo(BaseModel):
    exams: List[ExamInfo] = []
    schedules: List[ExamScheduleInfo] = []
    scores: List[ScoreInfo] = []
    reviews: List[ScoreReviewInfo] = []

# DTO cho thông tin chứng chỉ
class CertificateInfo(BaseModel):
    certificate_id: str
    certificate_name: str
    issue_date: Optional[date] = None
    issuing_organization: Optional[str] = None
    expiry_date: Optional[date] = None
    certificate_code: Optional[str] = None

# DTO cho thông tin giấy tờ xác thực
class CredentialInfo(BaseModel):
    credential_id: str
    title: str
    credential_type: str
    issuing_organization: str
    issue_date: date
    expiry_date: Optional[date] = None
    verification_status: Optional[str] = None

# DTO cho thông tin giải thưởng
class AwardInfo(BaseModel):
    award_id: str
    award_name: str
    award_level: str
    issuing_organization: str
    issue_date: date
    description: Optional[str] = None

# DTO cho thông tin thành tích
class AchievementInfo(BaseModel):
    achievement_id: str
    achievement_name: str
    achievement_type: str
    description: Optional[str] = None
    date_achieved: date
    issuing_organization: Optional[str] = None

# DTO cho thông tin công nhận
class RecognitionInfo(BaseModel):
    recognition_id: str
    recognition_type: str
    description: Optional[str] = None
    issue_date: date
    issuing_organization: Optional[str] = None

# DTO cho nhóm thông tin thành tích và giấy tờ
class AchievementsInfo(BaseModel):
    certificates: List[CertificateInfo] = []
    credentials: List[CredentialInfo] = []
    awards: List[AwardInfo] = []
    achievements: List[AchievementInfo] = []
    recognitions: List[RecognitionInfo] = []

# DTO tổng hợp cho tất cả thông tin thí sinh theo nhóm
class CandidateDetailedInfo(BaseModel):
    basic_info: CandidateBasicInfo
    education_info: Optional[EducationInfo] = None
    exams_info: Optional[ExamsInfo] = None
    achievements_info: Optional[AchievementsInfo] = None

# DTO cho kết quả tìm kiếm thí sinh
class CandidateSearchResult(BaseModel):
    candidates: List[CandidateBasicInfo]
    total: int
    page: int
    page_size: int

# DTO cho yêu cầu tìm kiếm thí sinh
class CandidateSearchRequest(BaseModel):
    candidate_id: Optional[str] = None
    id_number: Optional[str] = None
    full_name: Optional[str] = None
    birth_date: Optional[date] = None
    phone_number: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    registration_number: Optional[str] = None
    exam_id: Optional[str] = None
    school_id: Optional[str] = None
    page: int = 1
    page_size: int = 10 