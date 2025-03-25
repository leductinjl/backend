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
        sql_repository: Optional[ExamScheduleRepository] = None,
        graph_repository: Optional[ExamScheduleGraphRepository] = None
    ):
        """
        Initialize the ExamScheduleSyncService.
        
        Args:
            session: SQLAlchemy async session
            driver: Neo4j async driver
            sql_repository: Optional ExamScheduleRepository instance
            graph_repository: Optional ExamScheduleGraphRepository instance
        """
        super().__init__(session, driver, sql_repository, graph_repository)
        self.session = session
        self.driver = driver
        self.sql_repository = sql_repository or ExamScheduleRepository(session)
        self.graph_repository = graph_repository or ExamScheduleGraphRepository(driver)
    
    async def sync_node_by_id(self, schedule_id: str) -> bool:
        """
        Synchronize a specific exam schedule node by ID, only creating the node and INSTANCE_OF relationship.
        
        Args:
            schedule_id: The ID of the exam schedule to sync
            
        Returns:
            True if sync was successful, False otherwise
        """
        logger.info(f"Synchronizing exam schedule node {schedule_id}")
        
        try:
            # Get exam schedule from SQL database
            schedule = await self.sql_repository.get_by_id(schedule_id)
            if not schedule:
                logger.error(f"Exam schedule {schedule_id} not found in SQL database")
                return False
            
            # Convert to Neo4j format
            neo4j_data = self._convert_to_node(schedule)
            
            # Create or update node in Neo4j
            result = await self.graph_repository.create_or_update(neo4j_data)
            
            logger.info(f"Successfully synchronized exam schedule node {schedule_id}")
            return result
            
        except Exception as e:
            logger.error(f"Error syncing exam schedule node {schedule_id}: {e}")
            return False
    
    async def sync_all_nodes(self, limit: Optional[int] = None) -> Tuple[int, int]:
        """
        Synchronize all exam schedule nodes, without their relationships (except INSTANCE_OF).
        
        Args:
            limit: Optional limit on number of exam schedules to sync
            
        Returns:
            Tuple of (success_count, failed_count)
        """
        logger.info(f"Synchronizing all exam schedule nodes (limit={limit})")
        
        try:
            # Get all exam schedules from SQL database
            schedules, _ = await self.sql_repository.get_all(limit=limit)
            
            success_count = 0
            failed_count = 0
            
            for schedule in schedules:
                try:
                    # Sync only the schedule node - handle both ORM objects and dictionaries
                    schedule_id = schedule.exam_schedule_id if hasattr(schedule, 'exam_schedule_id') else schedule.get("exam_schedule_id")
                    if not schedule_id:
                        logger.error(f"Missing exam_schedule_id in schedule object: {schedule}")
                        failed_count += 1
                        continue
                        
                    if await self.sync_node_by_id(schedule_id):
                        success_count += 1
                    else:
                        failed_count += 1
                except Exception as e:
                    # Get schedule_id safely for logging
                    schedule_id = getattr(schedule, 'exam_schedule_id', None) if hasattr(schedule, 'exam_schedule_id') else schedule.get("exam_schedule_id", "unknown")
                    logger.error(f"Error syncing schedule node {schedule_id}: {e}")
                    failed_count += 1
            
            logger.info(f"Completed synchronizing exam schedule nodes: {success_count} successful, {failed_count} failed")
            return (success_count, failed_count)
            
        except Exception as e:
            logger.error(f"Error during exam schedule nodes synchronization: {e}")
            return (0, 0)
    
    async def sync_relationship_by_id(self, schedule_id: str) -> Dict[str, int]:
        """
        Synchronize relationships for a specific exam schedule.
        
        Args:
            schedule_id: ID of the exam schedule to synchronize relationships for
            
        Returns:
            Dictionary with counts of successfully synced relationships by type
        """
        logger.info(f"Synchronizing relationships for exam schedule {schedule_id}")
        
        # Check if exam schedule node exists before syncing relationships
        schedule_node = await self.graph_repository.get_by_id(schedule_id)
        if not schedule_node:
            logger.warning(f"Exam schedule node {schedule_id} not found in Neo4j, skipping relationship sync")
            return {
                "error": "Exam schedule node not found in Neo4j",
                "exam": 0,
                "subject": 0,
                "room": 0,
                "location": 0
            }
        
        relationship_counts = {
            "exam": 0,
            "subject": 0,
            "room": 0,
            "location": 0
        }
        
        try:
            # Get exam schedule from SQL database with full details
            schedule = await self.sql_repository.get_by_id(schedule_id)
            if not schedule:
                logger.error(f"Exam schedule {schedule_id} not found in SQL database")
                return relationship_counts
            
            # Extract IDs for relationships - handle both ORM objects and dictionaries
            if isinstance(schedule, dict):
                exam_id = schedule.get("exam_id")
                subject_id = schedule.get("subject_id")
                room_id = schedule.get("room_id")
                location_id = schedule.get("location_id")
            else:
                # Using property accessors or direct attribute access for ORM objects
                exam_id = getattr(schedule, "exam_id", None)
                subject_id = getattr(schedule, "subject_id", None)
                room_id = getattr(schedule, "room_id", None)
                location_id = getattr(schedule, "location_id", None)
            
            # Sync FOR_EXAM relationship (schedule-exam)
            if exam_id:
                success = await self.graph_repository.add_for_exam_relationship(schedule_id, exam_id)
                if success:
                    relationship_counts["exam"] += 1
            
            # Sync FOR_SUBJECT relationship (schedule-subject)
            if subject_id:
                success = await self.graph_repository.add_for_subject_relationship(schedule_id, subject_id)
                if success:
                    relationship_counts["subject"] += 1
            
            # Sync IN_ROOM relationship (schedule-room)
            if room_id:
                success = await self.graph_repository.add_in_room_relationship(schedule_id, room_id)
                if success:
                    relationship_counts["room"] += 1
            
            # Sync AT_LOCATION relationship (schedule-location)
            if location_id:
                success = await self.graph_repository.add_at_location_relationship(schedule_id, location_id)
                if success:
                    relationship_counts["location"] += 1
            
            logger.info(f"Exam schedule relationship synchronization completed for {schedule_id}: {relationship_counts}")
            return relationship_counts
            
        except Exception as e:
            logger.error(f"Error synchronizing relationships for exam schedule {schedule_id}: {e}")
            return relationship_counts
    
    async def sync_all_relationships(self, limit: Optional[int] = None) -> Dict[str, int]:
        """
        Synchronize relationships for all exam schedules.
        
        Args:
            limit: Optional maximum number of exam schedules to process
            
        Returns:
            Dictionary with counts of synced relationships by type
        """
        logger.info(f"Synchronizing relationships for all exam schedules (limit={limit})")
        
        try:
            # Get all exam schedules from SQL database
            schedules, total_count = await self.sql_repository.get_all(limit=limit)
            
            total_schedules = len(schedules)
            success_count = 0
            failure_count = 0
            
            # Aggregated counts for all relationship types
            relationship_counts = {
                "exam": 0,
                "subject": 0,
                "room": 0,
                "location": 0
            }
            
            # For each exam schedule, sync relationships
            for schedule in schedules:
                try:
                    # Get schedule_id safely - handle both ORM objects and dictionaries
                    schedule_id = schedule.exam_schedule_id if hasattr(schedule, 'exam_schedule_id') else schedule.get("exam_schedule_id")
                    if not schedule_id:
                        logger.error(f"Missing exam_schedule_id in schedule object: {schedule}")
                        failure_count += 1
                        continue
                    
                    # Verify exam schedule exists in Neo4j
                    schedule_node = await self.graph_repository.get_by_id(schedule_id)
                    if not schedule_node:
                        logger.warning(f"Exam schedule {schedule_id} not found in Neo4j, skipping relationship sync")
                        failure_count += 1
                        continue
                    
                    # Sync relationships for this exam schedule
                    results = await self.sync_relationship_by_id(schedule_id)
                    
                    # Update aggregated counts
                    for key, value in results.items():
                        if key in relationship_counts:
                            relationship_counts[key] += value
                    
                    success_count += 1
                    
                except Exception as e:
                    # Get schedule_id safely for logging
                    schedule_id = getattr(schedule, 'exam_schedule_id', None) if hasattr(schedule, 'exam_schedule_id') else schedule.get("exam_schedule_id", "unknown")
                    logger.error(f"Error synchronizing relationships for exam schedule {schedule_id}: {e}")
                    failure_count += 1
            
            # Prepare final result
            result = {
                "total_schedules": total_schedules,
                "success": success_count,
                "failed": failure_count,
                "relationships": relationship_counts
            }
            
            logger.info(f"Completed synchronizing relationships for all exam schedules: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error during exam schedule relationships synchronization: {e}")
            return {
                "total_schedules": 0,
                "success": 0,
                "failed": 0,
                "error": str(e),
                "relationships": {}
            }
    
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
                exam_name = schedule.get("exam_name")
                subject_name = schedule.get("subject_name")
                start_time = schedule.get("start_time")
                end_time = schedule.get("end_time")
                status = schedule.get("status")
                description = schedule.get("description")
                
                # Tạo tên có ý nghĩa
                name = f"Schedule {schedule_id}"
                if exam_name and subject_name and start_time:
                    formatted_time = start_time.strftime("%d/%m/%Y %H:%M") if hasattr(start_time, 'strftime') else start_time
                    name = f"{exam_name} - {subject_name} ({formatted_time})"
                elif exam_name and subject_name:
                    name = f"{exam_name} - {subject_name}"
            else:
                # Truy cập trực tiếp từ thuộc tính của đối tượng
                schedule_id = getattr(schedule, "exam_schedule_id", None) or getattr(schedule, "schedule_id", None)
                exam_name = getattr(schedule, "exam_name", None)
                subject_name = getattr(schedule, "subject_name", None)
                start_time = getattr(schedule, "start_time", None)
                end_time = getattr(schedule, "end_time", None)
                status = getattr(schedule, "status", None)
                description = getattr(schedule, "description", None)
                
                # Tạo tên có ý nghĩa
                name = f"Schedule {schedule_id}"
                if exam_name and subject_name and start_time:
                    formatted_time = start_time.strftime("%d/%m/%Y %H:%M") if hasattr(start_time, 'strftime') else start_time
                    name = f"{exam_name} - {subject_name} ({formatted_time})"
                elif exam_name and subject_name:
                    name = f"{exam_name} - {subject_name}"
            
            # Create the exam schedule node
            schedule_node = ExamScheduleNode(
                schedule_id=schedule_id,
                start_time=start_time,
                end_time=end_time,
                status=status,
                description=description,
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
                else:
                    schedule_id = getattr(schedule, "exam_schedule_id", None) or getattr(schedule, "schedule_id", "unknown")
                    
                return ExamScheduleNode(
                    schedule_id=schedule_id
                )
            except:
                # Ultimate fallback if even basic extraction fails
                return ExamScheduleNode(
                    schedule_id="unknown"
                )