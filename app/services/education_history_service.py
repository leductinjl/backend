"""
Education History service module.

This module contains business logic for handling education history operations,
using the repository layer for data access.
"""

from app.repositories.education_history_repository import EducationHistoryRepository
from typing import List, Dict, Any, Optional, Tuple
import logging

class EducationHistoryService:
    """
    Service for handling business logic related to education history
    """
    
    def __init__(self, education_history_repo: EducationHistoryRepository):
        """
        Initialize Education History Service
        
        Args:
            education_history_repo: Repository for interacting with education history data
        """
        self.education_history_repo = education_history_repo
        self.logger = logging.getLogger(__name__)
    
    async def get_all_education_histories(
        self, 
        skip: int = 0, 
        limit: int = 100,
        candidate_id: Optional[str] = None,
        school_id: Optional[str] = None,
        education_level_id: Optional[str] = None,
        start_year: Optional[int] = None,
        end_year: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get all education histories with pagination and filtering
        
        Args:
            skip: Number of records to skip for pagination
            limit: Maximum number of records to return
            candidate_id: Filter by candidate ID
            school_id: Filter by school ID
            education_level_id: Filter by education level ID
            start_year: Filter by start year
            end_year: Filter by end year
        
        Returns:
            Dictionary with education histories and pagination information
        """
        try:
            education_histories, total = await self.education_history_repo.get_all(
                skip=skip,
                limit=limit,
                candidate_id=candidate_id,
                school_id=school_id,
                education_level_id=education_level_id,
                start_year=start_year,
                end_year=end_year
            )
            
            # Calculate pagination metadata
            page = skip // limit + 1 if limit else 1
            
            # Convert to serialized response
            return {
                "items": [self._serialize_education_history(history) for history in education_histories],
                "total": total,
                "page": page,
                "size": limit
            }
        except Exception as e:
            self.logger.error(f"Error getting all education histories: {e}")
            raise
    
    async def get_education_history_by_id(self, education_history_id: str) -> Optional[Dict[str, Any]]:
        """
        Get an education history entry by its ID
        
        Args:
            education_history_id: ID of the education history to retrieve
            
        Returns:
            Dictionary containing education history details or None if not found
        """
        try:
            education_history = await self.education_history_repo.get_by_id(education_history_id)
            if not education_history:
                return None
            
            return self._serialize_education_history(education_history)
        except Exception as e:
            self.logger.error(f"Error getting education history {education_history_id}: {e}")
            raise
    
    async def get_education_histories_by_candidate(
        self, 
        candidate_id: str, 
        skip: int = 0, 
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        Get all education history entries for a specific candidate
        
        Args:
            candidate_id: ID of the candidate
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return
            
        Returns:
            Dictionary containing list of education history entries and pagination metadata
        """
        try:
            histories, total = await self.education_history_repo.get_by_candidate(candidate_id, skip, limit)
            
            # Calculate pagination metadata
            page = skip // limit + 1 if limit else 1
            
            # Convert to serialized response
            return {
                "items": [self._serialize_education_history(history) for history in histories],
                "total": total,
                "page": page,
                "size": limit
            }
        except Exception as e:
            self.logger.error(f"Error getting education histories for candidate {candidate_id}: {e}")
            raise
    
    async def get_education_histories_by_school(
        self, 
        school_id: str, 
        skip: int = 0, 
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        Get all education history entries for a specific school
        
        Args:
            school_id: ID of the school
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return
            
        Returns:
            Dictionary containing list of education history entries and pagination metadata
        """
        try:
            histories, total = await self.education_history_repo.get_by_school(school_id, skip, limit)
            
            # Calculate pagination metadata
            page = skip // limit + 1 if limit else 1
            
            # Convert to serialized response
            return {
                "items": [self._serialize_education_history(history) for history in histories],
                "total": total,
                "page": page,
                "size": limit
            }
        except Exception as e:
            self.logger.error(f"Error getting education histories for school {school_id}: {e}")
            raise
    
    async def create_education_history(self, education_history_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new education history entry
        
        Args:
            education_history_data: Dictionary containing education history data
            
        Returns:
            Dictionary containing created education history details
        """
        try:
            education_history = await self.education_history_repo.create(education_history_data)
            return self._serialize_education_history(education_history)
        except Exception as e:
            self.logger.error(f"Error creating education history: {e}")
            raise
    
    async def update_education_history(
        self, 
        education_history_id: str, 
        education_history_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Update an existing education history entry
        
        Args:
            education_history_id: ID of the education history to update
            education_history_data: Dictionary containing updated data
            
        Returns:
            Dictionary containing updated education history details or None if not found
        """
        try:
            education_history = await self.education_history_repo.update(
                education_history_id, 
                education_history_data
            )
            if not education_history:
                return None
            
            return self._serialize_education_history(education_history)
        except Exception as e:
            self.logger.error(f"Error updating education history {education_history_id}: {e}")
            raise
    
    async def delete_education_history(self, education_history_id: str) -> bool:
        """
        Delete an education history entry
        
        Args:
            education_history_id: ID of the education history to delete
            
        Returns:
            True if deleted successfully, False if not found
        """
        try:
            return await self.education_history_repo.delete(education_history_id)
        except Exception as e:
            self.logger.error(f"Error deleting education history {education_history_id}: {e}")
            raise
    
    def _serialize_education_history(self, education_history) -> Dict[str, Any]:
        """
        Convert education history model to dictionary format
        
        Args:
            education_history: EducationHistory model instance
            
        Returns:
            Dictionary with education history data and related entities
        """
        # Convert date objects to integers for year fields
        start_year = education_history.start_year.year if education_history.start_year else None
        end_year = education_history.end_year.year if education_history.end_year else None
        
        # Base data
        data = {
            "education_history_id": education_history.education_history_id,
            "candidate_id": education_history.candidate_id,
            "school_id": education_history.school_id,
            "education_level_id": education_history.education_level_id,
            "start_year": start_year,
            "end_year": end_year,
            "academic_performance": education_history.academic_performance,
            "additional_info": education_history.additional_info,
            "created_at": education_history.created_at,
            "updated_at": education_history.updated_at,
            
            # Add related data if available
            "candidate_name": getattr(education_history.candidate, "full_name", None) if hasattr(education_history, "candidate") and education_history.candidate else None,
            "school_name": getattr(education_history.school, "school_name", None) if hasattr(education_history, "school") and education_history.school else None,
            "education_level_name": getattr(education_history.education_level, "name", None) if hasattr(education_history, "education_level") and education_history.education_level else None,
        }
        
        return data 