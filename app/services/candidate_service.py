from app.repositories.candidate_repository import CandidateRepository
# Temporarily comment out Neo4j imports so the application can start
# from app.graph_repositories.candidate_graph_repository import CandidateGraphRepository
# from app.domain.graph_models.candidate_node import CandidateNode
from typing import List, Dict, Any, Optional
import logging

class CandidateService:
    """
    Service for handling business logic related to candidates
    """
    
    def __init__(self, candidate_repo: CandidateRepository):
        """
        Initialize Candidate Service
        
        Args:
            candidate_repo: Repository for interacting with candidate data
        """
        self.candidate_repo = candidate_repo
        self.logger = logging.getLogger(__name__)
    
    async def get_all_candidates(self, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get list of candidates
        
        Args:
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return
            
        Returns:
            List of serialized candidates
        """
        try:
            candidates = await self.candidate_repo.get_all(skip, limit)
            return [self._serialize_candidate(candidate) for candidate in candidates]
        except Exception as e:
            self.logger.error(f"Error getting all candidates: {e}")
            raise
    
    async def get_candidate_by_id(self, candidate_id: str) -> Optional[Dict[str, Any]]:
        """
        Get candidate information by ID
        
        Args:
            candidate_id: ID of the candidate
            
        Returns:
            Detailed information of the candidate or None if not found
        """
        try:
            candidate = await self.candidate_repo.get_by_id_with_personal_info(candidate_id)
            if not candidate:
                return None
            return self._serialize_candidate_with_details(candidate)
        except Exception as e:
            self.logger.error(f"Error getting candidate {candidate_id}: {e}")
            raise
    
    async def create_candidate(self, candidate_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new candidate
        
        Args:
            candidate_data: Data to create the candidate
            
        Returns:
            Information of the created candidate
        """
        try:
            candidate = await self.candidate_repo.create(candidate_data)
            return self._serialize_candidate_with_details(candidate)
        except Exception as e:
            self.logger.error(f"Error creating candidate: {e}")
            raise
    
    async def update_candidate(self, candidate_id: str, candidate_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Update candidate information
        
        Args:
            candidate_id: ID of the candidate to update
            candidate_data: Update data
            
        Returns:
            Information of the candidate after update or None if not found
        """
        try:
            candidate = await self.candidate_repo.update(candidate_id, candidate_data)
            
            if not candidate:
                return None
            
            # Get detailed information after update
            candidate = await self.candidate_repo.get_by_id_with_personal_info(candidate_id)
            return self._serialize_candidate_with_details(candidate)
        except Exception as e:
            self.logger.error(f"Error updating candidate {candidate_id}: {e}")
            raise
            
    async def update_candidate_personal_info(self, candidate_id: str, personal_info_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Update only the personal information of a candidate
        
        Args:
            candidate_id: ID of the candidate whose personal info to update
            personal_info_data: Personal information data to update
            
        Returns:
            Information of the candidate after update or None if not found
        """
        try:
            candidate = await self.candidate_repo.update_personal_info(candidate_id, personal_info_data)
            
            if not candidate:
                return None
                
            return self._serialize_candidate_with_details(candidate)
        except Exception as e:
            self.logger.error(f"Error updating personal info for candidate {candidate_id}: {e}")
            raise
    
    async def delete_candidate(self, candidate_id: str) -> bool:
        """
        Delete a candidate
        
        Args:
            candidate_id: ID of the candidate to delete
            
        Returns:
            True if deletion was successful, False if candidate not found
        """
        try:
            result = await self.candidate_repo.delete(candidate_id)
            return result
        except Exception as e:
            self.logger.error(f"Error deleting candidate {candidate_id}: {e}")
            raise
    
    async def search_candidates(self, search_term: str, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Search candidates by keyword
        
        Args:
            search_term: Search keyword
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return
            
        Returns:
            List of candidates matching the keyword
        """
        try:
            candidates = await self.candidate_repo.search(search_term, skip, limit)
            return [self._serialize_candidate(candidate) for candidate in candidates]
        except Exception as e:
            self.logger.error(f"Error searching candidates with term '{search_term}': {e}")
            raise
    
    async def get_candidate_education_history(self, candidate_id: str) -> List[Dict[str, Any]]:
        """Get education history of a candidate (from Neo4j)"""
        try:
            # Temporarily return empty array
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
        """Get exam history of a candidate (from Neo4j)"""
        try:
            # Temporarily return empty array
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
        """
        Convert model to basic dictionary
        
        Args:
            candidate: Candidate model
            
        Returns:
            Dictionary containing basic information of the candidate
        """
        return {
            "candidate_id": candidate.candidate_id,
            "full_name": candidate.full_name
        }
    
    def _serialize_candidate_with_details(self, candidate) -> Dict[str, Any]:
        """
        Convert model to dictionary with detailed information
        
        Args:
            candidate: Candidate model
            
        Returns:
            Dictionary containing detailed information of the candidate including personal information
        """
        result = self._serialize_candidate(candidate)
        
        if hasattr(candidate, 'personal_info') and candidate.personal_info:
            personal_info = candidate.personal_info
            result["personal_info"] = {
                "birth_date": personal_info.birth_date,
                "id_number": personal_info.id_number,
                "phone_number": personal_info.phone_number,
                "email": personal_info.email,
                "primary_address": personal_info.primary_address,
                "secondary_address": personal_info.secondary_address,
                "id_card_image_url": personal_info.id_card_image_url,
                "candidate_card_image_url": personal_info.candidate_card_image_url,
                "face_recognition_data_url": personal_info.face_recognition_data_url
            }
        else:
            result["personal_info"] = None
        
        return result 