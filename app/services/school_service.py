"""
School service module.

This module provides business logic for schools, bridging
the API layer with the repository layer.
"""

import logging
from typing import List, Optional, Dict, Any, Tuple

from app.repositories.school_repository import SchoolRepository
from app.domain.models.school import School

logger = logging.getLogger(__name__)

class SchoolService:
    """Service for handling school business logic."""
    
    def __init__(self, repository: SchoolRepository):
        """
        Initialize the service with a repository.
        
        Args:
            repository: Repository for school data access
        """
        self.repository = repository
    
    async def get_all_schools(
        self, 
        skip: int = 0, 
        limit: int = 100
    ) -> Tuple[List[School], int]:
        """
        Get all schools with pagination.
        
        Args:
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return
            
        Returns:
            Tuple containing the list of schools and total count
        """
        return await self.repository.get_all(skip=skip, limit=limit, filters={})
    
    async def get_school_by_id(self, school_id: str) -> Optional[School]:
        """
        Get a school by its ID.
        
        Args:
            school_id: The unique identifier of the school
            
        Returns:
            The school if found, None otherwise
        """
        return await self.repository.get_by_id(school_id)
    
    async def create_school(self, school_data: Dict[str, Any]) -> School:
        """
        Create a new school.
        
        Args:
            school_data: Dictionary containing the school data
            
        Returns:
            The created school
        """
        # Validate input data if needed
        
        # Create the school
        return await self.repository.create(school_data)
    
    async def update_school(self, school_id: str, school_data: Dict[str, Any]) -> Optional[School]:
        """
        Update a school.
        
        Args:
            school_id: The unique identifier of the school
            school_data: Dictionary containing the updated data
            
        Returns:
            The updated school if found, None otherwise
        """
        # Validate input data if needed
        
        # Remove any empty fields
        cleaned_data = {k: v for k, v in school_data.items() if v is not None}
        
        # Don't update if no fields to update
        if not cleaned_data:
            return await self.get_school_by_id(school_id)
        
        return await self.repository.update(school_id, cleaned_data)
    
    async def delete_school(self, school_id: str) -> bool:
        """
        Delete a school.
        
        Args:
            school_id: The unique identifier of the school
            
        Returns:
            True if the school was deleted, False otherwise
        """
        return await self.repository.delete(school_id) 