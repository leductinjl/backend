"""
Exam Location service module.

This module provides business logic for exam locations, bridging
the API layer with the repository layer.
"""

import logging
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy import select

from app.repositories.exam_location_repository import ExamLocationRepository
from app.repositories.exam_repository import ExamRepository
from app.domain.models.exam_location import ExamLocation

logger = logging.getLogger(__name__)

class ExamLocationService:
    """Service for handling exam location business logic."""
    
    def __init__(
        self, 
        repository: ExamLocationRepository,
        exam_repository: Optional[ExamRepository] = None
    ):
        """
        Initialize the service with repositories.
        
        Args:
            repository: Repository for exam location data access
            exam_repository: Repository for exam data access
        """
        self.repository = repository
        self.exam_repository = exam_repository
    
    async def get_all_exam_locations(
        self, 
        skip: int = 0, 
        limit: int = 100,
        exam_id: Optional[str] = None,
        is_active: Optional[bool] = None,
        city: Optional[str] = None,
        country: Optional[str] = None
    ) -> Tuple[List[Dict], int]:
        """
        Get all exam locations with pagination and optional filtering.
        
        Args:
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return
            exam_id: Optional filter by exam ID
            is_active: Optional filter by active status
            city: Optional filter by city
            country: Optional filter by country
            
        Returns:
            Tuple containing the list of exam locations and total count
        """
        filters = {}
        if exam_id:
            filters["exam_id"] = exam_id
        if is_active is not None:
            filters["is_active"] = is_active
        if city:
            filters["city"] = city
        if country:
            filters["country"] = country
        
        return await self.repository.get_all(skip=skip, limit=limit, filters=filters)
    
    async def get_exam_location_by_id(self, location_id: str) -> Optional[Dict]:
        """
        Get an exam location by its ID.
        
        Args:
            location_id: The unique identifier of the exam location
            
        Returns:
            The exam location if found, None otherwise
        """
        return await self.repository.get_by_id(location_id)
    
    async def get_locations_by_exam_id(self, exam_id: str) -> List[ExamLocation]:
        """
        Get all exam locations for a specific exam.
        
        Args:
            exam_id: The ID of the exam
            
        Returns:
            List of exam locations for the specified exam
        """
        return await self.repository.get_by_exam_id(exam_id)
    
    async def create_exam_location(self, exam_location_data: Dict[str, Any]) -> Optional[ExamLocation]:
        """
        Create a new exam location after validating the exam ID if provided.
        
        Args:
            exam_location_data: Dictionary containing the exam location data
            
        Returns:
            The created exam location if successful, None otherwise
        """
        # Validate that exam exists if exam_id is provided and repository is available
        exam_id = exam_location_data.get("exam_id")
        if exam_id and self.exam_repository:
            exam = await self.exam_repository.get_by_id(exam_id)
            
            if not exam:
                logger.error(f"Exam with ID {exam_id} not found")
                return None
        
        # Create the exam location
        return await self.repository.create(exam_location_data)
    
    async def update_exam_location(self, location_id: str, exam_location_data: Dict[str, Any]) -> Optional[ExamLocation]:
        """
        Update an exam location after validating the exam ID if provided.
        
        Args:
            location_id: The unique identifier of the exam location
            exam_location_data: Dictionary containing the updated data
            
        Returns:
            The updated exam location if found and valid, None otherwise
        """
        # Validate exam ID if provided and repository is available
        exam_id = exam_location_data.get("exam_id")
        if exam_id and self.exam_repository:
            exam = await self.exam_repository.get_by_id(exam_id)
            
            if not exam:
                logger.error(f"Exam with ID {exam_id} not found")
                return None
        
        # Remove any empty fields
        cleaned_data = {k: v for k, v in exam_location_data.items() if v is not None}
        
        # Don't update if no fields to update
        if not cleaned_data:
            # Just return the existing record
            existing_location = await self.repository.get_by_id(location_id)
            if not existing_location:
                return None
                
            # Convert to ExamLocation model for consistent return type
            query = select(ExamLocation).filter(ExamLocation.location_id == location_id)
            result = await self.repository.db.execute(query)
            return result.scalar_one_or_none()
        
        return await self.repository.update(location_id, cleaned_data)
    
    async def delete_exam_location(self, location_id: str) -> bool:
        """
        Delete an exam location.
        
        Args:
            location_id: The unique identifier of the exam location
            
        Returns:
            True if the exam location was deleted, False otherwise
        """
        return await self.repository.delete(location_id) 