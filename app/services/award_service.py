"""
Award service module.

This module contains business logic for handling award operations,
using the repository layer for data access.
"""

from app.repositories.award_repository import AwardRepository
from app.repositories.candidate_exam_repository import CandidateExamRepository
from typing import List, Dict, Any, Optional, Tuple
from datetime import date
import logging

class AwardService:
    """
    Service for handling business logic related to awards
    """
    
    def __init__(
        self, 
        award_repo: AwardRepository,
        candidate_exam_repo: Optional[CandidateExamRepository] = None
    ):
        """
        Initialize Award Service
        
        Args:
            award_repo: Repository for interacting with award data
            candidate_exam_repo: Repository for interacting with candidate exam data
        """
        self.award_repo = award_repo
        self.candidate_exam_repo = candidate_exam_repo
        self.logger = logging.getLogger(__name__)
    
    async def get_all_awards(
        self, 
        skip: int = 0, 
        limit: int = 100,
        candidate_exam_id: Optional[str] = None,
        award_type: Optional[str] = None,
        education_level: Optional[str] = None,
        award_date_from: Optional[date] = None,
        award_date_to: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        Get list of awards with pagination and filtering
        
        Args:
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return
            candidate_exam_id: Filter by candidate exam ID
            award_type: Filter by award type
            education_level: Filter by education level
            award_date_from: Filter by minimum award date
            award_date_to: Filter by maximum award date
            
        Returns:
            Dictionary containing list of awards and pagination metadata
        """
        try:
            # Construct filters dictionary
            filters = {}
            if candidate_exam_id:
                filters['candidate_exam_id'] = candidate_exam_id
            if award_type:
                filters['award_type'] = award_type
            if education_level:
                filters['education_level'] = education_level
            if award_date_from:
                filters['award_date_from'] = award_date_from
            if award_date_to:
                filters['award_date_to'] = award_date_to
                
            awards, total = await self.award_repo.get_all(skip, limit, filters)
            
            # Calculate pagination metadata
            page = skip // limit + 1 if limit else 1
            
            # Convert to serialized response
            return {
                "items": [self._serialize_award(award) for award in awards],
                "total": total,
                "page": page,
                "size": limit
            }
        except Exception as e:
            self.logger.error(f"Error getting all awards: {e}")
            raise
    
    async def get_award_by_id(self, award_id: str) -> Optional[Dict[str, Any]]:
        """
        Get an award by its ID
        
        Args:
            award_id: ID of the award to retrieve
            
        Returns:
            Dictionary containing award details or None if not found
        """
        try:
            award = await self.award_repo.get_by_id(award_id)
            if not award:
                return None
            
            return self._serialize_award(award)
        except Exception as e:
            self.logger.error(f"Error getting award {award_id}: {e}")
            raise
    
    async def get_awards_by_candidate_exam(
        self, 
        candidate_exam_id: str, 
        skip: int = 0, 
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        Get all awards for a specific candidate exam
        
        Args:
            candidate_exam_id: ID of the candidate exam
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return
            
        Returns:
            Dictionary containing list of awards and pagination metadata
        """
        try:
            awards, total = await self.award_repo.get_by_candidate_exam(
                candidate_exam_id, skip, limit
            )
            
            # Calculate pagination metadata
            page = skip // limit + 1 if limit else 1
            
            # Convert to serialized response
            return {
                "items": [self._serialize_award(award) for award in awards],
                "total": total,
                "page": page,
                "size": limit
            }
        except Exception as e:
            self.logger.error(f"Error getting awards for candidate exam {candidate_exam_id}: {e}")
            raise
    
    async def get_awards_by_candidate_id(
        self, 
        candidate_id: str, 
        skip: int = 0, 
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        Get all awards for a specific candidate across all exams
        
        Args:
            candidate_id: ID of the candidate
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return
            
        Returns:
            Dictionary containing list of awards and pagination metadata
        """
        try:
            # Verify that we have the required repository
            if not self.candidate_exam_repo:
                self.logger.error("Cannot get awards by candidate ID: candidate_exam_repo not provided")
                return {
                    "items": [],
                    "total": 0,
                    "page": 1,
                    "size": limit
                }
            
            # Get all candidate-exam registrations for this candidate
            candidate_exams = await self.candidate_exam_repo.get_by_candidate_id(candidate_id)
            
            # No registrations found
            if not candidate_exams:
                self.logger.info(f"No exam registrations found for candidate ID {candidate_id}")
                return {
                    "items": [],
                    "total": 0,
                    "page": 1,
                    "size": limit
                }
            
            # Collect all awards from all candidate-exam registrations
            all_awards = []
            total_count = 0
            
            for candidate_exam in candidate_exams:
                awards, count = await self.award_repo.get_by_candidate_exam(
                    candidate_exam["candidate_exam_id"], 0, 1000  # Get all awards
                )
                
                for award in awards:
                    # Add exam name to the award for context
                    serialized_award = self._serialize_award(award)
                    serialized_award["exam_name"] = candidate_exam.get("exam_name", "Unknown Exam")
                    all_awards.append(serialized_award)
                
                total_count += count
            
            # Apply pagination to the combined result
            start_idx = skip
            end_idx = min(skip + limit, len(all_awards))
            paginated_awards = all_awards[start_idx:end_idx] if start_idx < len(all_awards) else []
            
            return {
                "items": paginated_awards,
                "total": total_count,
                "page": skip // limit + 1 if limit > 0 else 1,
                "size": limit
            }
        except Exception as e:
            self.logger.error(f"Error getting awards for candidate {candidate_id}: {e}")
            raise
    
    async def get_awards_by_award_type(
        self, 
        award_type: str, 
        skip: int = 0, 
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        Get all awards of a specific type
        
        Args:
            award_type: Type of the award (First, Second, Third, etc.)
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return
            
        Returns:
            Dictionary containing list of awards and pagination metadata
        """
        try:
            awards, total = await self.award_repo.get_by_award_type(
                award_type, skip, limit
            )
            
            # Calculate pagination metadata
            page = skip // limit + 1 if limit else 1
            
            # Convert to serialized response
            return {
                "items": [self._serialize_award(award) for award in awards],
                "total": total,
                "page": page,
                "size": limit
            }
        except Exception as e:
            self.logger.error(f"Error getting awards for award type {award_type}: {e}")
            raise
    
    async def create_award(self, award_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new award
        
        Args:
            award_data: Dictionary containing award data
            
        Returns:
            Dictionary containing created award details
        """
        try:
            award = await self.award_repo.create(award_data)
            # Just return the basic award data without trying to access relationships
            return {
                "award_id": award.award_id,
                "candidate_exam_id": award.candidate_exam_id,
                "award_type": award.award_type,
                "achievement": award.achievement,
                "certificate_image_url": award.certificate_image_url,
                "education_level": award.education_level,
                "award_date": award.award_date,
                "additional_info": award.additional_info,
                "created_at": award.created_at,
                "updated_at": award.updated_at,
                "candidate_name": None,
                "exam_name": None
            }
        except Exception as e:
            self.logger.error(f"Error creating award: {e}")
            raise
    
    async def update_award(
        self, 
        award_id: str, 
        award_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Update an existing award
        
        Args:
            award_id: ID of the award to update
            award_data: Dictionary containing updated data
            
        Returns:
            Dictionary containing updated award details or None if not found
        """
        try:
            award = await self.award_repo.update(
                award_id, 
                award_data
            )
            if not award:
                return None
            
            return self._serialize_award(award)
        except Exception as e:
            self.logger.error(f"Error updating award {award_id}: {e}")
            raise
    
    async def delete_award(self, award_id: str) -> bool:
        """
        Delete an award
        
        Args:
            award_id: ID of the award to delete
            
        Returns:
            True if deleted successfully, False if not found
        """
        try:
            return await self.award_repo.delete(award_id)
        except Exception as e:
            self.logger.error(f"Error deleting award {award_id}: {e}")
            raise
    
    def _serialize_award(self, award) -> Dict[str, Any]:
        """
        Convert award model to dictionary with detailed information
        
        Args:
            award: Award model object
            
        Returns:
            Dictionary containing award information
        """
        data = {
            "award_id": award.award_id,
            "candidate_exam_id": award.candidate_exam_id,
            "award_type": award.award_type,
            "achievement": award.achievement,
            "certificate_image_url": award.certificate_image_url,
            "education_level": award.education_level,
            "award_date": award.award_date,
            "additional_info": award.additional_info,
            "created_at": award.created_at,
            "updated_at": award.updated_at,
            # Set default values for related information
            "candidate_name": None,
            "exam_name": None
        }
        
        # Safely add candidate name and exam name if available
        try:
            if hasattr(award, 'candidate_exam') and award.candidate_exam:
                if hasattr(award.candidate_exam, 'candidate') and award.candidate_exam.candidate:
                    data["candidate_name"] = award.candidate_exam.candidate.full_name
                
                if hasattr(award.candidate_exam, 'exam') and award.candidate_exam.exam:
                    data["exam_name"] = award.candidate_exam.exam.exam_name
        except Exception as e:
            # Log but don't fail if there's an issue accessing relationships
            self.logger.warning(f"Error accessing relationships for award {award.award_id}: {e}")
        
        return data 