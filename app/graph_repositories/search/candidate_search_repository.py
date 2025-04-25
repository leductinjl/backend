"""
Candidate Search Repository Module.

Module này cung cấp các truy vấn tìm kiếm thí sinh trong Neo4j graph database.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import date

from app.domain.graph_models.candidate_node import CandidateNode

logger = logging.getLogger(__name__)

class CandidateSearchRepository:
    """Repository for searching candidate information in Neo4j."""
    
    def __init__(self, neo4j_connection):
        """Initialize with Neo4j connection."""
        self.neo4j = neo4j_connection
        self.logger = logging.getLogger(__name__)
    
    async def search_candidates(self, search_criteria: Dict[str, Any], page: int = 1, page_size: int = 10) -> Tuple[List[Dict], int]:
        """
        Tìm kiếm thí sinh theo nhiều tiêu chí.
        
        Args:
            search_criteria: Dictionary chứa các tiêu chí tìm kiếm
            page: Số trang
            page_size: Kích thước trang
            
        Returns:
            Tuple gồm danh sách thí sinh và tổng số kết quả
        """
        try:
            # Kiểm tra xem có ít nhất một thông tin định danh không
            if not search_criteria.get("candidate_id") and not search_criteria.get("id_number"):
                return [], 0
                
            # Tính toán skip dựa trên page và page_size
            skip = (page - 1) * page_size
            
            # Lấy tham số case_sensitive, mặc định là False
            case_sensitive = search_criteria.get("case_sensitive", False)
            
            # Xây dựng truy vấn Cypher
            query = """
            MATCH (c:Candidate:OntologyInstance)
            WHERE 
              // Nếu có mã thí sinh, phải khớp chính xác
              ($candidate_id IS NULL OR c.candidate_id = $candidate_id)
              // Nếu có số căn cước, phải khớp chính xác
              AND ($id_number IS NULL OR c.id_number = $id_number)
              // Nếu có tên, tùy theo case_sensitive
              AND ($full_name IS NULL OR 
                   CASE WHEN $case_sensitive THEN c.full_name = $full_name
                        ELSE toLower(c.full_name) = toLower($full_name)
                   END)
              // Nếu có cả mã thí sinh và số căn cước, phải khớp cả hai
              AND (
                ($candidate_id IS NOT NULL AND $id_number IS NOT NULL AND $full_name IS NOT NULL 
                 AND c.candidate_id = $candidate_id AND c.id_number = $id_number 
                 AND CASE WHEN $case_sensitive THEN c.full_name = $full_name
                         ELSE toLower(c.full_name) = toLower($full_name)
                    END)
                OR
                ($candidate_id IS NOT NULL AND $id_number IS NOT NULL AND $full_name IS NULL 
                 AND c.candidate_id = $candidate_id AND c.id_number = $id_number)
                OR
                ($candidate_id IS NOT NULL AND $id_number IS NULL AND $full_name IS NOT NULL 
                 AND c.candidate_id = $candidate_id 
                 AND CASE WHEN $case_sensitive THEN c.full_name = $full_name
                         ELSE toLower(c.full_name) = toLower($full_name)
                    END)
                OR
                ($candidate_id IS NULL AND $id_number IS NOT NULL AND $full_name IS NOT NULL 
                 AND c.id_number = $id_number 
                 AND CASE WHEN $case_sensitive THEN c.full_name = $full_name
                         ELSE toLower(c.full_name) = toLower($full_name)
                    END)
                OR
                ($candidate_id IS NOT NULL AND $id_number IS NULL AND $full_name IS NULL 
                 AND c.candidate_id = $candidate_id)
                OR
                ($candidate_id IS NULL AND $id_number IS NOT NULL AND $full_name IS NULL 
                 AND c.id_number = $id_number)
              )
              AND ($birth_date IS NULL OR c.birth_date = $birth_date)
              AND ($phone_number IS NULL OR c.phone_number = $phone_number)
              AND ($email IS NULL OR c.email = $email)
              AND ($address IS NULL OR c.address CONTAINS $address OR c.primary_address CONTAINS $address 
                   OR c.secondary_address CONTAINS $address)
            
            // Tìm theo mã số trong kỳ thi
            OPTIONAL MATCH (c)-[r:ATTENDS_EXAM]->(e:Exam)
            WHERE 
              ($registration_number IS NULL OR r.registration_number = $registration_number)
              AND ($exam_id IS NULL OR e.exam_id = $exam_id)
              
            // Tìm theo trường học
            OPTIONAL MATCH (c)-[rs:STUDIES_AT]->(s:School)
            WHERE $school_id IS NULL OR s.school_id = $school_id
              
            WITH c, COUNT(DISTINCT e) as exam_count, COUNT(DISTINCT s) as school_count
            WHERE 
              (($registration_number IS NULL AND $exam_id IS NULL) OR exam_count > 0)
              AND ($school_id IS NULL OR school_count > 0)
            
            WITH c, count(*) as total
            // Ưu tiên sắp xếp theo mã thí sinh và số căn cước trước
            ORDER BY 
              CASE WHEN $candidate_id IS NOT NULL AND c.candidate_id = $candidate_id THEN 0
                   WHEN $id_number IS NOT NULL AND c.id_number = $id_number THEN 1
                   ELSE 2 END,
              c.full_name
            SKIP $skip LIMIT $limit
            RETURN c, total
            """
            
            # Tham số truy vấn
            params = {
                "candidate_id": search_criteria.get("candidate_id"),
                "id_number": search_criteria.get("id_number"),
                "full_name": search_criteria.get("full_name"),
                "birth_date": search_criteria.get("birth_date"),
                "phone_number": search_criteria.get("phone_number"),
                "email": search_criteria.get("email"),
                "address": search_criteria.get("address"),
                "registration_number": search_criteria.get("registration_number"),
                "exam_id": search_criteria.get("exam_id"),
                "school_id": search_criteria.get("school_id"),
                "case_sensitive": case_sensitive,
                "skip": skip,
                "limit": page_size
            }
            
            # Thực thi truy vấn
            result = await self.neo4j.execute_query(query, params)
            
            candidates = []
            total = 0
            
            # Xử lý kết quả
            if result and len(result) > 0:
                for record in result:
                    candidate_node = record[0]
                    if not total and len(record) > 1:
                        total = record[1]
                    
                    # Chuyển đổi Node thành dictionary
                    candidate_dict = dict(candidate_node.items())
                    candidates.append(candidate_dict)
            
            return candidates, total
            
        except Exception as e:
            self.logger.error(f"Error searching candidates: {str(e)}", exc_info=True)
            return [], 0
    
    async def get_candidate_education_info(self, candidate_id: str) -> Dict[str, List]:
        """
        Lấy thông tin học vấn của thí sinh, bao gồm trường học, ngành học, và bằng cấp.
        
        Args:
            candidate_id: ID của thí sinh
            
        Returns:
            Dictionary chứa thông tin về trường học, ngành học, và bằng cấp
        """
        try:
            query = """
            // Tìm thí sinh
            MATCH (c:Candidate {candidate_id: $candidate_id})
            
            // Lấy thông tin trường học
            OPTIONAL MATCH (c)-[rs:STUDIES_AT]->(s:School)
            
            // Lấy thông tin ngành học
            OPTIONAL MATCH (c)-[rm:STUDIES_MAJOR]->(m:Major)
            
            // Lấy thông tin bằng cấp
            OPTIONAL MATCH (c)-[rd:HOLDS_DEGREE]->(d:Degree)
            
            RETURN 
              collect(DISTINCT {
                school_id: s.school_id,
                school_name: s.school_name,
                start_year: rs.start_year,
                end_year: rs.end_year,
                education_level: rs.education_level,
                academic_performance: rs.academic_performance,
                additional_info: rs.additional_info
              }) as schools,
              
              collect(DISTINCT {
                major_id: m.major_id,
                major_name: m.major_name,
                school_id: rm.school_id,
                school_name: rm.school_name,
                start_year: rm.start_year,
                end_year: rm.end_year
              }) as majors,
              
              collect(DISTINCT {
                degree_id: d.degree_id,
                degree_name: d.degree_name,
                issue_date: d.issue_date,
                issuing_organization: d.issuing_organization,
                major_id: d.major_id,
                major_name: d.major_name,
                school_id: d.school_id,
                school_name: d.school_name
              }) as degrees
            """
            
            result = await self.neo4j.execute_query(query, {"candidate_id": candidate_id})
            
            if not result or len(result) == 0:
                return {"schools": [], "majors": [], "degrees": []}
            
            record = result[0]
            
            # Xử lý kết quả, lọc các mục NULL
            schools = [s for s in record[0] if s.get("school_id") is not None]
            majors = [m for m in record[1] if m.get("major_id") is not None]
            degrees = [d for d in record[2] if d.get("degree_id") is not None]
            
            return {
                "schools": schools,
                "majors": majors,
                "degrees": degrees
            }
            
        except Exception as e:
            self.logger.error(f"Error getting education info for candidate {candidate_id}: {str(e)}", exc_info=True)
            return {"schools": [], "majors": [], "degrees": []}
    
    async def get_candidate_exams_info(self, candidate_id: str) -> Dict[str, List]:
        """
        Lấy thông tin kỳ thi của thí sinh, bao gồm các kỳ thi, lịch thi, điểm số, và thông tin phúc khảo.
        
        Args:
            candidate_id: ID của thí sinh
            
        Returns:
            Dictionary chứa thông tin về kỳ thi, lịch thi, điểm số, và phúc khảo
        """
        try:
            query = """
            // Tìm thí sinh
            MATCH (c:Candidate {candidate_id: $candidate_id})
            
            // Lấy thông tin kỳ thi
            OPTIONAL MATCH (c)-[re:ATTENDS_EXAM]->(e:Exam)
            
            // Lấy thông tin lịch thi
            OPTIONAL MATCH (c)-[rsch:HAS_EXAM_SCHEDULE]->(sch:ExamSchedule)
            
            // Lấy thông tin điểm thi
            OPTIONAL MATCH (c)-[rs:RECEIVES_SCORE]->(score:ExamScore)
            
            // Lấy thông tin phúc khảo
            OPTIONAL MATCH (c)-[rr:REQUESTS_REVIEW]->(review:ScoreReview)
            
            RETURN 
              collect(DISTINCT {
                exam_id: e.exam_id,
                exam_name: e.exam_name,
                registration_number: re.registration_number,
                registration_date: re.registration_date,
                status: re.status
              }) as exams,
              
              collect(DISTINCT {
                exam_schedule_id: sch.exam_schedule_id,
                exam_id: sch.exam_id,
                exam_name: sch.exam_name,
                subject_id: sch.subject_id,
                subject_name: sch.subject_name,
                room_id: rsch.room_id,
                room_name: rsch.room_name,
                exam_date: sch.exam_date,
                start_time: sch.start_time,
                end_time: sch.end_time
              }) as schedules,
              
              collect(DISTINCT {
                exam_score_id: score.exam_score_id,
                exam_id: rs.exam_id,
                exam_name: rs.exam_name,
                subject_id: rs.subject_id,
                subject_name: rs.subject_name,
                score: score.score,
                max_score: score.max_score,
                min_score: score.min_score,
                is_final: score.is_final
              }) as scores,
              
              collect(DISTINCT {
                review_id: review.review_id,
                exam_score_id: review.exam_score_id,
                subject_name: review.subject_name,
                original_score: review.original_score,
                reviewed_score: review.reviewed_score,
                status: review.status,
                request_date: review.request_date,
                completion_date: review.completion_date
              }) as reviews
            """
            
            result = await self.neo4j.execute_query(query, {"candidate_id": candidate_id})
            
            if not result or len(result) == 0:
                return {"exams": [], "schedules": [], "scores": [], "reviews": []}
            
            record = result[0]
            
            # Xử lý kết quả, lọc các mục NULL
            exams = [e for e in record[0] if e.get("exam_id") is not None]
            schedules = [s for s in record[1] if s.get("exam_schedule_id") is not None]
            scores = [s for s in record[2] if s.get("exam_score_id") is not None]
            reviews = [r for r in record[3] if r.get("review_id") is not None]
            
            return {
                "exams": exams,
                "schedules": schedules,
                "scores": scores,
                "reviews": reviews
            }
            
        except Exception as e:
            self.logger.error(f"Error getting exams info for candidate {candidate_id}: {str(e)}", exc_info=True)
            return {"exams": [], "schedules": [], "scores": [], "reviews": []}
    
    async def get_candidate_achievements_info(self, candidate_id: str) -> Dict[str, List]:
        """
        Lấy thông tin thành tích và giấy tờ của thí sinh.
        
        Args:
            candidate_id: ID của thí sinh
            
        Returns:
            Dictionary chứa thông tin về chứng chỉ, giấy tờ xác thực, giải thưởng, thành tích, và công nhận
        """
        try:
            query = """
            // Tìm thí sinh
            MATCH (c:Candidate {candidate_id: $candidate_id})
            
            // Lấy thông tin chứng chỉ
            OPTIONAL MATCH (c)-[rc:EARNS_CERTIFICATE]->(cert:Certificate)
            
            // Lấy thông tin giấy tờ xác thực
            OPTIONAL MATCH (c)-[rcred:PROVIDES_CREDENTIAL]->(cred:Credential)
            
            // Lấy thông tin giải thưởng
            OPTIONAL MATCH (c)-[ra:EARNS_AWARD]->(award:Award)
            
            // Lấy thông tin thành tích
            OPTIONAL MATCH (c)-[rach:ACHIEVES]->(ach:Achievement)
            
            // Lấy thông tin công nhận
            OPTIONAL MATCH (c)-[rrec:RECEIVES_RECOGNITION]->(rec:Recognition)
            
            RETURN 
              collect(DISTINCT {
                certificate_id: cert.certificate_id,
                certificate_name: cert.certificate_name,
                issue_date: cert.issue_date,
                issuing_organization: cert.issuing_organization,
                expiry_date: cert.expiry_date,
                certificate_code: cert.certificate_code
              }) as certificates,
              
              collect(DISTINCT {
                credential_id: cred.credential_id,
                title: cred.title,
                credential_type: cred.credential_type,
                issuing_organization: cred.issuing_organization,
                issue_date: cred.issue_date,
                expiry_date: cred.expiry_date,
                verification_status: cred.verification_status
              }) as credentials,
              
              collect(DISTINCT {
                award_id: award.award_id,
                award_name: award.award_name,
                award_level: award.award_level,
                issuing_organization: award.issuing_organization,
                issue_date: award.issue_date,
                description: award.description
              }) as awards,
              
              collect(DISTINCT {
                achievement_id: ach.achievement_id,
                achievement_name: ach.achievement_name,
                achievement_type: ach.achievement_type,
                description: ach.description,
                date_achieved: ach.date_achieved,
                issuing_organization: ach.issuing_organization
              }) as achievements,
              
              collect(DISTINCT {
                recognition_id: rec.recognition_id,
                recognition_type: rec.recognition_type,
                description: rec.description,
                issue_date: rec.issue_date,
                issuing_organization: rec.issuing_organization
              }) as recognitions
            """
            
            result = await self.neo4j.execute_query(query, {"candidate_id": candidate_id})
            
            if not result or len(result) == 0:
                return {
                    "certificates": [],
                    "credentials": [],
                    "awards": [],
                    "achievements": [],
                    "recognitions": []
                }
            
            record = result[0]
            
            # Xử lý kết quả, lọc các mục NULL
            certificates = [c for c in record[0] if c.get("certificate_id") is not None]
            credentials = [c for c in record[1] if c.get("credential_id") is not None]
            awards = [a for a in record[2] if a.get("award_id") is not None]
            achievements = [a for a in record[3] if a.get("achievement_id") is not None]
            recognitions = [r for r in record[4] if r.get("recognition_id") is not None]
            
            return {
                "certificates": certificates,
                "credentials": credentials,
                "awards": awards,
                "achievements": achievements,
                "recognitions": recognitions
            }
            
        except Exception as e:
            self.logger.error(f"Error getting achievements info for candidate {candidate_id}: {str(e)}", exc_info=True)
            return {
                "certificates": [],
                "credentials": [],
                "awards": [],
                "achievements": [],
                "recognitions": []
            }
    
    async def get_candidate_by_id(self, candidate_id: str) -> Optional[Dict[str, Any]]:
        """
        Lấy thông tin cơ bản của thí sinh theo ID.
        
        Args:
            candidate_id: ID của thí sinh
            
        Returns:
            Dictionary chứa thông tin cơ bản của thí sinh hoặc None nếu không tìm thấy
        """
        try:
            query = """
            MATCH (c:Candidate {candidate_id: $candidate_id})
            RETURN c
            """
            
            result = await self.neo4j.execute_query(query, {"candidate_id": candidate_id})
            
            if not result or len(result) == 0:
                return None
            
            candidate_node = result[0][0]
            return dict(candidate_node.items())
            
        except Exception as e:
            self.logger.error(f"Error getting candidate by ID {candidate_id}: {str(e)}", exc_info=True)
            return None 