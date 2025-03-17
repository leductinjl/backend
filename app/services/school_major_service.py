"""
School-Major service module.

This module provides business logic for school-major relationships, bridging
the API layer with the repository layer.
"""

import logging
from typing import List, Optional, Dict, Any, Tuple

from app.repositories.school_major_repository import SchoolMajorRepository
from app.repositories.school_repository import SchoolRepository
from app.repositories.major_repository import MajorRepository
from app.domain.models.school_major import SchoolMajor

logger = logging.getLogger(__name__)

class SchoolMajorService:
    """Service for handling school-major relationship business logic."""
    
    def __init__(
        self, 
        repository: SchoolMajorRepository,
        school_repository: SchoolRepository = None,
        major_repository: MajorRepository = None
    ):
        """
        Initialize the service with repositories.
        
        Args:
            repository: Repository for school-major relationship data access
            school_repository: Repository for school data access
            major_repository: Repository for major data access
        """
        self.repository = repository
        self.school_repository = school_repository
        self.major_repository = major_repository
    
    async def get_all_school_majors(
        self, 
        skip: int = 0, 
        limit: int = 100,
        school_id: Optional[str] = None,
        major_id: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> Tuple[List[Dict], int]:
        """
        Get all school-major relationships with pagination and optional filtering.
        
        Args:
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return
            school_id: Optional filter by school ID
            major_id: Optional filter by major ID
            is_active: Optional filter by active status
            
        Returns:
            Tuple containing the list of school-major relationships and total count
        """
        filters = {}
        if school_id:
            filters["school_id"] = school_id
        if major_id:
            filters["major_id"] = major_id
        if is_active is not None:
            filters["is_active"] = is_active
        
        return await self.repository.get_all(skip=skip, limit=limit, filters=filters)
    
    async def get_school_major_by_id(self, school_major_id: str) -> Optional[Dict]:
        """
        Get a school-major relationship by its ID.
        
        Args:
            school_major_id: The unique identifier of the school-major relationship
            
        Returns:
            The school-major relationship if found, None otherwise
        """
        return await self.repository.get_by_id(school_major_id)
    
    async def create_school_major(self, school_major_data: Dict[str, Any]) -> Optional[SchoolMajor]:
        """
        Create a new school-major relationship after validating the school and major IDs.
        
        Args:
            school_major_data: Dictionary containing the school-major relationship data
            
        Returns:
            The created school-major relationship if successful, None otherwise
        """
        # Validate that school and major exist if repositories are provided
        if self.school_repository and self.major_repository:
            school = await self.school_repository.get_by_id(school_major_data["school_id"])
            major = await self.major_repository.get_by_id(school_major_data["major_id"])
            
            if not school:
                logger.error(f"School with ID {school_major_data['school_id']} not found")
                return None
                
            if not major:
                logger.error(f"Major with ID {school_major_data['major_id']} not found")
                return None
        
        # Check if relationship already exists
        existing = await self.repository.get_by_school_and_major(
            school_major_data["school_id"],
            school_major_data["major_id"]
        )
        
        if existing:
            logger.warning(f"School-major relationship already exists for school ID {school_major_data['school_id']} and major ID {school_major_data['major_id']}")
            return None
        
        # Create the school-major relationship
        return await self.repository.create(school_major_data)
    
    async def update_school_major(self, school_major_id: str, school_major_data: Dict[str, Any]) -> Optional[SchoolMajor]:
        """
        Update a school-major relationship.
        
        Args:
            school_major_id: The unique identifier of the school-major relationship
            school_major_data: Dictionary containing the updated data
            
        Returns:
            The updated school-major relationship if found, None otherwise
        """
        # Remove any empty fields
        cleaned_data = {k: v for k, v in school_major_data.items() if v is not None}
        
        # Don't allow updating school_id or major_id
        if "school_id" in cleaned_data:
            del cleaned_data["school_id"]
        if "major_id" in cleaned_data:
            del cleaned_data["major_id"]
        
        # Don't update if no fields to update
        if not cleaned_data:
            return await self.repository.get_by_id(school_major_id)
        
        return await self.repository.update(school_major_id, cleaned_data)
    
    async def delete_school_major(self, school_major_id: str) -> bool:
        """
        Delete a school-major relationship.
        
        Args:
            school_major_id: The unique identifier of the school-major relationship
            
        Returns:
            True if the school-major relationship was deleted, False otherwise
        """
        return await self.repository.delete(school_major_id) 