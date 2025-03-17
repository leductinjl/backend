"""
Exam Room service module.

This module provides business logic for exam rooms, bridging
the API layer with the repository layer.
"""

import logging
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy import select

from app.repositories.exam_room_repository import ExamRoomRepository
from app.repositories.exam_location_repository import ExamLocationRepository
from app.domain.models.exam_room import ExamRoom

logger = logging.getLogger(__name__)

class ExamRoomService:
    """Service for handling exam room business logic."""
    
    def __init__(
        self, 
        repository: ExamRoomRepository,
        exam_location_repository: Optional[ExamLocationRepository] = None
    ):
        """
        Initialize the service with repositories.
        
        Args:
            repository: Repository for exam room data access
            exam_location_repository: Repository for exam location data access
        """
        self.repository = repository
        self.exam_location_repository = exam_location_repository
    
    async def get_all_exam_rooms(
        self, 
        skip: int = 0, 
        limit: int = 100,
        location_id: Optional[str] = None,
        exam_id: Optional[str] = None,
        is_active: Optional[bool] = None,
        capacity_min: Optional[int] = None,
        capacity_max: Optional[int] = None
    ) -> Tuple[List[Dict], int]:
        """
        Get all exam rooms with pagination and optional filtering.
        
        Args:
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return
            location_id: Optional filter by location ID
            exam_id: Optional filter by exam ID
            is_active: Optional filter by active status
            capacity_min: Optional minimum capacity filter
            capacity_max: Optional maximum capacity filter
            
        Returns:
            Tuple containing the list of exam rooms and total count
        """
        filters = {}
        if location_id:
            filters["location_id"] = location_id
        if exam_id:
            filters["exam_id"] = exam_id
        if is_active is not None:
            filters["is_active"] = is_active
            
        # Capacity filters will be handled separately in the repository
        # if needed, as they might require comparison operations
        
        return await self.repository.get_all(skip=skip, limit=limit, filters=filters)
    
    async def get_exam_room_by_id(self, room_id: str) -> Optional[Dict]:
        """
        Get an exam room by its ID.
        
        Args:
            room_id: The unique identifier of the exam room
            
        Returns:
            The exam room if found, None otherwise
        """
        return await self.repository.get_by_id(room_id)
    
    async def get_rooms_by_location_id(self, location_id: str) -> List[ExamRoom]:
        """
        Get all exam rooms for a specific location.
        
        Args:
            location_id: The ID of the exam location
            
        Returns:
            List of exam rooms for the specified location
        """
        return await self.repository.get_by_location_id(location_id)
    
    async def get_rooms_by_exam_id(self, exam_id: str) -> List[Dict]:
        """
        Get all exam rooms for a specific exam.
        
        Args:
            exam_id: The ID of the exam
            
        Returns:
            List of exam rooms for the specified exam
        """
        return await self.repository.get_by_exam_id(exam_id)
    
    async def create_exam_room(self, exam_room_data: Dict[str, Any]) -> Optional[ExamRoom]:
        """
        Create a new exam room after validating the location ID.
        
        Args:
            exam_room_data: Dictionary containing the exam room data
            
        Returns:
            The created exam room if successful, None otherwise
        """
        # Validate that location exists if repository is provided
        if self.exam_location_repository:
            location = await self.exam_location_repository.get_by_id(exam_room_data["location_id"])
            
            if not location:
                logger.error(f"Exam location with ID {exam_room_data['location_id']} not found")
                return None
        
        # Create the exam room
        return await self.repository.create(exam_room_data)
    
    async def update_exam_room(self, room_id: str, exam_room_data: Dict[str, Any]) -> Optional[ExamRoom]:
        """
        Update an exam room after validating the location ID if provided.
        
        Args:
            room_id: The unique identifier of the exam room
            exam_room_data: Dictionary containing the updated data
            
        Returns:
            The updated exam room if found and valid, None otherwise
        """
        # Validate location ID if provided and repository is available
        if "location_id" in exam_room_data and self.exam_location_repository:
            location = await self.exam_location_repository.get_by_id(exam_room_data["location_id"])
            
            if not location:
                logger.error(f"Exam location with ID {exam_room_data['location_id']} not found")
                return None
        
        # Remove any empty fields
        cleaned_data = {k: v for k, v in exam_room_data.items() if v is not None}
        
        # Don't update if no fields to update
        if not cleaned_data:
            # Just return the existing record
            existing_room_dict = await self.repository.get_by_id(room_id)
            if not existing_room_dict:
                return None
                
            # Convert to ExamRoom model for consistent return type
            query = select(ExamRoom).filter(ExamRoom.room_id == room_id)
            result = await self.repository.db.execute(query)
            return result.scalar_one_or_none()
        
        return await self.repository.update(room_id, cleaned_data)
    
    async def delete_exam_room(self, room_id: str) -> bool:
        """
        Delete an exam room.
        
        Args:
            room_id: The unique identifier of the exam room
            
        Returns:
            True if the exam room was deleted, False otherwise
        """
        return await self.repository.delete(room_id) 