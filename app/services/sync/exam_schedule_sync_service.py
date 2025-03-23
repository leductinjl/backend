"""
Exam Schedule Sync Service Module.

This module provides the ExamScheduleSyncService class for synchronizing ExamSchedule
data between PostgreSQL and Neo4j.
"""

import logging
from typing import Optional, Tuple, List, Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession
from neo4j import AsyncDriver

from app.domain.models.exam_schedule import ExamSchedule
from app.domain.graph_models.exam_schedule_node import ExamScheduleNode
from app.repositories.exam_schedule_repository import ExamScheduleRepository
from app.graph_repositories.exam_schedule_graph_repository import ExamScheduleGraphRepository
from app.services.sync.base_sync_service import BaseSyncService

logger = logging.getLogger(__name__)

class ExamScheduleSyncService(BaseSyncService):
    """
    Service for synchronizing ExamSchedule data between PostgreSQL and Neo4j.
    
    This service implements the BaseSyncService abstract class and provides
    methods for synchronizing individual exam schedules by ID and synchronizing
    all exam schedules in the database.
    """
    
    def __init__(
        self,
        session: AsyncSession,
        driver: AsyncDriver,
        exam_schedule_repository: Optional[ExamScheduleRepository] = None,
        exam_schedule_graph_repository: Optional[ExamScheduleGraphRepository] = None
    ):
        """
        Initialize the ExamScheduleSyncService.
        
        Args:
            session: SQLAlchemy async session
            driver: Neo4j async driver
            exam_schedule_repository: Optional ExamScheduleRepository instance
            exam_schedule_graph_repository: Optional ExamScheduleGraphRepository instance
        """
        self.session = session
        self.driver = driver
        self.exam_schedule_repository = exam_schedule_repository or ExamScheduleRepository(session)
        self.exam_schedule_graph_repository = exam_schedule_graph_repository or ExamScheduleGraphRepository(driver)
    
    async def sync_by_id(self, schedule_id: str) -> bool:
        """
        Synchronize a single exam schedule by ID.
        
        Args:
            schedule_id: ID of the exam schedule to synchronize
            
        Returns:
            True if synchronization was successful, False otherwise
        """
        try:
            # Get exam schedule from SQL database
            schedule = await self.exam_schedule_repository.get_by_id(schedule_id)
            if not schedule:
                logger.warning(f"Exam Schedule with ID {schedule_id} not found in SQL database")
                return False
            
            # Convert the SQLAlchemy model to a dictionary for easier handling
            schedule_dict = {
                "exam_schedule_id": schedule.exam_schedule_id,
                "schedule_id": schedule.exam_schedule_id,  # Add schedule_id alias for Neo4j model
                "exam_subject_id": schedule.exam_subject_id,
                "room_id": schedule.room_id,
                "start_time": schedule.start_time,
                "end_time": schedule.end_time,
                "description": schedule.description,
                "status": schedule.status,
                "exam_id": schedule.exam_id,  # Using property from ExamSchedule model
                "subject_id": schedule.subject_id,  # Using property from ExamSchedule model
                "location_id": schedule.location_id,  # Using property from ExamSchedule model
                "exam_name": schedule.exam_name,  # Direct property access
                "subject_name": schedule.subject_name  # Direct property access
            }
            
            # Convert to Neo4j node and save
            schedule_node = self._convert_to_node(schedule_dict)
            result = await self.exam_schedule_graph_repository.create_or_update(schedule_node)
            
            if result:
                logger.info(f"Successfully synchronized exam schedule {schedule_id}")
                return True
            else:
                logger.error(f"Failed to synchronize exam schedule {schedule_id}")
                return False
            
        except Exception as e:
            logger.error(f"Error synchronizing exam schedule {schedule_id}: {str(e)}")
            return False
    
    async def sync_all(self, limit: Optional[int] = None, offset: int = 0) -> Tuple[int, int]:
        """
        Synchronize all exam schedules from PostgreSQL to Neo4j.
        
        Args:
            limit: Optional maximum number of exam schedules to synchronize
            offset: Optional offset for pagination
            
        Returns:
            Tuple containing counts of (successful, failed) synchronizations
        """
        success_count = 0
        failure_count = 0
        
        try:
            # Get all exam schedules from SQL database
            schedules, total = await self.exam_schedule_repository.get_all(skip=offset, limit=limit or 100)
            
            logger.info(f"Found {total} exam schedules to synchronize")
            
            # Synchronize each exam schedule
            for schedule in schedules:
                if await self.sync_by_id(schedule.exam_schedule_id):
                    success_count += 1
                else:
                    failure_count += 1
                    
            logger.info(f"Exam Schedule synchronization complete. Success: {success_count}, Failed: {failure_count}")
            
        except Exception as e:
            logger.error(f"Error during exam schedule synchronization: {str(e)}")
        
        return success_count, failure_count
    
    def _convert_to_node(self, schedule: Dict[str, Any]) -> ExamScheduleNode:
        """
        Convert a SQL ExamSchedule model to an ExamScheduleNode.
        
        Args:
            schedule: SQL ExamSchedule dictionary
            
        Returns:
            ExamScheduleNode instance ready for Neo4j
        """
        try:
            # Create a meaningful name for the schedule
            schedule_id = schedule.get("exam_schedule_id") or schedule.get("schedule_id")
            name = f"Schedule {schedule_id}"
            
            # Get more descriptive information if available
            exam_name = schedule.get("exam_name")
            subject_name = schedule.get("subject_name")
            start_time = schedule.get("start_time")
            
            if exam_name and subject_name and start_time:
                formatted_time = start_time.strftime("%d/%m/%Y %H:%M") if hasattr(start_time, 'strftime') else start_time
                name = f"{exam_name} - {subject_name} ({formatted_time})"
            elif exam_name and subject_name:
                name = f"{exam_name} - {subject_name}"
            
            # Create the exam schedule node
            schedule_node = ExamScheduleNode(
                schedule_id=schedule_id,
                exam_id=schedule.get("exam_id"),
                subject_id=schedule.get("subject_id"),
                exam_subject_id=schedule.get("exam_subject_id"),
                location_id=schedule.get("location_id"),
                room_id=schedule.get("room_id"),
                start_time=schedule.get("start_time"),
                end_time=schedule.get("end_time"),
                description=schedule.get("description"),
                status=schedule.get("status"),
                date=schedule.get("start_time").date() if schedule.get("start_time") else None,
                additional_info=None
            )
            
            # Set the name explicitly in case the constructor logic changes
            schedule_node.name = name
            
            return schedule_node
            
        except Exception as e:
            logger.error(f"Error converting exam schedule to node: {str(e)}")
            # Return a basic node with just the ID as fallback
            return ExamScheduleNode(
                schedule_id=schedule.get("exam_schedule_id") or schedule.get("schedule_id"),
                exam_id=schedule.get("exam_id"),
                exam_subject_id=schedule.get("exam_subject_id"),
                room_id=schedule.get("room_id")
            ) 