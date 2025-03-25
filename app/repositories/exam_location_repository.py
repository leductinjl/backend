"""
Exam Location repository module.

This module provides database operations for exam locations,
including CRUD operations and queries.
"""

import logging
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func, join, and_
from sqlalchemy.sql import expression

from app.domain.models.exam_location import ExamLocation
from app.domain.models.exam import Exam
from app.domain.models.exam_location_mapping import ExamLocationMapping

logger = logging.getLogger(__name__)

class ExamLocationRepository:
    """Repository for managing ExamLocation entities in the database."""
    
    def __init__(self, db: AsyncSession):
        """
        Initialize the repository with a database session.
        
        Args:
            db: An async SQLAlchemy session
        """
        self.db = db
    
    async def get_all(
        self, 
        skip: int = 0, 
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None
    ) -> Tuple[List[Dict], int]:
        """
        Get all exam locations with pagination and optional filtering.
        
        Args:
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return
            filters: Optional dictionary of filter criteria
            
        Returns:
            Tuple containing the list of exam locations with details and total count
        """
        # Base query for exam locations
        query = select(ExamLocation)
        
        # Handle exam_id filter specifically since it requires a join
        exam_id = None
        if filters and "exam_id" in filters:
            exam_id = filters.pop("exam_id")
        
        # Apply direct filters to ExamLocation if any
        if filters:
            for field, value in filters.items():
                if hasattr(ExamLocation, field) and value is not None:
                    query = query.filter(getattr(ExamLocation, field) == value)
        
        # If filtering by exam_id, join with ExamLocationMapping
        if exam_id:
            query = (
                query
                .join(ExamLocationMapping, ExamLocationMapping.location_id == ExamLocation.location_id)
                .filter(ExamLocationMapping.exam_id == exam_id)
            )
        
        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total = await self.db.scalar(count_query)
        
        # Apply pagination
        query = query.offset(skip).limit(limit)
        
        # Execute query
        result = await self.db.execute(query)
        locations = result.scalars().all()
        
        # Process results 
        exam_locations = []
        for location in locations:
            # Get exam details for this location if they exist
            exam_query = (
                select(Exam)
                .join(ExamLocationMapping, Exam.exam_id == ExamLocationMapping.exam_id)
                .filter(ExamLocationMapping.location_id == location.location_id)
            )
            exam_result = await self.db.execute(exam_query)
            exams = exam_result.scalars().all()
            
            # Extract exam names
            exam_details = []
            for exam in exams:
                mapping_query = (
                    select(ExamLocationMapping)
                    .filter(
                        and_(
                            ExamLocationMapping.exam_id == exam.exam_id,
                            ExamLocationMapping.location_id == location.location_id
                        )
                    )
                )
                mapping_result = await self.db.execute(mapping_query)
                mapping = mapping_result.scalar_one_or_none()
                
                exam_details.append({
                    "exam_id": exam.exam_id,
                    "exam_name": exam.exam_name,
                    "is_primary": mapping.is_primary if mapping else False,
                    "mapping_id": mapping.mapping_id if mapping else None
                })
            
            location_dict = {
                "location_id": location.location_id,
                "location_name": location.location_name,
                "address": location.address,
                "city": location.city,
                "state_province": location.state_province,
                "country": location.country,
                "postal_code": location.postal_code,
                "capacity": location.capacity,
                "contact_info": location.contact_info,
                "additional_info": location.additional_info,
                "is_active": location.is_active,
                "created_at": location.created_at,
                "updated_at": location.updated_at,
                "exams": exam_details
            }
            exam_locations.append(location_dict)
        
        return exam_locations, total or 0
    
    async def get_by_id(self, location_id: str) -> Optional[Dict]:
        """
        Get an exam location by its ID, including exam details.
        
        Args:
            location_id: The unique identifier of the exam location
            
        Returns:
            The exam location with exam details if found, None otherwise
        """
        query = select(ExamLocation).filter(ExamLocation.location_id == location_id)
        result = await self.db.execute(query)
        location = result.scalar_one_or_none()
        
        if not location:
            return None
        
        # Get exam details for this location
        exam_query = (
            select(Exam)
            .join(ExamLocationMapping, Exam.exam_id == ExamLocationMapping.exam_id)
            .filter(ExamLocationMapping.location_id == location_id)
        )
        exam_result = await self.db.execute(exam_query)
        exams = exam_result.scalars().all()
        
        # Extract exam names and details
        exam_details = []
        for exam in exams:
            mapping_query = (
                select(ExamLocationMapping)
                .filter(
                    and_(
                        ExamLocationMapping.exam_id == exam.exam_id,
                        ExamLocationMapping.location_id == location_id
                    )
                )
            )
            mapping_result = await self.db.execute(mapping_query)
            mapping = mapping_result.scalar_one_or_none()
            
            exam_details.append({
                "exam_id": exam.exam_id,
                "exam_name": exam.exam_name,
                "is_primary": mapping.is_primary if mapping else False,
                "mapping_id": mapping.mapping_id if mapping else None
            })
            
        # Get rooms for this location
        rooms = await self.get_rooms_by_location_id(location_id)
        
        return {
            "location_id": location.location_id,
            "location_name": location.location_name,
            "address": location.address,
            "city": location.city,
            "state_province": location.state_province,
            "country": location.country,
            "postal_code": location.postal_code,
            "capacity": location.capacity,
            "contact_info": location.contact_info,
            "additional_info": location.additional_info,
            "is_active": location.is_active,
            "created_at": location.created_at,
            "updated_at": location.updated_at,
            "exams": exam_details,
            "rooms": rooms
        }
    
    async def get_rooms_by_location_id(self, location_id: str) -> List[Dict]:
        """
        Get all exam rooms for a specific location.
        
        Args:
            location_id: The ID of the exam location
            
        Returns:
            List of exam rooms for the specified location
        """
        try:
            # Import here to avoid circular imports
            from app.domain.models.exam_room import ExamRoom
            
            # Query for rooms that belong to this location
            query = select(ExamRoom).filter(ExamRoom.location_id == location_id)
            result = await self.db.execute(query)
            rooms = result.scalars().all()
            
            # Convert to dictionary
            room_list = []
            for room in rooms:
                room_list.append({
                    "room_id": room.room_id,
                    "room_name": room.room_name,
                    "capacity": room.capacity,
                    "location_id": room.location_id,
                    "is_active": room.is_active
                })
                
            return room_list
        except Exception as e:
            logger.error(f"Error getting rooms for location {location_id}: {e}")
            return []
    
    async def get_by_exam_id(self, exam_id: str) -> List[ExamLocation]:
        """
        Get all exam locations for a specific exam.
        
        Args:
            exam_id: The ID of the exam
            
        Returns:
            List of exam locations for the specified exam
        """
        query = (
            select(ExamLocation)
            .join(ExamLocationMapping, ExamLocationMapping.location_id == ExamLocation.location_id)
            .filter(ExamLocationMapping.exam_id == exam_id)
        )
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def create(self, exam_location_data: Dict[str, Any]) -> ExamLocation:
        """
        Create a new exam location.
        
        Args:
            exam_location_data: Dictionary containing the exam location data
            
        Returns:
            The created exam location
        """
        # Handle exam_id separately since it's not part of the ExamLocation model
        exam_id = None
        if "exam_id" in exam_location_data:
            exam_id = exam_location_data.pop("exam_id")
        
        # Create a new exam location
        new_exam_location = ExamLocation(**exam_location_data)
        
        # Add to session and commit
        self.db.add(new_exam_location)
        await self.db.flush()
        
        # If exam_id was provided, create a mapping
        if exam_id:
            mapping = ExamLocationMapping(
                exam_id=exam_id,
                location_id=new_exam_location.location_id,
                is_primary=True  # Make this the primary location for the exam by default
            )
            self.db.add(mapping)
        
        await self.db.commit()
        await self.db.refresh(new_exam_location)
        
        logger.info(f"Created exam location with ID: {new_exam_location.location_id}")
        return new_exam_location
    
    async def update(self, location_id: str, exam_location_data: Dict[str, Any]) -> Optional[ExamLocation]:
        """
        Update an exam location.
        
        Args:
            location_id: The unique identifier of the exam location
            exam_location_data: Dictionary containing the updated data
            
        Returns:
            The updated exam location if found, None otherwise
        """
        # Handle exam_id separately since it's not part of the ExamLocation model
        exam_id = None
        if "exam_id" in exam_location_data:
            exam_id = exam_location_data.pop("exam_id")
        
        # Get the raw ExamLocation object first
        query = select(ExamLocation).filter(ExamLocation.location_id == location_id)
        result = await self.db.execute(query)
        existing_location = result.scalar_one_or_none()
        
        if not existing_location:
            return None
        
        # Update the exam location
        update_stmt = (
            update(ExamLocation)
            .where(ExamLocation.location_id == location_id)
            .values(**exam_location_data)
            .returning(ExamLocation)
        )
        result = await self.db.execute(update_stmt)
        
        # If exam_id was provided, update or create a mapping
        if exam_id:
            # Check if a mapping already exists
            mapping_query = (
                select(ExamLocationMapping)
                .filter(
                    and_(
                        ExamLocationMapping.exam_id == exam_id,
                        ExamLocationMapping.location_id == location_id
                    )
                )
            )
            mapping_result = await self.db.execute(mapping_query)
            existing_mapping = mapping_result.scalar_one_or_none()
            
            if not existing_mapping:
                # Create a new mapping
                mapping = ExamLocationMapping(
                    exam_id=exam_id,
                    location_id=location_id,
                    is_primary=True  # Make this the primary location for the exam by default
                )
                self.db.add(mapping)
        
        await self.db.commit()
        
        updated_location = result.scalar_one_or_none()
        if updated_location:
            logger.info(f"Updated exam location with ID: {location_id}")
        
        return updated_location
    
    async def delete(self, location_id: str) -> bool:
        """
        Delete an exam location.
        
        Args:
            location_id: The unique identifier of the exam location
            
        Returns:
            True if the exam location was deleted, False otherwise
        """
        # Check if the exam location exists
        query = select(ExamLocation).filter(ExamLocation.location_id == location_id)
        result = await self.db.execute(query)
        existing_location = result.scalar_one_or_none()
        
        if not existing_location:
            return False
        
        # First delete any mappings for this location
        mapping_delete_stmt = delete(ExamLocationMapping).where(ExamLocationMapping.location_id == location_id)
        await self.db.execute(mapping_delete_stmt)
        
        # Then delete the exam location
        delete_stmt = delete(ExamLocation).where(ExamLocation.location_id == location_id)
        await self.db.execute(delete_stmt)
        
        await self.db.commit()
        
        logger.info(f"Deleted exam location with ID: {location_id}")
        return True 