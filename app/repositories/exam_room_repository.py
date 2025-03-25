"""
Exam Room repository module.

This module provides database operations for exam rooms,
including CRUD operations and queries.
"""

import logging
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func, join
from sqlalchemy.sql import expression

from app.domain.models.exam_room import ExamRoom
from app.domain.models.exam_location import ExamLocation
from app.domain.models.exam_location_mapping import ExamLocationMapping
from app.domain.models.exam import Exam
from app.services.id_service import generate_model_id

logger = logging.getLogger(__name__)

class ExamRoomRepository:
    """Repository for managing ExamRoom entities in the database."""
    
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
        Get all exam rooms with pagination and optional filtering.
        
        Args:
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return
            filters: Optional dictionary of filter criteria
            
        Returns:
            Tuple containing the list of exam rooms with details and total count
        """
        # Base query for exam rooms and locations
        base_query = (
            select(
                ExamRoom,
                ExamLocation.location_name
            )
            .join(ExamLocation, ExamRoom.location_id == ExamLocation.location_id)
        )
        
        # Apply filters if any
        if filters:
            for field, value in filters.items():
                # Handle special case for filtering by exam_id
                if field == "exam_id":
                    # We need to join with exam_location_mapping and exam tables
                    base_query = (
                        base_query
                        .join(ExamLocationMapping, ExamLocation.location_id == ExamLocationMapping.location_id)
                        .join(Exam, ExamLocationMapping.exam_id == Exam.exam_id)
                        .filter(Exam.exam_id == value)
                    )
                # Handle filtering by ExamRoom fields
                elif hasattr(ExamRoom, field) and value is not None:
                    base_query = base_query.filter(getattr(ExamRoom, field) == value)
        
        # Get total count
        count_query = select(func.count()).select_from(base_query.subquery())
        total = await self.db.scalar(count_query)
        
        # Apply pagination
        query = base_query.offset(skip).limit(limit)
        
        # Execute query
        result = await self.db.execute(query)
        
        # Process results to include related details
        exam_rooms = []
        for room, location_name in result:
            # Get related exams for this room's location
            exams_query = (
                select(
                    Exam.exam_id,
                    Exam.exam_name
                )
                .join(ExamLocationMapping, Exam.exam_id == ExamLocationMapping.exam_id)
                .filter(ExamLocationMapping.location_id == room.location_id)
            )
            exams_result = await self.db.execute(exams_query)
            exams = [{"exam_id": exam_id, "exam_name": exam_name} for exam_id, exam_name in exams_result]
            
            # Get schedules for this room
            schedules = await self.get_schedules_by_room_id(room.room_id)
            
            room_dict = {
                "room_id": room.room_id,
                "room_name": room.room_name,
                "capacity": room.capacity,
                "floor": room.floor,
                "room_number": room.room_number,
                "description": room.description,
                "is_active": room.is_active,
                "equipment": room.equipment,
                "special_requirements": room.special_requirements,
                "location_id": room.location_id,
                "room_metadata": room.room_metadata,
                "created_at": room.created_at,
                "updated_at": room.updated_at,
                "location_name": location_name,
                "exams": exams,  # List of exams instead of single exam_id/name
                "schedules": schedules  # Add schedules to the returned data
            }
            exam_rooms.append(room_dict)
        
        return exam_rooms, total or 0
    
    async def get_by_id(self, room_id: str) -> Optional[Dict]:
        """
        Get an exam room by its ID, including related details.
        
        Args:
            room_id: The unique identifier of the exam room
            
        Returns:
            The exam room with related details if found, None otherwise
        """
        # Base query for exam room and location
        query = (
            select(
                ExamRoom,
                ExamLocation.location_name
            )
            .join(ExamLocation, ExamRoom.location_id == ExamLocation.location_id)
            .filter(ExamRoom.room_id == room_id)
        )
        
        result = await self.db.execute(query)
        row = result.first()
        
        if not row:
            return None
        
        room, location_name = row
        
        # Get related exams for this room's location
        exams_query = (
            select(
                Exam.exam_id,
                Exam.exam_name
            )
            .join(ExamLocationMapping, Exam.exam_id == ExamLocationMapping.exam_id)
            .filter(ExamLocationMapping.location_id == room.location_id)
        )
        exams_result = await self.db.execute(exams_query)
        exams = [{"exam_id": exam_id, "exam_name": exam_name} for exam_id, exam_name in exams_result]
        
        # Get schedules for this room
        schedules = await self.get_schedules_by_room_id(room_id)
        
        return {
            "room_id": room.room_id,
            "room_name": room.room_name,
            "capacity": room.capacity,
            "floor": room.floor,
            "room_number": room.room_number,
            "description": room.description,
            "is_active": room.is_active,
            "equipment": room.equipment,
            "special_requirements": room.special_requirements,
            "location_id": room.location_id,
            "room_metadata": room.room_metadata,
            "created_at": room.created_at,
            "updated_at": room.updated_at,
            "location_name": location_name,
            "exams": exams,  # List of exams instead of single exam_id/name
            "schedules": schedules  # Add schedules to the returned data
        }
    
    async def get_schedules_by_room_id(self, room_id: str) -> List[Dict]:
        """
        Get all exam schedules for a specific room.
        
        Args:
            room_id: The ID of the exam room
            
        Returns:
            List of exam schedules for the specified room
        """
        try:
            # Import here to avoid circular imports
            from app.domain.models.exam_schedule import ExamSchedule
            
            # Query for schedules that are assigned to this room
            query = select(ExamSchedule).filter(ExamSchedule.room_id == room_id)
            result = await self.db.execute(query)
            schedules = result.scalars().all()
            
            # Convert to dictionary
            schedule_list = []
            for schedule in schedules:
                # Log attributes to debug
                logger.debug(f"Schedule attributes: {dir(schedule)}")
                
                # Use the correct attribute name (exam_schedule_id instead of schedule_id)
                schedule_list.append({
                    "schedule_id": getattr(schedule, "exam_schedule_id", None),  # Use exam_schedule_id instead
                    "exam_id": getattr(schedule, "exam_subject_id", None),  # Adjusted based on the SQL query
                    "room_id": schedule.room_id,
                    "start_time": schedule.start_time,
                    "end_time": schedule.end_time,
                    "status": getattr(schedule, "status", None),
                    "is_active": getattr(schedule, "is_active", True),
                    "description": getattr(schedule, "description", None)
                })
                
            return schedule_list
        except Exception as e:
            logger.error(f"Error getting schedules for room {room_id}: {e}")
            return []
    
    async def get_by_location_id(self, location_id: str) -> List[ExamRoom]:
        """
        Get all exam rooms for a specific location.
        
        Args:
            location_id: The ID of the exam location
            
        Returns:
            List of exam rooms for the specified location
        """
        query = select(ExamRoom).filter(ExamRoom.location_id == location_id)
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def get_by_exam_id(self, exam_id: str) -> List[Dict]:
        """
        Get all exam rooms for a specific exam.
        
        Args:
            exam_id: The ID of the exam
            
        Returns:
            List of exam rooms (with location information) for the specified exam
        """
        # Query rooms through the proper relationship path
        query = (
            select(
                ExamRoom,
                ExamLocation.location_name
            )
            .join(ExamLocation, ExamRoom.location_id == ExamLocation.location_id)
            .join(ExamLocationMapping, ExamLocation.location_id == ExamLocationMapping.location_id)
            .join(Exam, ExamLocationMapping.exam_id == Exam.exam_id)
            .filter(Exam.exam_id == exam_id)
        )
        result = await self.db.execute(query)
        
        rooms = []
        for room, location_name in result:
            room_dict = {
                "room_id": room.room_id,
                "room_name": room.room_name,
                "capacity": room.capacity,
                "floor": room.floor,
                "room_number": room.room_number,
                "description": room.description,
                "is_active": room.is_active,
                "equipment": room.equipment,
                "special_requirements": room.special_requirements,
                "location_id": room.location_id,
                "location_name": location_name,
                "room_metadata": room.room_metadata,
                "created_at": room.created_at,
                "updated_at": room.updated_at,
                "exam_id": exam_id  # Include the requested exam_id for reference
            }
            rooms.append(room_dict)
        
        return rooms
    
    async def create(self, exam_room_data: Dict[str, Any]) -> ExamRoom:
        """
        Create a new exam room.
        
        Args:
            exam_room_data: Dictionary containing the exam room data
            
        Returns:
            The created exam room
        """
        # Ensure room_id is set
        if 'room_id' not in exam_room_data or not exam_room_data['room_id']:
            exam_room_data['room_id'] = generate_model_id("ExamRoom")
            logger.info(f"Generated new room_id: {exam_room_data['room_id']}")
            
        # Create a new exam room
        new_exam_room = ExamRoom(**exam_room_data)
        
        # Add to session and commit
        self.db.add(new_exam_room)
        await self.db.commit()
        await self.db.refresh(new_exam_room)
        
        logger.info(f"Created exam room with ID: {new_exam_room.room_id}")
        return new_exam_room
    
    async def update(self, room_id: str, exam_room_data: Dict[str, Any]) -> Optional[ExamRoom]:
        """
        Update an exam room.
        
        Args:
            room_id: The unique identifier of the exam room
            exam_room_data: Dictionary containing the updated data
            
        Returns:
            The updated exam room if found, None otherwise
        """
        # Get the raw ExamRoom object first
        query = select(ExamRoom).filter(ExamRoom.room_id == room_id)
        result = await self.db.execute(query)
        existing_room = result.scalar_one_or_none()
        
        if not existing_room:
            return None
        
        # Update the exam room
        update_stmt = (
            update(ExamRoom)
            .where(ExamRoom.room_id == room_id)
            .values(**exam_room_data)
            .returning(ExamRoom)
        )
        result = await self.db.execute(update_stmt)
        await self.db.commit()
        
        updated_room = result.scalar_one_or_none()
        if updated_room:
            logger.info(f"Updated exam room with ID: {room_id}")
        
        return updated_room
    
    async def delete(self, room_id: str) -> bool:
        """
        Delete an exam room.
        
        Args:
            room_id: The unique identifier of the exam room
            
        Returns:
            True if the exam room was deleted, False otherwise
        """
        # Check if the exam room exists
        query = select(ExamRoom).filter(ExamRoom.room_id == room_id)
        result = await self.db.execute(query)
        existing_room = result.scalar_one_or_none()
        
        if not existing_room:
            return False
        
        # Delete the exam room
        delete_stmt = delete(ExamRoom).where(ExamRoom.room_id == room_id)
        await self.db.execute(delete_stmt)
        await self.db.commit()
        
        logger.info(f"Deleted exam room with ID: {room_id}")
        return True 