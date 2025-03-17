"""
Education Level service module.

This module handles business logic for education level operations,
using the repository layer for data access.
"""

from app.repositories.education_level_repository import EducationLevelRepository
from typing import Dict, List, Optional, Tuple, Any
import logging

class EducationLevelService:
    """Service for managing education level data."""
    
    def __init__(self, repository: EducationLevelRepository):
        """
        Initialize the service with a repository.
        
        Args:
            repository: EducationLevelRepository instance
        """
        self.repository = repository
        self.logger = logging.getLogger(__name__)
        
    async def get_all_education_levels(
        self, 
        skip: int = 0, 
        limit: int = 100, 
        code: Optional[str] = None,
        name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Retrieve a paginated list of education levels with optional filtering.
        
        Args:
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return
            code: Filter by code (partial match)
            name: Filter by name (partial match)
            
        Returns:
            Dictionary with items, total count, page and size
        """
        try:
            education_levels, total = await self.repository.get_all(
                skip=skip, 
                limit=limit, 
                code=code,
                name=name
            )
            
            return {
                "items": [self._serialize_education_level(level) for level in education_levels],
                "total": total,
                "page": skip // limit + 1 if limit else 1,
                "size": limit
            }
        except Exception as e:
            self.logger.error(f"Error getting education levels: {str(e)}")
            raise
            
    async def get_education_level_by_id(self, education_level_id: str) -> Optional[Dict[str, Any]]:
        """
        Get an education level by ID.
        
        Args:
            education_level_id: ID of the education level to retrieve
            
        Returns:
            Serialized education level or None if not found
        """
        try:
            education_level = await self.repository.get_by_id(education_level_id)
            if not education_level:
                return None
                
            return self._serialize_education_level(education_level)
        except Exception as e:
            self.logger.error(f"Error getting education level with ID {education_level_id}: {str(e)}")
            raise
            
    async def get_education_level_by_code(self, code: str) -> Optional[Dict[str, Any]]:
        """
        Get an education level by its code.
        
        Args:
            code: Unique code of the education level
            
        Returns:
            Serialized education level or None if not found
        """
        try:
            education_level = await self.repository.get_by_code(code)
            if not education_level:
                return None
                
            return self._serialize_education_level(education_level)
        except Exception as e:
            self.logger.error(f"Error getting education level with code {code}: {str(e)}")
            raise
            
    async def create_education_level(self, education_level_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new education level.
        
        Args:
            education_level_data: Dictionary with education level data
            
        Returns:
            Serialized created education level
        """
        try:
            education_level = await self.repository.create(education_level_data)
            return self._serialize_education_level(education_level)
        except Exception as e:
            self.logger.error(f"Error creating education level: {str(e)}")
            raise
            
    async def update_education_level(
        self, 
        education_level_id: str, 
        education_level_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Update an education level by ID.
        
        Args:
            education_level_id: ID of the education level to update
            education_level_data: Dictionary with updated data
            
        Returns:
            Serialized updated education level or None if not found
        """
        try:
            education_level = await self.repository.update(education_level_id, education_level_data)
            if not education_level:
                return None
                
            return self._serialize_education_level(education_level)
        except Exception as e:
            self.logger.error(f"Error updating education level with ID {education_level_id}: {str(e)}")
            raise
            
    async def delete_education_level(self, education_level_id: str) -> bool:
        """
        Delete an education level by ID.
        
        Args:
            education_level_id: ID of the education level to delete
            
        Returns:
            Boolean indicating success
        """
        try:
            return await self.repository.delete(education_level_id)
        except Exception as e:
            self.logger.error(f"Error deleting education level with ID {education_level_id}: {str(e)}")
            raise
            
    def _serialize_education_level(self, education_level) -> Dict[str, Any]:
        """
        Convert an education level model to a dictionary.
        
        Args:
            education_level: EducationLevel model instance
            
        Returns:
            Dictionary with education level data
        """
        return {
            "education_level_id": education_level.education_level_id,
            "code": education_level.code,
            "name": education_level.name,
            "description": education_level.description,
            "display_order": education_level.display_order,
            "created_at": education_level.created_at,
            "updated_at": education_level.updated_at
        } 