"""
Exam Schedule service module.

This module provides business logic for managing exam schedules,
including validations and complex operations that may involve multiple repositories.
"""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.repositories.exam_schedule_repository import ExamScheduleRepository
from app.repositories.exam_subject_repository import ExamSubjectRepository
from app.domain.models.exam_schedule import ExamSchedule, ScheduleStatus
from app.api.dto.exam_schedule import (
    ExamScheduleCreate,
    ExamScheduleUpdate,
    ExamScheduleResponse
)

class ExamScheduleService:
    """Service for managing exam schedules."""
    
    def __init__(self, db: AsyncSession):
        """
        Initialize with a database session.
        
        Args:
            db: SQLAlchemy async session
        """
        self.db = db
        self.logger = logging.getLogger(__name__)
        self.exam_schedule_repository = ExamScheduleRepository(db)
        self.exam_subject_repository = ExamSubjectRepository(db)
    
    async def get_exam_schedules(
        self,
        skip: int = 0,
        limit: int = 100,
        exam_id: Optional[str] = None,
        subject_id: Optional[str] = None,
        exam_subject_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        status: Optional[str] = None
    ) -> Tuple[List[ExamSchedule], int]:
        """
        Get exam schedules with pagination and filtering.
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            exam_id: Filter by exam ID
            subject_id: Filter by subject ID
            exam_subject_id: Filter by exam subject ID
            start_date: Filter by minimum start date
            end_date: Filter by maximum end date
            status: Filter by status
            
        Returns:
            Tuple of (list of exam schedules, total count)
        """
        try:
            # Validate status if provided
            if status and status not in [s.value for s in ScheduleStatus]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid status. Valid values are: {', '.join([s.value for s in ScheduleStatus])}"
                )
            
            # Get exam schedules with filters
            schedules, total = await self.exam_schedule_repository.get_all(
                skip=skip,
                limit=limit,
                exam_id=exam_id,
                subject_id=subject_id,
                exam_subject_id=exam_subject_id,
                start_date=start_date,
                end_date=end_date,
                status=status
            )
            
            return schedules, total
            
        except HTTPException:
            raise
        except Exception as e:
            self.logger.error(f"Error getting exam schedules: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An error occurred while retrieving exam schedules"
            )
    
    async def get_exam_schedule_by_id(self, exam_schedule_id: str) -> ExamSchedule:
        """
        Get an exam schedule by ID.
        
        Args:
            exam_schedule_id: ID of the exam schedule to retrieve
            
        Returns:
            ExamSchedule object
            
        Raises:
            HTTPException: If the exam schedule is not found
        """
        try:
            # Get the exam schedule
            exam_schedule = await self.exam_schedule_repository.get_by_id(exam_schedule_id)
            
            # Raise exception if not found
            if not exam_schedule:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Exam schedule with ID {exam_schedule_id} not found"
                )
            
            return exam_schedule
            
        except HTTPException:
            raise
        except Exception as e:
            self.logger.error(f"Error getting exam schedule with ID {exam_schedule_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An error occurred while retrieving the exam schedule"
            )
    
    async def get_schedules_by_exam_subject(
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
            
        Raises:
            HTTPException: If the exam subject is not found
        """
        try:
            # Verify the exam subject exists
            exam_subject = await self.exam_subject_repository.get_by_id(exam_subject_id)
            if not exam_subject:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Exam subject with ID {exam_subject_id} not found"
                )
            
            # Get schedules for the exam subject
            schedules, total = await self.exam_schedule_repository.get_by_exam_subject(
                exam_subject_id=exam_subject_id,
                skip=skip,
                limit=limit
            )
            
            return schedules, total
            
        except HTTPException:
            raise
        except Exception as e:
            self.logger.error(f"Error getting schedules for exam subject {exam_subject_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An error occurred while retrieving exam schedules for the exam subject"
            )
    
    async def get_schedules_by_exam(
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
            # Get schedules for the exam
            schedules, total = await self.exam_schedule_repository.get_by_exam(
                exam_id=exam_id,
                skip=skip,
                limit=limit
            )
            
            return schedules, total
            
        except Exception as e:
            self.logger.error(f"Error getting schedules for exam {exam_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An error occurred while retrieving exam schedules for the exam"
            )
    
    async def create_exam_schedule(self, schedule_data: ExamScheduleCreate) -> ExamSchedule:
        """
        Create a new exam schedule.
        
        Args:
            schedule_data: Data for creating the exam schedule
            
        Returns:
            Created ExamSchedule object
            
        Raises:
            HTTPException: If validation fails or an error occurs during creation
        """
        try:
            # Verify the exam subject exists
            exam_subject = await self.exam_subject_repository.get_by_id(schedule_data.exam_subject_id)
            if not exam_subject:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Exam subject with ID {schedule_data.exam_subject_id} not found"
                )
            
            # Validate start and end times
            if schedule_data.end_time <= schedule_data.start_time:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="End time must be after start time"
                )
            
            # Check for overlapping schedules for the same exam subject
            existing_schedules, _ = await self.exam_schedule_repository.get_by_exam_subject(
                exam_subject_id=schedule_data.exam_subject_id
            )
            
            for existing in existing_schedules:
                # Check if the new schedule overlaps with an existing one
                if (
                    (schedule_data.start_time < existing.end_time and
                     schedule_data.end_time > existing.start_time)
                ):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Schedule overlaps with an existing schedule (ID: {existing.exam_schedule_id})"
                    )
            
            # Prepare data for creation
            schedule_dict = schedule_data.dict()
            
            # Create the exam schedule
            created_schedule = await self.exam_schedule_repository.create(schedule_dict)
            
            return created_schedule
            
        except HTTPException:
            raise
        except Exception as e:
            self.logger.error(f"Error creating exam schedule: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An error occurred while creating the exam schedule"
            )
    
    async def update_exam_schedule(
        self,
        exam_schedule_id: str,
        schedule_data: ExamScheduleUpdate
    ) -> ExamSchedule:
        """
        Update an exam schedule.
        
        Args:
            exam_schedule_id: ID of the exam schedule to update
            schedule_data: Data for updating the exam schedule
            
        Returns:
            Updated ExamSchedule object
            
        Raises:
            HTTPException: If validation fails or an error occurs during update
        """
        try:
            # Get the existing schedule
            existing_schedule = await self.get_exam_schedule_by_id(exam_schedule_id)
            
            # Prepare update data
            update_dict = {k: v for k, v in schedule_data.dict(exclude_unset=True).items() if v is not None}
            
            # Validate start and end times if being updated
            start_time = update_dict.get('start_time', existing_schedule.start_time)
            end_time = update_dict.get('end_time', existing_schedule.end_time)
            
            if end_time <= start_time:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="End time must be after start time"
                )
            
            # Check for overlapping schedules if times are being updated
            if 'start_time' in update_dict or 'end_time' in update_dict:
                other_schedules, _ = await self.exam_schedule_repository.get_by_exam_subject(
                    exam_subject_id=existing_schedule.exam_subject_id
                )
                
                for other in other_schedules:
                    # Skip the current schedule
                    if other.exam_schedule_id == exam_schedule_id:
                        continue
                    
                    # Check if the updated schedule overlaps with another existing one
                    if (
                        (start_time < other.end_time and
                         end_time > other.start_time)
                    ):
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Updated schedule would overlap with an existing schedule (ID: {other.exam_schedule_id})"
                        )
            
            # Update the exam schedule
            updated_schedule = await self.exam_schedule_repository.update(
                exam_schedule_id=exam_schedule_id,
                exam_schedule_data=update_dict
            )
            
            if not updated_schedule:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Exam schedule with ID {exam_schedule_id} not found"
                )
            
            return updated_schedule
            
        except HTTPException:
            raise
        except Exception as e:
            self.logger.error(f"Error updating exam schedule {exam_schedule_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An error occurred while updating the exam schedule"
            )
    
    async def delete_exam_schedule(self, exam_schedule_id: str) -> bool:
        """
        Delete an exam schedule.
        
        Args:
            exam_schedule_id: ID of the exam schedule to delete
            
        Returns:
            Boolean indicating success
            
        Raises:
            HTTPException: If the exam schedule is not found or an error occurs during deletion
        """
        try:
            # Verify the exam schedule exists
            exam_schedule = await self.get_exam_schedule_by_id(exam_schedule_id)
            
            # Delete the exam schedule
            deleted = await self.exam_schedule_repository.delete(exam_schedule_id)
            
            if not deleted:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Exam schedule with ID {exam_schedule_id} not found"
                )
            
            return True
            
        except HTTPException:
            raise
        except Exception as e:
            self.logger.error(f"Error deleting exam schedule {exam_schedule_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An error occurred while deleting the exam schedule"
            ) 