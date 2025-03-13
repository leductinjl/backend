from app.repositories.candidate_repository import CandidateRepository
# Tạm thời comment các import Neo4j để ứng dụng có thể khởi động
# from app.graph_repositories.candidate_graph_repository import CandidateGraphRepository
# from app.domain.graph_models.candidate_node import CandidateNode
from typing import List, Dict, Any, Optional
import logging

class CandidateService:
    """
    Service xử lý logic nghiệp vụ liên quan đến thí sinh
    """
    
    def __init__(self, candidate_repo: CandidateRepository, candidate_graph_repo=None):
        self.candidate_repo = candidate_repo
        self.candidate_graph_repo = candidate_graph_repo
        self.logger = logging.getLogger(__name__)
    
    async def get_all_candidates(self, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """Lấy danh sách thí sinh"""
        try:
            candidates = await self.candidate_repo.get_all(skip, limit)
            return [self._serialize_candidate(candidate) for candidate in candidates]
        except Exception as e:
            self.logger.error(f"Error getting all candidates: {e}")
            raise
    
    async def get_candidate_by_id(self, candidate_id: str) -> Optional[Dict[str, Any]]:
        """Lấy thông tin thí sinh theo ID"""
        try:
            candidate = await self.candidate_repo.get_by_id_with_personal_info(candidate_id)
            if not candidate:
                return None
            return self._serialize_candidate_with_details(candidate)
        except Exception as e:
            self.logger.error(f"Error getting candidate {candidate_id}: {e}")
            raise
    
    async def create_candidate(self, candidate_data: Dict[str, Any]) -> Dict[str, Any]:
        """Tạo thí sinh mới"""
        try:
            # Xử lý dữ liệu PostgreSQL
            candidate = await self.candidate_repo.create(candidate_data)
            
            # Tạm thời comment phần xử lý Neo4j
            """
            # Tạo node trong Neo4j
            if candidate and self.candidate_graph_repo:
                candidate_node = CandidateNode(
                    candidate_id=candidate.candidate_id,
                    full_name=candidate.full_name
                )
                await self.candidate_graph_repo.create_or_update(candidate_node)
            """
            
            return self._serialize_candidate(candidate)
        except Exception as e:
            self.logger.error(f"Error creating candidate: {e}")
            raise
    
    async def update_candidate(self, candidate_id: str, candidate_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Cập nhật thông tin thí sinh"""
        try:
            # Cập nhật trong PostgreSQL
            candidate = await self.candidate_repo.update(candidate_id, candidate_data)
            
            # Tạm thời comment phần xử lý Neo4j
            """
            # Cập nhật node trong Neo4j
            if candidate and self.candidate_graph_repo:
                candidate_node = CandidateNode(
                    candidate_id=candidate.candidate_id,
                    full_name=candidate.full_name
                )
                await self.candidate_graph_repo.create_or_update(candidate_node)
            """
            
            if not candidate:
                return None
            
            return self._serialize_candidate(candidate)
        except Exception as e:
            self.logger.error(f"Error updating candidate {candidate_id}: {e}")
            raise
    
    async def delete_candidate(self, candidate_id: str) -> bool:
        """Xóa thí sinh"""
        try:
            # Tạm thời comment phần xử lý Neo4j
            """
            # Xóa node trong Neo4j
            if self.candidate_graph_repo:
                await self.candidate_graph_repo.delete(candidate_id)
            """
            
            # Xóa trong PostgreSQL
            result = await self.candidate_repo.delete(candidate_id)
            return result
        except Exception as e:
            self.logger.error(f"Error deleting candidate {candidate_id}: {e}")
            raise
    
    async def search_candidates(self, search_term: str, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """Tìm kiếm thí sinh theo từ khóa"""
        try:
            candidates = await self.candidate_repo.search(search_term, skip, limit)
            return [self._serialize_candidate(candidate) for candidate in candidates]
        except Exception as e:
            self.logger.error(f"Error searching candidates with term '{search_term}': {e}")
            raise
    
    async def get_candidate_education_history(self, candidate_id: str) -> List[Dict[str, Any]]:
        """Lấy lịch sử học tập của thí sinh (từ Neo4j)"""
        try:
            # Tạm thời trả về mảng rỗng
            return []
            """
            if not self.candidate_graph_repo:
                return []
            
            education_history = await self.candidate_graph_repo.get_education_history(candidate_id)
            return education_history
            """
        except Exception as e:
            self.logger.error(f"Error getting education history for candidate {candidate_id}: {e}")
            raise
    
    async def get_candidate_exam_history(self, candidate_id: str) -> List[Dict[str, Any]]:
        """Lấy lịch sử thi của thí sinh (từ Neo4j)"""
        try:
            # Tạm thời trả về mảng rỗng
            return []
            """
            if not self.candidate_graph_repo:
                return []
            
            exam_history = await self.candidate_graph_repo.get_exam_history(candidate_id)
            return exam_history
            """
        except Exception as e:
            self.logger.error(f"Error getting exam history for candidate {candidate_id}: {e}")
            raise
    
    def _serialize_candidate(self, candidate) -> Dict[str, Any]:
        """Chuyển đổi model thành dictionary"""
        return {
            "candidate_id": candidate.candidate_id,
            "full_name": candidate.full_name
        }
    
    def _serialize_candidate_with_details(self, candidate) -> Dict[str, Any]:
        """Chuyển đổi model thành dictionary với thông tin chi tiết"""
        result = self._serialize_candidate(candidate)
        
        if hasattr(candidate, 'personal_info') and candidate.personal_info:
            personal_info = candidate.personal_info
            result.update({
                "birth_date": personal_info.birth_date,
                "id_number": personal_info.id_number,
                "phone_number": personal_info.phone_number,
                "email": personal_info.email,
                "primary_address": personal_info.primary_address,
                "secondary_address": personal_info.secondary_address
            })
        
        return result 