"""
Candidate Search Service Module.

Module này cung cấp các dịch vụ tìm kiếm thông tin thí sinh theo nhiều tiêu chí
và phân nhóm thông tin kết quả.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import date

from app.graph_repositories.search.candidate_search_repository import CandidateSearchRepository
from app.api.dto.candidate_search import (
    CandidateBasicInfo,
    CandidateDetailedInfo,
    CandidateSearchResult,
    EducationInfo,
    ExamsInfo,
    AchievementsInfo,
    SchoolInfo,
    MajorInfo,
    DegreeInfo,
    ExamInfo,
    ExamScheduleInfo,
    ScoreInfo,
    ScoreReviewInfo,
    CertificateInfo,
    CredentialInfo,
    AwardInfo,
    AchievementInfo,
    RecognitionInfo
)

logger = logging.getLogger(__name__)

class CandidateSearchService:
    """Service for searching and retrieving candidate information."""
    
    def __init__(self, search_repo: CandidateSearchRepository):
        """Initialize with search repository."""
        self.search_repo = search_repo
        self.logger = logging.getLogger(__name__)
    
    def _convert_neo4j_date(self, neo4j_date) -> Optional[date]:
        """Convert Neo4j Date to Python date."""
        if neo4j_date is None:
            return None
        return date(neo4j_date.year, neo4j_date.month, neo4j_date.day)
    
    async def search_candidates(self, search_criteria: Dict[str, Any], page: int = 1, page_size: int = 10) -> CandidateSearchResult:
        """
        Tìm kiếm thí sinh theo nhiều tiêu chí.
        
        Args:
            search_criteria: Dictionary chứa các tiêu chí tìm kiếm
            page: Số trang
            page_size: Kích thước trang
            
        Returns:
            CandidateSearchResult chứa danh sách thí sinh và thông tin phân trang
        """
        try:
            # Gọi repository để thực hiện tìm kiếm
            candidates, total = await self.search_repo.search_candidates(search_criteria, page, page_size)
            
            # Chuyển đổi kết quả sang DTO
            candidate_dtos = []
            
            for candidate in candidates:
                candidate_dto = CandidateBasicInfo(
                    candidate_id=candidate.get("candidate_id"),
                    full_name=candidate.get("full_name"),
                    birth_date=self._convert_neo4j_date(candidate.get("birth_date")),
                    id_number=candidate.get("id_number"),
                    phone_number=candidate.get("phone_number"),
                    email=candidate.get("email"),
                    primary_address=candidate.get("primary_address") or candidate.get("address"),
                    secondary_address=candidate.get("secondary_address"),
                    id_card_image_url=candidate.get("id_card_image_url"),
                    candidate_card_image_url=candidate.get("candidate_card_image_url")
                )
                candidate_dtos.append(candidate_dto)
            
            # Trả về kết quả tìm kiếm
            return CandidateSearchResult(
                candidates=candidate_dtos,
                total=total,
                page=page,
                page_size=page_size
            )
            
        except Exception as e:
            self.logger.error(f"Error searching candidates: {str(e)}", exc_info=True)
            # Trả về kết quả trống nếu có lỗi
            return CandidateSearchResult(
                candidates=[],
                total=0,
                page=page,
                page_size=page_size
            )
    
    async def get_candidate_info(self, candidate_id: str, include_education: bool = False, 
                               include_exams: bool = False, include_achievements: bool = False) -> Optional[CandidateDetailedInfo]:
        """
        Lấy thông tin chi tiết của thí sinh theo ID, với các nhóm thông tin tùy chọn.
        
        Args:
            candidate_id: ID của thí sinh
            include_education: Có bao gồm thông tin học vấn không
            include_exams: Có bao gồm thông tin kỳ thi không
            include_achievements: Có bao gồm thông tin thành tích không
            
        Returns:
            CandidateDetailedInfo chứa thông tin chi tiết của thí sinh theo các nhóm
        """
        try:
            # Lấy thông tin cơ bản của thí sinh
            candidate_data = await self.search_repo.get_candidate_by_id(candidate_id)
            if not candidate_data:
                return None
            
            # Tạo đối tượng thông tin cơ bản
            basic_info = CandidateBasicInfo(
                candidate_id=candidate_data.get("candidate_id"),
                full_name=candidate_data.get("full_name"),
                birth_date=self._convert_neo4j_date(candidate_data.get("birth_date")),
                id_number=candidate_data.get("id_number"),
                phone_number=candidate_data.get("phone_number"),
                email=candidate_data.get("email"),
                primary_address=candidate_data.get("primary_address") or candidate_data.get("address"),
                secondary_address=candidate_data.get("secondary_address"),
                id_card_image_url=candidate_data.get("id_card_image_url"),
                candidate_card_image_url=candidate_data.get("candidate_card_image_url")
            )
            
            # Khởi tạo kết quả
            result = CandidateDetailedInfo(basic_info=basic_info)
            
            # Nếu yêu cầu thông tin học vấn
            if include_education:
                education_data = await self.search_repo.get_candidate_education_info(candidate_id)
                
                # Chuyển đổi dữ liệu trường học
                schools = [
                    SchoolInfo(
                        school_id=s.get("school_id"),
                        school_name=s.get("school_name"),
                        start_year=s.get("start_year"),
                        end_year=s.get("end_year"),
                        education_level=s.get("education_level"),
                        academic_performance=s.get("academic_performance"),
                        additional_info=s.get("additional_info")
                    ) for s in education_data.get("schools", [])
                    if s.get("school_id") is not None and s.get("school_name") is not None
                ]
                
                # Chuyển đổi dữ liệu ngành học
                majors = [
                    MajorInfo(
                        major_id=m.get("major_id"),
                        major_name=m.get("major_name"),
                        school_id=m.get("school_id"),
                        school_name=m.get("school_name"),
                        start_year=m.get("start_year"),
                        end_year=m.get("end_year")
                    ) for m in education_data.get("majors", [])
                    if m.get("major_id") is not None and m.get("major_name") is not None
                ]
                
                # Chuyển đổi dữ liệu bằng cấp
                degrees = [
                    DegreeInfo(
                        degree_id=d.get("degree_id"),
                        degree_name=d.get("degree_name"),
                        issue_date=d.get("issue_date"),
                        issuing_organization=d.get("issuing_organization"),
                        major_id=d.get("major_id"),
                        major_name=d.get("major_name"),
                        school_id=d.get("school_id"),
                        school_name=d.get("school_name")
                    ) for d in education_data.get("degrees", [])
                    if d.get("degree_id") is not None and d.get("degree_name") is not None
                ]
                
                # Gán thông tin học vấn vào kết quả
                result.education_info = EducationInfo(
                    schools=schools,
                    majors=majors,
                    degrees=degrees
                )
            
            # Nếu yêu cầu thông tin kỳ thi
            if include_exams:
                exams_data = await self.search_repo.get_candidate_exams_info(candidate_id)
                
                # Chuyển đổi dữ liệu kỳ thi
                exams = [
                    ExamInfo(
                        exam_id=e.get("exam_id"),
                        exam_name=e.get("exam_name"),
                        registration_number=e.get("registration_number"),
                        registration_date=self._convert_neo4j_date(e.get("registration_date")),
                        status=e.get("status")
                    ) for e in exams_data.get("exams", [])
                    if e.get("exam_id") is not None and e.get("exam_name") is not None
                ]
                
                # Chuyển đổi dữ liệu lịch thi
                schedules = [
                    ExamScheduleInfo(
                        exam_schedule_id=s.get("exam_schedule_id"),
                        exam_id=s.get("exam_id"),
                        exam_name=s.get("exam_name"),
                        subject_id=s.get("subject_id"),
                        subject_name=s.get("subject_name"),
                        room_id=s.get("room_id"),
                        room_name=s.get("room_name"),
                        exam_date=s.get("exam_date"),
                        start_time=s.get("start_time"),
                        end_time=s.get("end_time")
                    ) for s in exams_data.get("schedules", [])
                    if s.get("exam_schedule_id") is not None and s.get("exam_id") is not None 
                    and s.get("exam_name") is not None and s.get("subject_id") is not None 
                    and s.get("subject_name") is not None
                ]
                
                # Chuyển đổi dữ liệu điểm thi
                scores = [
                    ScoreInfo(
                        exam_score_id=s.get("exam_score_id"),
                        exam_id=s.get("exam_id"),
                        exam_name=s.get("exam_name"),
                        subject_id=s.get("subject_id"),
                        subject_name=s.get("subject_name"),
                        score=s.get("score", 0.0),
                        max_score=s.get("max_score", 10.0),
                        min_score=s.get("min_score", 0.0),
                        is_final=s.get("is_final", True)
                    ) for s in exams_data.get("scores", [])
                    if s.get("exam_score_id") is not None and s.get("exam_id") is not None 
                    and s.get("exam_name") is not None and s.get("subject_id") is not None 
                    and s.get("subject_name") is not None and s.get("score") is not None
                ]
                
                # Chuyển đổi dữ liệu phúc khảo
                reviews = [
                    ScoreReviewInfo(
                        review_id=r.get("review_id"),
                        exam_score_id=r.get("exam_score_id"),
                        subject_name=r.get("subject_name"),
                        original_score=r.get("original_score", 0.0),
                        reviewed_score=r.get("reviewed_score"),
                        status=r.get("status"),
                        request_date=r.get("request_date"),
                        completion_date=r.get("completion_date")
                    ) for r in exams_data.get("reviews", [])
                    if r.get("review_id") is not None and r.get("exam_score_id") is not None 
                    and r.get("subject_name") is not None and r.get("original_score") is not None 
                    and r.get("status") is not None and r.get("request_date") is not None
                ]
                
                # Gán thông tin kỳ thi vào kết quả
                result.exams_info = ExamsInfo(
                    exams=exams,
                    schedules=schedules,
                    scores=scores,
                    reviews=reviews
                )
            
            # Nếu yêu cầu thông tin thành tích
            if include_achievements:
                achievements_data = await self.search_repo.get_candidate_achievements_info(candidate_id)
                
                # Chuyển đổi dữ liệu chứng chỉ
                certificates = [
                    CertificateInfo(
                        certificate_id=c.get("certificate_id"),
                        certificate_name=c.get("certificate_name"),
                        issue_date=c.get("issue_date"),
                        issuing_organization=c.get("issuing_organization"),
                        expiry_date=c.get("expiry_date"),
                        certificate_code=c.get("certificate_code")
                    ) for c in achievements_data.get("certificates", [])
                    if c.get("certificate_id") is not None and c.get("certificate_name") is not None
                ]
                
                # Chuyển đổi dữ liệu giấy tờ xác thực
                credentials = [
                    CredentialInfo(
                        credential_id=c.get("credential_id"),
                        title=c.get("title"),
                        credential_type=c.get("credential_type"),
                        issuing_organization=c.get("issuing_organization"),
                        issue_date=c.get("issue_date"),
                        expiry_date=c.get("expiry_date"),
                        verification_status=c.get("verification_status")
                    ) for c in achievements_data.get("credentials", [])
                    if c.get("credential_id") is not None and c.get("title") is not None 
                    and c.get("credential_type") is not None and c.get("issuing_organization") is not None 
                    and c.get("issue_date") is not None
                ]
                
                # Chuyển đổi dữ liệu giải thưởng
                awards = [
                    AwardInfo(
                        award_id=a.get("award_id"),
                        award_name=a.get("award_name"),
                        award_level=a.get("award_level"),
                        issuing_organization=a.get("issuing_organization"),
                        issue_date=a.get("issue_date"),
                        description=a.get("description")
                    ) for a in achievements_data.get("awards", [])
                    if a.get("award_id") is not None and a.get("award_name") is not None 
                    and a.get("award_level") is not None and a.get("issuing_organization") is not None 
                    and a.get("issue_date") is not None
                ]
                
                # Chuyển đổi dữ liệu thành tích
                achievements = [
                    AchievementInfo(
                        achievement_id=a.get("achievement_id"),
                        achievement_name=a.get("achievement_name"),
                        achievement_type=a.get("achievement_type"),
                        description=a.get("description"),
                        date_achieved=a.get("date_achieved"),
                        issuing_organization=a.get("issuing_organization")
                    ) for a in achievements_data.get("achievements", [])
                    if a.get("achievement_id") is not None and a.get("achievement_name") is not None 
                    and a.get("achievement_type") is not None and a.get("date_achieved") is not None
                ]
                
                # Chuyển đổi dữ liệu công nhận
                recognitions = [
                    RecognitionInfo(
                        recognition_id=r.get("recognition_id"),
                        recognition_type=r.get("recognition_type"),
                        description=r.get("description"),
                        issue_date=r.get("issue_date"),
                        issuing_organization=r.get("issuing_organization")
                    ) for r in achievements_data.get("recognitions", [])
                    if r.get("recognition_id") is not None and r.get("recognition_type") is not None 
                    and r.get("issue_date") is not None
                ]
                
                # Gán thông tin thành tích vào kết quả
                result.achievements_info = AchievementsInfo(
                    certificates=certificates,
                    credentials=credentials,
                    awards=awards,
                    achievements=achievements,
                    recognitions=recognitions
                )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error getting candidate info for ID {candidate_id}: {str(e)}", exc_info=True)
            return None
    
    async def get_candidate_education_info(self, candidate_id: str) -> Optional[EducationInfo]:
        """
        Lấy thông tin học vấn của thí sinh.
        
        Args:
            candidate_id: ID của thí sinh
            
        Returns:
            EducationInfo chứa thông tin về trường học, ngành học, và bằng cấp
        """
        try:
            # Kiểm tra xem thí sinh tồn tại không
            candidate = await self.search_repo.get_candidate_by_id(candidate_id)
            if not candidate:
                return None
            
            # Lấy thông tin học vấn
            education_data = await self.search_repo.get_candidate_education_info(candidate_id)
            
            # Chuyển đổi dữ liệu trường học
            schools = [
                SchoolInfo(
                    school_id=s.get("school_id"),
                    school_name=s.get("school_name"),
                    start_year=s.get("start_year"),
                    end_year=s.get("end_year"),
                    education_level=s.get("education_level"),
                    academic_performance=s.get("academic_performance"),
                    additional_info=s.get("additional_info")
                ) for s in education_data.get("schools", [])
            ]
            
            # Chuyển đổi dữ liệu ngành học
            majors = [
                MajorInfo(
                    major_id=m.get("major_id"),
                    major_name=m.get("major_name"),
                    school_id=m.get("school_id"),
                    school_name=m.get("school_name"),
                    start_year=m.get("start_year"),
                    end_year=m.get("end_year")
                ) for m in education_data.get("majors", [])
            ]
            
            # Chuyển đổi dữ liệu bằng cấp
            degrees = [
                DegreeInfo(
                    degree_id=d.get("degree_id"),
                    degree_name=d.get("degree_name"),
                    issue_date=d.get("issue_date"),
                    issuing_organization=d.get("issuing_organization"),
                    major_id=d.get("major_id"),
                    major_name=d.get("major_name"),
                    school_id=d.get("school_id"),
                    school_name=d.get("school_name")
                ) for d in education_data.get("degrees", [])
            ]
            
            # Trả về kết quả
            return EducationInfo(
                schools=schools,
                majors=majors,
                degrees=degrees
            )
            
        except Exception as e:
            self.logger.error(f"Error getting education info for candidate {candidate_id}: {str(e)}", exc_info=True)
            return None
    
    async def get_candidate_exams_info(self, candidate_id: str) -> Optional[ExamsInfo]:
        """
        Lấy thông tin kỳ thi của thí sinh.
        
        Args:
            candidate_id: ID của thí sinh
            
        Returns:
            ExamsInfo chứa thông tin về kỳ thi, lịch thi, điểm số, và phúc khảo
        """
        try:
            # Kiểm tra xem thí sinh tồn tại không
            candidate = await self.search_repo.get_candidate_by_id(candidate_id)
            if not candidate:
                return None
            
            # Lấy thông tin kỳ thi
            exams_data = await self.search_repo.get_candidate_exams_info(candidate_id)
            
            # Chuyển đổi dữ liệu kỳ thi
            exams = [
                ExamInfo(
                    exam_id=e.get("exam_id"),
                    exam_name=e.get("exam_name"),
                    registration_number=e.get("registration_number"),
                    registration_date=self._convert_neo4j_date(e.get("registration_date")),
                    status=e.get("status")
                ) for e in exams_data.get("exams", [])
                if e.get("exam_id") is not None and e.get("exam_name") is not None
            ]
            
            # Chuyển đổi dữ liệu lịch thi
            schedules = [
                ExamScheduleInfo(
                    exam_schedule_id=s.get("exam_schedule_id"),
                    exam_id=s.get("exam_id"),
                    exam_name=s.get("exam_name"),
                    subject_id=s.get("subject_id"),
                    subject_name=s.get("subject_name"),
                    room_id=s.get("room_id"),
                    room_name=s.get("room_name"),
                    exam_date=s.get("exam_date"),
                    start_time=s.get("start_time"),
                    end_time=s.get("end_time")
                ) for s in exams_data.get("schedules", [])
                if s.get("exam_schedule_id") is not None and s.get("exam_id") is not None 
                and s.get("exam_name") is not None and s.get("subject_id") is not None 
                and s.get("subject_name") is not None
            ]
            
            # Chuyển đổi dữ liệu điểm thi
            scores = [
                ScoreInfo(
                    exam_score_id=s.get("exam_score_id"),
                    exam_id=s.get("exam_id"),
                    exam_name=s.get("exam_name"),
                    subject_id=s.get("subject_id"),
                    subject_name=s.get("subject_name"),
                    score=s.get("score", 0.0),
                    max_score=s.get("max_score", 10.0),
                    min_score=s.get("min_score", 0.0),
                    is_final=s.get("is_final", True)
                ) for s in exams_data.get("scores", [])
                if s.get("exam_score_id") is not None and s.get("exam_id") is not None 
                and s.get("exam_name") is not None and s.get("subject_id") is not None 
                and s.get("subject_name") is not None and s.get("score") is not None
            ]
            
            # Chuyển đổi dữ liệu phúc khảo
            reviews = [
                ScoreReviewInfo(
                    review_id=r.get("review_id"),
                    exam_score_id=r.get("exam_score_id"),
                    subject_name=r.get("subject_name"),
                    original_score=r.get("original_score", 0.0),
                    reviewed_score=r.get("reviewed_score"),
                    status=r.get("status"),
                    request_date=r.get("request_date"),
                    completion_date=r.get("completion_date")
                ) for r in exams_data.get("reviews", [])
                if r.get("review_id") is not None and r.get("exam_score_id") is not None 
                and r.get("subject_name") is not None and r.get("original_score") is not None 
                and r.get("status") is not None and r.get("request_date") is not None
            ]
            
            # Trả về kết quả
            return ExamsInfo(
                exams=exams,
                schedules=schedules,
                scores=scores,
                reviews=reviews
            )
            
        except Exception as e:
            self.logger.error(f"Error getting exams info for candidate {candidate_id}: {str(e)}", exc_info=True)
            return None
    
    async def get_candidate_achievements_info(self, candidate_id: str) -> Optional[AchievementsInfo]:
        """
        Lấy thông tin thành tích và giấy tờ của thí sinh.
        
        Args:
            candidate_id: ID của thí sinh
            
        Returns:
            AchievementsInfo chứa thông tin về chứng chỉ, giấy tờ xác thực, giải thưởng, thành tích, và công nhận
        """
        try:
            # Kiểm tra xem thí sinh tồn tại không
            candidate = await self.search_repo.get_candidate_by_id(candidate_id)
            if not candidate:
                return None
            
            # Lấy thông tin thành tích
            achievements_data = await self.search_repo.get_candidate_achievements_info(candidate_id)
            
            # Chuyển đổi dữ liệu chứng chỉ
            certificates = [
                CertificateInfo(
                    certificate_id=c.get("certificate_id"),
                    certificate_name=c.get("certificate_name"),
                    issue_date=c.get("issue_date"),
                    issuing_organization=c.get("issuing_organization"),
                    expiry_date=c.get("expiry_date"),
                    certificate_code=c.get("certificate_code")
                ) for c in achievements_data.get("certificates", [])
            ]
            
            # Chuyển đổi dữ liệu giấy tờ xác thực
            credentials = [
                CredentialInfo(
                    credential_id=c.get("credential_id"),
                    title=c.get("title"),
                    credential_type=c.get("credential_type"),
                    issuing_organization=c.get("issuing_organization"),
                    issue_date=c.get("issue_date"),
                    expiry_date=c.get("expiry_date"),
                    verification_status=c.get("verification_status")
                ) for c in achievements_data.get("credentials", [])
            ]
            
            # Chuyển đổi dữ liệu giải thưởng
            awards = [
                AwardInfo(
                    award_id=a.get("award_id"),
                    award_name=a.get("award_name"),
                    award_level=a.get("award_level"),
                    issuing_organization=a.get("issuing_organization"),
                    issue_date=a.get("issue_date"),
                    description=a.get("description")
                ) for a in achievements_data.get("awards", [])
            ]
            
            # Chuyển đổi dữ liệu thành tích
            achievements = [
                AchievementInfo(
                    achievement_id=a.get("achievement_id"),
                    achievement_name=a.get("achievement_name"),
                    achievement_type=a.get("achievement_type"),
                    description=a.get("description"),
                    date_achieved=a.get("date_achieved"),
                    issuing_organization=a.get("issuing_organization")
                ) for a in achievements_data.get("achievements", [])
            ]
            
            # Chuyển đổi dữ liệu công nhận
            recognitions = [
                RecognitionInfo(
                    recognition_id=r.get("recognition_id"),
                    recognition_type=r.get("recognition_type"),
                    description=r.get("description"),
                    issue_date=r.get("issue_date"),
                    issuing_organization=r.get("issuing_organization")
                ) for r in achievements_data.get("recognitions", [])
            ]
            
            # Trả về kết quả
            return AchievementsInfo(
                certificates=certificates,
                credentials=credentials,
                awards=awards,
                achievements=achievements,
                recognitions=recognitions
            )
            
        except Exception as e:
            self.logger.error(f"Error getting achievements info for candidate {candidate_id}: {str(e)}", exc_info=True)
            return None 