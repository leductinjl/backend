"""
Exam Schedule Sync Service Module.

This module provides the ExamScheduleSyncService class for synchronizing ExamSchedule
data between PostgreSQL and Neo4j.
"""

import logging
from typing import Optional, Tuple, List, Dict, Any, Union

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
    
    async def sync_by_id(self, schedule_id: str, skip_relationships: bool = False) -> bool:
        """
        Synchronize a specific exam schedule by ID.
        
        Args:
            schedule_id: The ID of the exam schedule to sync
            skip_relationships: If True, only sync node without its relationships
            
        Returns:
            True if sync was successful, False otherwise
        """
        logger.info(f"Synchronizing exam schedule {schedule_id} (skip_relationships={skip_relationships})")
        
        try:
            # Get exam schedule from SQL database
            schedule = await self.exam_schedule_repository.get_by_id(schedule_id)
            if not schedule:
                logger.error(f"Exam schedule {schedule_id} not found in SQL database")
                return False
            
            # Convert to Neo4j format
            neo4j_data = self._convert_to_node(schedule)
            
            # Create or update node in Neo4j
            await self.exam_schedule_graph_repository.create_or_update(neo4j_data)
            
            # Sync relationships if needed
            if not skip_relationships:
                await self.sync_relationships(schedule_id)
            
            return True
            
        except Exception as e:
            logger.error(f"Error syncing exam schedule {schedule_id}: {e}")
            return False
    
    async def sync_all(self, limit: Optional[int] = None, skip_relationships: bool = False) -> Union[Tuple[int, int], Dict[str, int]]:
        """
        Synchronize all exam schedules.
        
        Args:
            limit: Optional limit on number of exam schedules to sync
            skip_relationships: If True, only sync nodes without their relationships
            
        Returns:
            Tuple of (success_count, failed_count) or dict with success/failed counts
        """
        logger.info(f"Synchronizing all exam schedules (skip_relationships={skip_relationships})")
        
        try:
            # Get all exam schedules from SQL database
            schedules, _ = await self.exam_schedule_repository.get_all(limit=limit)
            
            success_count = 0
            failed_count = 0
            
            for schedule in schedules:
                try:
                    # Sync the schedule node - handle both ORM objects and dictionaries
                    schedule_id = schedule.exam_schedule_id if hasattr(schedule, 'exam_schedule_id') else schedule.get("exam_schedule_id")
                    if not schedule_id:
                        logger.error(f"Missing exam_schedule_id in schedule object: {schedule}")
                        failed_count += 1
                        continue
                        
                    await self.sync_by_id(schedule_id, skip_relationships=skip_relationships)
                    success_count += 1
                except Exception as e:
                    # Get schedule_id safely for logging
                    schedule_id = getattr(schedule, 'exam_schedule_id', None) if hasattr(schedule, 'exam_schedule_id') else schedule.get("exam_schedule_id", "unknown")
                    logger.error(f"Error syncing schedule {schedule_id}: {e}")
                    failed_count += 1
            
            return (success_count, failed_count)
            
        except Exception as e:
            logger.error(f"Error during exam schedule synchronization: {e}")
            return {"success": 0, "failed": 0}
    
    def _convert_to_node(self, schedule) -> ExamScheduleNode:
        """
        Convert a SQL ExamSchedule model to a ExamScheduleNode.
        
        Args:
            schedule: SQL ExamSchedule model or Dictionary
            
        Returns:
            ExamScheduleNode instance ready for Neo4j
        """
        try:
            # Xác định cách truy cập dữ liệu dựa trên loại đối tượng
            if isinstance(schedule, dict):
                schedule_id = schedule.get("exam_schedule_id") or schedule.get("schedule_id")
                exam_id = schedule.get("exam_id")
                exam_subject_id = schedule.get("exam_subject_id")
                room_id = schedule.get("room_id")
                start_time = schedule.get("start_time")
                end_time = schedule.get("end_time")
                status = schedule.get("status")
                name = f"Schedule for exam {exam_id}" if exam_id else f"Schedule {schedule_id}"
            else:
                # Truy cập trực tiếp từ thuộc tính của đối tượng
                schedule_id = getattr(schedule, "exam_schedule_id", None) or getattr(schedule, "schedule_id", None)
                exam_id = getattr(schedule, "exam_id", None)
                exam_subject_id = getattr(schedule, "exam_subject_id", None)
                room_id = getattr(schedule, "room_id", None)
                start_time = getattr(schedule, "start_time", None)
                end_time = getattr(schedule, "end_time", None)
                status = getattr(schedule, "status", None)
                name = f"Schedule for exam {exam_id}" if exam_id else f"Schedule {schedule_id}"
            
            # Create the exam schedule node
            schedule_node = ExamScheduleNode(
                schedule_id=schedule_id,
                exam_id=exam_id,
                exam_subject_id=exam_subject_id,
                room_id=room_id,
                start_time=start_time,
                end_time=end_time,
                status=status,
                additional_info=None
            )
            
            # Set the name explicitly in case the constructor logic changes
            schedule_node.name = name
            
            return schedule_node
            
        except Exception as e:
            logger.error(f"Error converting exam schedule to node: {str(e)}")
            # Return a basic node with just the ID as fallback
            try:
                # Safe extraction even in error cases
                if isinstance(schedule, dict):
                    schedule_id = schedule.get("exam_schedule_id") or schedule.get("schedule_id", "unknown")
                    exam_id = schedule.get("exam_id")
                    exam_subject_id = schedule.get("exam_subject_id")
                    room_id = schedule.get("room_id")
                else:
                    schedule_id = getattr(schedule, "exam_schedule_id", None) or getattr(schedule, "schedule_id", "unknown")
                    exam_id = getattr(schedule, "exam_id", None)
                    exam_subject_id = getattr(schedule, "exam_subject_id", None)
                    room_id = getattr(schedule, "room_id", None)
                    
                return ExamScheduleNode(
                    schedule_id=schedule_id,
                    exam_id=exam_id,
                    exam_subject_id=exam_subject_id,
                    room_id=room_id
                )
            except:
                # Ultimate fallback if even basic extraction fails
                return ExamScheduleNode(
                    schedule_id="unknown",
                    exam_id=None,
                    exam_subject_id=None,
                    room_id=None
                )
            
    async def sync_relationships(self, schedule_id: str) -> Dict[str, int]:
        """
        Synchronize relationships for a specific exam schedule.
        
        Args:
            schedule_id: ID of the exam schedule to synchronize relationships for
            
        Returns:
            Dictionary with counts of successfully synced relationships by type
        """
        logger.info(f"Synchronizing relationships for exam schedule {schedule_id}")
        
        relationship_counts = {
            "exam": 0,
            "subject": 0,
            "room": 0,
            "location": 0
        }
        
        try:
            # Get exam schedule from SQL database with full details
            schedule = await self.exam_schedule_repository.get_by_id(schedule_id)
            if not schedule:
                logger.error(f"Exam schedule {schedule_id} not found in SQL database")
                return relationship_counts
            
            # Extract IDs for relationships
            exam_id = schedule.get("exam_id")
            subject_id = schedule.get("subject_id")
            room_id = schedule.get("room_id")
            location_id = schedule.get("location_id")
            
            # Sync FOR_EXAM relationship (schedule-exam)
            if exam_id:
                success = await self.exam_schedule_graph_repository.add_for_exam_relationship(schedule_id, exam_id)
                if success:
                    relationship_counts["exam"] += 1
            
            # Sync FOR_SUBJECT relationship (schedule-subject)
            if subject_id:
                success = await self.exam_schedule_graph_repository.add_for_subject_relationship(schedule_id, subject_id)
                if success:
                    relationship_counts["subject"] += 1
            
            # Sync IN_ROOM relationship (schedule-room)
            if room_id:
                success = await self.exam_schedule_graph_repository.add_in_room_relationship(schedule_id, room_id)
                if success:
                    relationship_counts["room"] += 1
            
            # Sync AT_LOCATION relationship (schedule-location)
            if location_id:
                success = await self.exam_schedule_graph_repository.add_at_location_relationship(schedule_id, location_id)
                if success:
                    relationship_counts["location"] += 1
            
            logger.info(f"Exam schedule relationship synchronization completed for {schedule_id}")
            return relationship_counts
            
        except Exception as e:
            logger.error(f"Error synchronizing relationships for exam schedule {schedule_id}: {e}")
            return relationship_counts 