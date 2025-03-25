"""
Exam Schedule repository module.

This module provides database access methods for the ExamSchedule model,
including CRUD operations and queries for retrieving exam schedules with various filters.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func, and_, or_, between
from sqlalchemy.orm import joinedload
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
import logging

from app.domain.models.exam_schedule import ExamSchedule
from app.domain.models.exam_subject import ExamSubject
from app.domain.models.exam import Exam
from app.domain.models.subject import Subject
from app.domain.models.exam_room import ExamRoom
from app.domain.models.exam_location import ExamLocation

class ExamScheduleRepository:
    """Repository for interacting with the ExamSchedule table."""
    
    def __init__(self, db: AsyncSession):
        """
        Initialize with a database session.
        
        Args:
            db: SQLAlchemy async session
        """
        self.db = db
        self.logger = logging.getLogger(__name__)
    
    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        exam_id: Optional[str] = None,
        subject_id: Optional[str] = None,
        exam_subject_id: Optional[str] = None,
        room_id: Optional[str] = None,
        location_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        status: Optional[str] = None
    ) -> Tuple[List[ExamSchedule], int]:
        """
        Retrieve exam schedules with pagination and filtering.
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            exam_id: Filter by exam ID
            subject_id: Filter by subject ID
            exam_subject_id: Filter by exam subject ID
            room_id: Filter by exam room ID
            location_id: Filter by exam location ID
            start_date: Filter by minimum start date
            end_date: Filter by maximum end date
            status: Filter by status
            
        Returns:
            Tuple of (list of exam schedules, total count)
        """
        try:
            # Build query with joins for related data
            query = (
                select(ExamSchedule)
                .options(
                    joinedload(ExamSchedule.exam_subject)
                    .joinedload(ExamSubject.exam),
                    joinedload(ExamSchedule.exam_subject)
                    .joinedload(ExamSubject.subject),
                    joinedload(ExamSchedule.exam_room)
                    .joinedload(ExamRoom.location)
                )
            )
            
            # Apply filters
            conditions = []
            
            if exam_subject_id:
                conditions.append(ExamSchedule.exam_subject_id == exam_subject_id)
            
            if room_id:
                conditions.append(ExamSchedule.room_id == room_id)
                
            if exam_id:
                conditions.append(ExamSubject.exam_id == exam_id)
                
            if subject_id:
                conditions.append(ExamSubject.subject_id == subject_id)
            
            if start_date:
                conditions.append(ExamSchedule.start_time >= start_date)
                
            if end_date:
                conditions.append(ExamSchedule.end_time <= end_date)
                
            if status:
                conditions.append(ExamSchedule.status == status)
                
            if location_id:
                conditions.append(ExamRoom.location_id == location_id)
            
            # Apply joins if needed for filtering
            if exam_id or subject_id:
                query = query.join(ExamSubject, ExamSchedule.exam_subject_id == ExamSubject.exam_subject_id)
                
            if location_id:
                query = query.join(ExamRoom, ExamSchedule.room_id == ExamRoom.room_id)
            
            # Apply conditions if any
            if conditions:
                query = query.where(and_(*conditions))
            
            # Order by start time
            query = query.order_by(ExamSchedule.start_time)
            
            # Get total count
            count_query = select(func.count()).select_from(query.subquery())
            total = await self.db.scalar(count_query)
            
            # Apply pagination
            query = query.offset(skip).limit(limit)
            
            # Execute query
            result = await self.db.execute(query)
            schedules = result.scalars().unique().all()
            
            return schedules, total
            
        except Exception as e:
            self.logger.error(f"Error getting exam schedules: {str(e)}")
            raise
    
    async def get_by_id(self, exam_schedule_id: str) -> Optional[ExamSchedule]:
        """
        Get an exam schedule by ID.
        
        Args:
            exam_schedule_id: ID of the exam schedule to retrieve
            
        Returns:
            ExamSchedule object or None if not found
        """
        try:
            query = (
                select(ExamSchedule)
                .options(
                    joinedload(ExamSchedule.exam_subject)
                    .joinedload(ExamSubject.exam),
                    joinedload(ExamSchedule.exam_subject)
                    .joinedload(ExamSubject.subject),
                    joinedload(ExamSchedule.exam_room)
                    .joinedload(ExamRoom.location)
                )
                .where(ExamSchedule.exam_schedule_id == exam_schedule_id)
            )
            
            result = await self.db.execute(query)
            return result.scalars().first()
            
        except Exception as e:
            self.logger.error(f"Error getting exam schedule with ID {exam_schedule_id}: {str(e)}")
            raise
    
    async def get_by_exam_subject(
        self,
        exam_subject_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[ExamSchedule], int]:
        """
        Get exam schedules for a specific exam subject.
        
        Args:
            exam_subject_id: ID of the exam subject
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            Tuple of (list of exam schedules, total count)
        """
        try:
            # Base query
            query = (
                select(ExamSchedule)
                .options(
                    joinedload(ExamSchedule.exam_subject)
                    .joinedload(ExamSubject.exam),
                    joinedload(ExamSchedule.exam_subject)
                    .joinedload(ExamSubject.subject),
                    joinedload(ExamSchedule.exam_room)
                    .joinedload(ExamRoom.location)
                )
                .where(ExamSchedule.exam_subject_id == exam_subject_id)
                .order_by(ExamSchedule.start_time)
            )
            
            # Get total count
            count_query = select(func.count()).select_from(
                select(ExamSchedule).where(ExamSchedule.exam_subject_id == exam_subject_id).subquery()
            )
            total = await self.db.scalar(count_query)
            
            # Apply pagination
            query = query.offset(skip).limit(limit)
            
            # Execute query
            result = await self.db.execute(query)
            schedules = result.scalars().unique().all()
            
            return schedules, total
            
        except Exception as e:
            self.logger.error(f"Error getting exam schedules for exam subject {exam_subject_id}: {str(e)}")
            raise
    
    async def get_by_exam(
        self,
        exam_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[ExamSchedule], int]:
        """
        Get exam schedules for a specific exam.
        
        Args:
            exam_id: ID of the exam
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            Tuple of (list of exam schedules, total count)
        """
        try:
            # Join query to get schedules for the exam
            query = (
                select(ExamSchedule)
                .join(ExamSubject, ExamSchedule.exam_subject_id == ExamSubject.exam_subject_id)
                .options(
                    joinedload(ExamSchedule.exam_subject)
                    .joinedload(ExamSubject.exam),
                    joinedload(ExamSchedule.exam_subject)
                    .joinedload(ExamSubject.subject),
                    joinedload(ExamSchedule.exam_room)
                    .joinedload(ExamRoom.location)
                )
                .where(ExamSubject.exam_id == exam_id)
                .order_by(ExamSchedule.start_time)
            )
            
            # Get total count
            count_query = select(func.count()).select_from(
                select(ExamSchedule)
                .join(ExamSubject, ExamSchedule.exam_subject_id == ExamSubject.exam_subject_id)
                .where(ExamSubject.exam_id == exam_id)
                .subquery()
            )
            total = await self.db.scalar(count_query)
            
            # Apply pagination
            query = query.offset(skip).limit(limit)
            
            # Execute query
            result = await self.db.execute(query)
            schedules = result.scalars().unique().all()
            
            return schedules, total
            
        except Exception as e:
            self.logger.error(f"Error getting exam schedules for exam {exam_id}: {str(e)}")
            raise
    
    async def get_by_room(
        self,
        room_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[ExamSchedule], int]:
        """
        Get exam schedules for a specific exam room.
        
        Args:
            room_id: ID of the exam room
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            Tuple of (list of exam schedules, total count)
        """
        try:
            # Query for schedules in the specified room
            query = (
                select(ExamSchedule)
                .options(
                    joinedload(ExamSchedule.exam_subject)
                    .joinedload(ExamSubject.exam),
                    joinedload(ExamSchedule.exam_subject)
                    .joinedload(ExamSubject.subject),
                    joinedload(ExamSchedule.exam_room)
                    .joinedload(ExamRoom.location)
                )
                .where(ExamSchedule.room_id == room_id)
                .order_by(ExamSchedule.start_time)
            )
            
            # Get total count
            count_query = select(func.count()).select_from(
                select(ExamSchedule).where(ExamSchedule.room_id == room_id).subquery()
            )
            total = await self.db.scalar(count_query)
            
            # Apply pagination
            query = query.offset(skip).limit(limit)
            
            # Execute query
            result = await self.db.execute(query)
            schedules = result.scalars().unique().all()
            
            return schedules, total
            
        except Exception as e:
            self.logger.error(f"Error getting exam schedules for room {room_id}: {str(e)}")
            raise
    
    async def get_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[ExamSchedule], int]:
        """
        Get exam schedules within a date range.
        
        Args:
            start_date: Start of the date range
            end_date: End of the date range
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            Tuple of (list of exam schedules, total count)
        """
        try:
            # Query for schedules in the date range
            query = (
                select(ExamSchedule)
                .options(
                    joinedload(ExamSchedule.exam_subject)
                    .joinedload(ExamSubject.exam),
                    joinedload(ExamSchedule.exam_subject)
                    .joinedload(ExamSubject.subject),
                    joinedload(ExamSchedule.exam_room)
                    .joinedload(ExamRoom.location)
                )
                .where(
                    or_(
                        # Schedule that starts within the date range
                        and_(
                            ExamSchedule.start_time >= start_date,
                            ExamSchedule.start_time <= end_date
                        ),
                        # Schedule that ends within the date range
                        and_(
                            ExamSchedule.end_time >= start_date,
                            ExamSchedule.end_time <= end_date
                        ),
                        # Schedule that spans the date range
                        and_(
                            ExamSchedule.start_time <= start_date,
                            ExamSchedule.end_time >= end_date
                        )
                    )
                )
                .order_by(ExamSchedule.start_time)
            )
            
            # Get total count
            count_query = select(func.count()).select_from(query.subquery())
            total = await self.db.scalar(count_query)
            
            # Apply pagination
            query = query.offset(skip).limit(limit)
            
            # Execute query
            result = await self.db.execute(query)
            schedules = result.scalars().unique().all()
            
            return schedules, total
            
        except Exception as e:
            self.logger.error(f"Error getting exam schedules for date range {start_date} to {end_date}: {str(e)}")
            raise
    
    async def create(self, exam_schedule_data: Dict[str, Any]) -> ExamSchedule:
        """
        Create a new exam schedule.
        
        Args:
            exam_schedule_data: Dictionary with exam schedule data
            
        Returns:
            Created ExamSchedule object
        """
        try:
            # Generate ID if not provided
            if 'exam_schedule_id' not in exam_schedule_data:
                from app.services.id_service import generate_model_id
                exam_schedule_data['exam_schedule_id'] = generate_model_id("ExamSchedule")
            
            # Validate that room_id is provided
            if 'room_id' not in exam_schedule_data or not exam_schedule_data['room_id']:
                raise ValueError("room_id is required for creating an exam schedule")
            
            # Create new exam schedule
            exam_schedule = ExamSchedule(**exam_schedule_data)
            self.db.add(exam_schedule)
            await self.db.flush()
            
            # Get the created exam schedule with related data
            created_schedule = await self.get_by_id(exam_schedule.exam_schedule_id)
            
            return created_schedule
            
        except Exception as e:
            await self.db.rollback()
            self.logger.error(f"Error creating exam schedule: {str(e)}")
            raise
    
    async def update(self, exam_schedule_id: str, exam_schedule_data: Dict[str, Any]) -> Optional[ExamSchedule]:
        """
        Update an exam schedule.
        
        Args:
            exam_schedule_id: ID of the exam schedule to update
            exam_schedule_data: Dictionary with updated exam schedule data
            
        Returns:
            Updated ExamSchedule object or None if not found
        """
        try:
            # Check if the exam schedule exists
            exam_schedule = await self.get_by_id(exam_schedule_id)
            if not exam_schedule:
                return None
            
            # Update the exam schedule
            stmt = (
                update(ExamSchedule)
                .where(ExamSchedule.exam_schedule_id == exam_schedule_id)
                .values(**exam_schedule_data)
            )
            await self.db.execute(stmt)
            
            # Get the updated exam schedule
            updated_schedule = await self.get_by_id(exam_schedule_id)
            
            return updated_schedule
            
        except Exception as e:
            await self.db.rollback()
            self.logger.error(f"Error updating exam schedule {exam_schedule_id}: {str(e)}")
            raise
    
    async def delete(self, exam_schedule_id: str) -> bool:
        """
        Delete an exam schedule.
        
        Args:
            exam_schedule_id: ID of the exam schedule to delete
            
        Returns:
            True if deleted successfully, False if not found
        """
        try:
            # Check if the exam schedule exists
            query = select(ExamSchedule).filter(ExamSchedule.exam_schedule_id == exam_schedule_id)
            result = await self.db.execute(query)
            exam_schedule = result.scalars().first()
            
            if not exam_schedule:
                return False
            
            # Delete the exam schedule
            delete_stmt = delete(ExamSchedule).where(ExamSchedule.exam_schedule_id == exam_schedule_id)
            await self.db.execute(delete_stmt)
            await self.db.commit()
            
            self.logger.info(f"Deleted exam schedule with ID {exam_schedule_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error deleting exam schedule with ID {exam_schedule_id}: {str(e)}")
            await self.db.rollback()
            raise
            
    async def get_by_candidate_id(self, candidate_id: str) -> List[ExamSchedule]:
        """
        Lấy lịch thi của một thí sinh.
        
        Phương thức này tìm tất cả lịch thi liên quan đến thí sinh thông qua
        candidate_exam và candidate_exam_subject.
        
        Args:
            candidate_id: ID của thí sinh cần lấy lịch thi
            
        Returns:
            Danh sách các lịch thi của thí sinh
        """
        from app.domain.models.candidate_exam import CandidateExam
        from app.domain.models.candidate_exam_subject import CandidateExamSubject
        
        try:
            # Xây dựng truy vấn để lấy lịch thi thông qua candidate -> candidate_exam -> candidate_exam_subject -> exam_subject -> exam_schedule
            query = (
                select(ExamSchedule)
                .join(ExamSubject, ExamSchedule.exam_subject_id == ExamSubject.exam_subject_id)
                .join(CandidateExamSubject, CandidateExamSubject.exam_subject_id == ExamSubject.exam_subject_id)
                .join(CandidateExam, CandidateExamSubject.candidate_exam_id == CandidateExam.candidate_exam_id)
                .filter(CandidateExam.candidate_id == candidate_id)
                .options(
                    joinedload(ExamSchedule.exam_subject)
                    .joinedload(ExamSubject.exam),
                    joinedload(ExamSchedule.exam_subject)
                    .joinedload(ExamSubject.subject),
                    joinedload(ExamSchedule.exam_room)
                    .joinedload(ExamRoom.location)
                )
                .order_by(ExamSchedule.start_time)
            )
            
            result = await self.db.execute(query)
            schedules = result.scalars().unique().all()
            
            self.logger.info(f"Retrieved {len(schedules)} exam schedules for candidate {candidate_id}")
            return schedules
            
        except Exception as e:
            self.logger.error(f"Error getting exam schedules for candidate {candidate_id}: {str(e)}")
            raise 