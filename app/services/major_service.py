"""
Major service module.

This module provides business logic for majors (fields of study), bridging
the API layer with the repository layer.
"""

import logging
from typing import List, Optional, Dict, Any, Tuple

from app.repositories.major_repository import MajorRepository
from app.domain.models.major import Major

logger = logging.getLogger(__name__)

class MajorService:
    """Service for handling major business logic."""
    
    def __init__(self, repository: MajorRepository):
        """
        Initialize the service with a repository.
        
        Args:
            repository: Repository for major data access
        """
        self.repository = repository
    
    async def get_all_majors(
        self, 
        skip: int = 0, 
        limit: int = 100
    ) -> Tuple[List[Major], int]:
        """
        Get all majors with pagination.
        
        Args:
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return
            
        Returns:
            Tuple containing the list of majors and total count
        """
        return await self.repository.get_all(skip=skip, limit=limit, filters={})
    
    async def get_major_by_id(self, major_id: str) -> Optional[Major]:
        """
        Get a major by its ID.
        
        Args:
            major_id: The unique identifier of the major
            
        Returns:
            The major if found, None otherwise
        """
        return await self.repository.get_by_id(major_id)
    
    async def create_major(self, major_data: Dict[str, Any]) -> Major:
        """
        Create a new major.
        
        Args:
            major_data: Dictionary containing the major data
            
        Returns:
            The created major
        """
        # Validate input data if needed
        
        # Create the major
        return await self.repository.create(major_data)
    
    async def update_major(self, major_id: str, major_data: Dict[str, Any]) -> Optional[Major]:
        """
        Update a major.
        
        Args:
            major_id: The unique identifier of the major
            major_data: Dictionary containing the updated data
            
        Returns:
            The updated major if found, None otherwise
        """
        # Validate input data if needed
        
        # Remove any empty fields
        cleaned_data = {k: v for k, v in major_data.items() if v is not None}
        
        # Don't update if no fields to update
        if not cleaned_data:
            return await self.get_major_by_id(major_id)
        
        return await self.repository.update(major_id, cleaned_data)
    
    async def delete_major(self, major_id: str) -> bool:
        """
        Delete a major.
        
        Args:
            major_id: The unique identifier of the major
            
        Returns:
            True if the major was deleted, False otherwise
        """
        return await self.repository.delete(major_id) 