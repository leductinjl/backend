"""
Achievement service module.

This module contains business logic for handling achievement operations,
using the repository layer for data access.
"""

from app.repositories.achievement_repository import AchievementRepository
from typing import List, Dict, Any, Optional, Tuple
from datetime import date
import logging

class AchievementService:
    """
    Service for handling business logic related to achievements
    """
    
    def __init__(self, achievement_repo: AchievementRepository):
        """
        Initialize Achievement Service
        
        Args:
            achievement_repo: Repository for interacting with achievement data
        """
        self.achievement_repo = achievement_repo
        self.logger = logging.getLogger(__name__)
    
    async def get_all_achievements(
        self, 
        skip: int = 0, 
        limit: int = 100,
        candidate_exam_id: Optional[str] = None,
        achievement_type: Optional[str] = None,
        organization: Optional[str] = None,
        education_level: Optional[str] = None,
        achievement_date_from: Optional[date] = None,
        achievement_date_to: Optional[date] = None,
        search: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get list of achievements with pagination and filtering
        
        Args:
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return
            candidate_exam_id: Filter by candidate exam ID
            achievement_type: Filter by achievement type
            organization: Filter by organization
            education_level: Filter by education level
            achievement_date_from: Filter by minimum achievement date
            achievement_date_to: Filter by maximum achievement date
            search: Search term for achievement name
            
        Returns:
            Dictionary containing list of achievements and pagination metadata
        """
        try:
            # Construct filters dictionary
            filters = {}
            if candidate_exam_id:
                filters['candidate_exam_id'] = candidate_exam_id
            if achievement_type:
                filters['achievement_type'] = achievement_type
            if organization:
                filters['organization'] = organization
            if education_level:
                filters['education_level'] = education_level
            if achievement_date_from:
                filters['achievement_date_from'] = achievement_date_from
            if achievement_date_to:
                filters['achievement_date_to'] = achievement_date_to
            if search:
                filters['search'] = search
                
            achievements, total = await self.achievement_repo.get_all(skip, limit, filters)
            
            # Calculate pagination metadata
            page = skip // limit + 1 if limit else 1
            
            # Convert to serialized response
            return {
                "items": [self._serialize_achievement(achievement) for achievement in achievements],
                "total": total,
                "page": page,
                "size": limit
            }
        except Exception as e:
            self.logger.error(f"Error getting all achievements: {e}")
            raise
    
    async def get_achievement_by_id(self, achievement_id: str) -> Optional[Dict[str, Any]]:
        """
        Get an achievement by its ID
        
        Args:
            achievement_id: ID of the achievement to retrieve
            
        Returns:
            Dictionary containing achievement details or None if not found
        """
        try:
            achievement = await self.achievement_repo.get_by_id(achievement_id)
            if not achievement:
                return None
            
            return self._serialize_achievement(achievement)
        except Exception as e:
            self.logger.error(f"Error getting achievement {achievement_id}: {e}")
            raise
    
    async def get_achievements_by_candidate_exam(
        self, 
        candidate_exam_id: str, 
        skip: int = 0, 
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        Get all achievements for a specific candidate exam
        
        Args:
            candidate_exam_id: ID of the candidate exam
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return
            
        Returns:
            Dictionary containing list of achievements and pagination metadata
        """
        try:
            achievements, total = await self.achievement_repo.get_by_candidate_exam(
                candidate_exam_id, skip, limit
            )
            
            # Calculate pagination metadata
            page = skip // limit + 1 if limit else 1
            
            # Convert to serialized response
            return {
                "items": [self._serialize_achievement(achievement) for achievement in achievements],
                "total": total,
                "page": page,
                "size": limit
            }
        except Exception as e:
            self.logger.error(f"Error getting achievements for candidate exam {candidate_exam_id}: {e}")
            raise
    
    async def get_achievements_by_achievement_type(
        self, 
        achievement_type: str, 
        skip: int = 0, 
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        Get all achievements of a specific type
        
        Args:
            achievement_type: Type of the achievement (Research, Community Service, etc.)
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return
            
        Returns:
            Dictionary containing list of achievements and pagination metadata
        """
        try:
            achievements, total = await self.achievement_repo.get_by_achievement_type(
                achievement_type, skip, limit
            )
            
            # Calculate pagination metadata
            page = skip // limit + 1 if limit else 1
            
            # Convert to serialized response
            return {
                "items": [self._serialize_achievement(achievement) for achievement in achievements],
                "total": total,
                "page": page,
                "size": limit
            }
        except Exception as e:
            self.logger.error(f"Error getting achievements for achievement type {achievement_type}: {e}")
            raise
    
    async def get_achievements_by_organization(
        self, 
        organization: str, 
        skip: int = 0, 
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        Get all achievements recognized by a specific organization
        
        Args:
            organization: Name of the organization
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return
            
        Returns:
            Dictionary containing list of achievements and pagination metadata
        """
        try:
            achievements, total = await self.achievement_repo.get_by_organization(
                organization, skip, limit
            )
            
            # Calculate pagination metadata
            page = skip // limit + 1 if limit else 1
            
            # Convert to serialized response
            return {
                "items": [self._serialize_achievement(achievement) for achievement in achievements],
                "total": total,
                "page": page,
                "size": limit
            }
        except Exception as e:
            self.logger.error(f"Error getting achievements for organization {organization}: {e}")
            raise
    
    async def create_achievement(self, achievement_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new achievement
        
        Args:
            achievement_data: Dictionary containing achievement data
            
        Returns:
            Dictionary containing created achievement details
        """
        try:
            # Don't set achievement_id here, let the repository handle it
            if 'achievement_id' in achievement_data and not achievement_data['achievement_id']:
                del achievement_data['achievement_id']
                
            self.logger.info(f"Creating achievement for candidate_exam_id: {achievement_data.get('candidate_exam_id')}")
            achievement = await self.achievement_repo.create(achievement_data)
            self.logger.info(f"Successfully created achievement with ID: {achievement.achievement_id}")
            
            # Return basic achievement data to avoid potential relationship loading issues
            return {
                "achievement_id": achievement.achievement_id,
                "candidate_exam_id": achievement.candidate_exam_id,
                "achievement_name": achievement.achievement_name,
                "achievement_type": achievement.achievement_type,
                "description": achievement.description,
                "achievement_date": achievement.achievement_date,
                "organization": achievement.organization,
                "proof_url": achievement.proof_url,
                "education_level": achievement.education_level,
                "additional_info": achievement.additional_info,
                "created_at": achievement.created_at,
                "updated_at": achievement.updated_at,
                "candidate_name": None,
                "exam_name": None
            }
        except Exception as e:
            self.logger.error(f"Error creating achievement: {e}")
            raise
    
    async def update_achievement(
        self, 
        achievement_id: str, 
        achievement_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Update an existing achievement
        
        Args:
            achievement_id: ID of the achievement to update
            achievement_data: Dictionary containing updated data
            
        Returns:
            Dictionary containing updated achievement details or None if not found
        """
        try:
            achievement = await self.achievement_repo.update(
                achievement_id, 
                achievement_data
            )
            if not achievement:
                return None
            
            return self._serialize_achievement(achievement)
        except Exception as e:
            self.logger.error(f"Error updating achievement {achievement_id}: {e}")
            raise
    
    async def delete_achievement(self, achievement_id: str) -> bool:
        """
        Delete an achievement
        
        Args:
            achievement_id: ID of the achievement to delete
            
        Returns:
            True if deleted successfully, False if not found
        """
        try:
            return await self.achievement_repo.delete(achievement_id)
        except Exception as e:
            self.logger.error(f"Error deleting achievement {achievement_id}: {e}")
            raise
    
    def _serialize_achievement(self, achievement) -> Dict[str, Any]:
        """
        Convert achievement model to dictionary with detailed information
        
        Args:
            achievement: Achievement model object
            
        Returns:
            Dictionary containing achievement information
        """
        data = {
            "achievement_id": achievement.achievement_id,
            "candidate_exam_id": achievement.candidate_exam_id,
            "achievement_name": achievement.achievement_name,
            "achievement_type": achievement.achievement_type,
            "description": achievement.description,
            "achievement_date": achievement.achievement_date,
            "organization": achievement.organization,
            "proof_url": achievement.proof_url,
            "education_level": achievement.education_level,
            "additional_info": achievement.additional_info,
            "created_at": achievement.created_at,
            "updated_at": achievement.updated_at,
            # Set default values for related information
            "candidate_name": None,
            "exam_name": None
        }
        
        # Safely add candidate name and exam name if available
        try:
            if hasattr(achievement, 'candidate_exam') and achievement.candidate_exam:
                if hasattr(achievement.candidate_exam, 'candidate') and achievement.candidate_exam.candidate:
                    data["candidate_name"] = achievement.candidate_exam.candidate.full_name
                
                if hasattr(achievement.candidate_exam, 'exam') and achievement.candidate_exam.exam:
                    data["exam_name"] = achievement.candidate_exam.exam.exam_name
        except Exception as e:
            # Log but don't fail if there's an issue accessing relationships
            self.logger.warning(f"Error accessing relationships for achievement {achievement.achievement_id}: {e}")
        
        return data 