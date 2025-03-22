"""
Exam synchronization service module.

This module provides services for synchronizing exam-related data between
PostgreSQL and Neo4j databases, including exams, exam locations, exam rooms,
and exam schedules.
"""

import logging
import json
import traceback
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.sync.base_sync_service import BaseSyncService
from app.domain.graph_models.exam_node import ExamNode
from app.domain.graph_models.exam_location_node import ExamLocationNode
from app.domain.graph_models.exam_room_node import ExamRoomNode
from app.domain.graph_models.exam_schedule_node import ExamScheduleNode
from app.domain.graph_models.exam_attempt_node import ExamAttemptNode
from app.graph_repositories.exam_graph_repository import ExamGraphRepository
from app.graph_repositories.exam_location_graph_repository import ExamLocationGraphRepository
from app.graph_repositories.exam_room_graph_repository import ExamRoomGraphRepository
from app.graph_repositories.exam_schedule_graph_repository import ExamScheduleGraphRepository
from app.graph_repositories.exam_attempt_graph_repository import ExamAttemptGraphRepository
from app.repositories.repository_factory import RepositoryFactory

logger = logging.getLogger(__name__)

class ExamSyncService(BaseSyncService):
    """
    Service for synchronizing exam-related data between PostgreSQL and Neo4j.
    
    This service handles synchronization of exams, exam locations, exam rooms,
    and exam schedules.
    """
    
    def __init__(self, neo4j_connection, db_session: AsyncSession):
        """Initialize with Neo4j connection and SQLAlchemy session."""
        super().__init__(neo4j_connection, db_session)
        
        # Initialize exam-related repositories
        self.exam_graph_repo = ExamGraphRepository(neo4j_connection)
        self.exam_location_graph_repository = ExamLocationGraphRepository(neo4j_connection)
        self.exam_room_graph_repository = ExamRoomGraphRepository(neo4j_connection)
        self.exam_schedule_graph_repository = ExamScheduleGraphRepository(neo4j_connection)
        self.exam_attempt_graph_repository = ExamAttemptGraphRepository(neo4j_connection)
        
    async def sync_exam(self, exam_model):
        """
        Synchronize an exam from PostgreSQL to Neo4j.
        
        Args:
            exam_model: An Exam SQLAlchemy model or dictionary
        
        Returns:
            bool: True if successful, False otherwise
        """
        await self._log_sync_start("exam", getattr(exam_model, "exam_id", exam_model.get("exam_id")))
        try:
            # Convert to dictionary if SQLAlchemy model
            if not isinstance(exam_model, dict):
                exam_dict = {
                    "exam_id": exam_model.exam_id,
                    "exam_name": exam_model.exam_name,
                    "exam_description": exam_model.exam_description,
                    "exam_type": exam_model.exam_type,
                    "start_date": exam_model.start_date,
                    "end_date": exam_model.end_date,
                    "status": exam_model.status,
                }
            else:
                exam_dict = exam_model
            
            # Create Neo4j node
            exam_node = ExamNode.from_dict(exam_dict)
            
            # Create or update node in Neo4j
            query = exam_node.create_query()
            await self._execute_neo4j_query(query, exam_node.to_dict())
            
            await self._log_sync_success("exam", exam_dict.get("exam_id"))
            return True
        except Exception as e:
            await self._log_sync_error("exam", str(e), getattr(exam_model, "exam_id", exam_model.get("exam_id")))
            logger.error(traceback.format_exc())
            return False
    
    async def sync_exam_location(self, exam_location_model):
        """
        Synchronize an exam location from PostgreSQL to Neo4j.
        
        Args:
            exam_location_model: An ExamLocation SQLAlchemy model or dictionary
        
        Returns:
            bool: True if successful, False otherwise
        """
        location_id = None
        try:
            # Handle both dictionary and SQLAlchemy model
            if isinstance(exam_location_model, dict):
                location_id = exam_location_model.get("location_id")
                location_dict = exam_location_model
                
                # Convert complex objects to JSON strings
                if "contact_info" in location_dict and location_dict["contact_info"] and not isinstance(location_dict["contact_info"], str):
                    location_dict["contact_info"] = json.dumps(location_dict["contact_info"])
                
                if "additional_info" in location_dict and location_dict["additional_info"] and not isinstance(location_dict["additional_info"], str):
                    location_dict["additional_info"] = json.dumps(location_dict["additional_info"])
            else:
                location_id = exam_location_model.location_id
                location_dict = {
                    "location_id": exam_location_model.location_id,
                    "location_name": exam_location_model.location_name,
                    "address": exam_location_model.address,
                    "city": exam_location_model.city,
                    "state": exam_location_model.state,
                    "country": exam_location_model.country,
                    "postal_code": exam_location_model.postal_code,
                    "capacity": exam_location_model.capacity,
                    "status": exam_location_model.status,
                }
                
                # Convert complex objects to JSON strings
                if hasattr(exam_location_model, "contact_info") and exam_location_model.contact_info:
                    location_dict["contact_info"] = (
                        json.dumps(exam_location_model.contact_info)
                        if not isinstance(exam_location_model.contact_info, str)
                        else exam_location_model.contact_info
                    )
                
                if hasattr(exam_location_model, "additional_info") and exam_location_model.additional_info:
                    location_dict["additional_info"] = (
                        json.dumps(exam_location_model.additional_info)
                        if not isinstance(exam_location_model.additional_info, str)
                        else exam_location_model.additional_info
                    )
            
            await self._log_sync_start("exam location", location_id)
            
            # Create Neo4j node
            location_node = ExamLocationNode.from_dict(location_dict)
            
            # Create or update node in Neo4j
            query = location_node.create_query()
            logger.info(f"Executing Neo4j query for exam location {location_id}")
            await self._execute_neo4j_query(query, location_node.to_dict())
            
            # Create relationships if applicable
            if hasattr(location_node, "create_relationships_query") and callable(getattr(location_node, "create_relationships_query")):
                rel_query = location_node.create_relationships_query()
                if rel_query:
                    logger.info(f"Creating relationships for exam location {location_id}")
                    await self._execute_neo4j_query(rel_query, location_node.to_dict())
            
            await self._log_sync_success("exam location", location_id)
            return True
        except Exception as e:
            await self._log_sync_error("exam location", str(e), location_id)
            logger.error(traceback.format_exc())
            return False
    
    async def sync_exam_room(self, exam_room_model):
        """
        Synchronize an exam room from PostgreSQL to Neo4j.
        
        Args:
            exam_room_model: An ExamRoom SQLAlchemy model or dictionary
        
        Returns:
            bool: True if successful, False otherwise
        """
        room_id = None
        try:
            # Handle both dictionary and SQLAlchemy model
            if isinstance(exam_room_model, dict):
                room_id = exam_room_model.get("room_id")
                room_dict = exam_room_model
                
                # Convert complex objects to JSON strings
                if "room_facilities" in room_dict and room_dict["room_facilities"] and not isinstance(room_dict["room_facilities"], str):
                    room_dict["room_facilities"] = json.dumps(room_dict["room_facilities"])
            else:
                room_id = exam_room_model.room_id
                room_dict = {
                    "room_id": exam_room_model.room_id,
                    "location_id": exam_room_model.location_id,
                    "room_name": exam_room_model.room_name,
                    "capacity": exam_room_model.capacity,
                    "room_type": exam_room_model.room_type,
                    "status": exam_room_model.status,
                }
                
                # Convert complex objects to JSON strings
                if hasattr(exam_room_model, "room_facilities") and exam_room_model.room_facilities:
                    room_dict["room_facilities"] = (
                        json.dumps(exam_room_model.room_facilities)
                        if not isinstance(exam_room_model.room_facilities, str)
                        else exam_room_model.room_facilities
                    )
            
            await self._log_sync_start("exam room", room_id)
            
            # Create Neo4j node
            room_node = ExamRoomNode.from_dict(room_dict)
            
            # Create or update node in Neo4j
            query = room_node.create_query()
            logger.info(f"Executing Neo4j query for exam room {room_id}")
            await self._execute_neo4j_query(query, room_node.to_dict())
            
            # Create relationships if applicable
            if hasattr(room_node, "create_relationships_query") and callable(getattr(room_node, "create_relationships_query")):
                rel_query = room_node.create_relationships_query()
                if rel_query:
                    logger.info(f"Creating relationships for exam room {room_id}")
                    await self._execute_neo4j_query(rel_query, room_node.to_dict())
            
            await self._log_sync_success("exam room", room_id)
            return True
        except Exception as e:
            await self._log_sync_error("exam room", str(e), room_id)
            logger.error(traceback.format_exc())
            return False
    
    async def sync_exam_schedule(self, exam_schedule_model):
        """
        Synchronize an exam schedule from PostgreSQL to Neo4j.
        
        Args:
            exam_schedule_model: An ExamSchedule SQLAlchemy model or dictionary
        
        Returns:
            bool: True if successful, False otherwise
        """
        schedule_id = None
        try:
            # Handle both dictionary and SQLAlchemy model
            if isinstance(exam_schedule_model, dict):
                schedule_id = exam_schedule_model.get("exam_schedule_id")
                schedule_dict = exam_schedule_model
            else:
                schedule_id = exam_schedule_model.exam_schedule_id
                schedule_dict = {
                    "exam_schedule_id": exam_schedule_model.exam_schedule_id,
                    "exam_id": exam_schedule_model.exam_id,
                    "room_id": exam_schedule_model.room_id,
                    "start_time": exam_schedule_model.start_time,
                    "end_time": exam_schedule_model.end_time,
                    "schedule_date": exam_schedule_model.schedule_date,
                    "status": exam_schedule_model.status,
                }
            
            await self._log_sync_start("exam schedule", schedule_id)
            
            # Create Neo4j node
            schedule_node = ExamScheduleNode.from_dict(schedule_dict)
            
            # Create or update node in Neo4j
            query = schedule_node.create_query()
            logger.info(f"Executing Neo4j query for exam schedule {schedule_id}")
            await self._execute_neo4j_query(query, schedule_node.to_dict())
            
            # Create relationships if applicable
            if hasattr(schedule_node, "create_relationships_query") and callable(getattr(schedule_node, "create_relationships_query")):
                rel_query = schedule_node.create_relationships_query()
                if rel_query:
                    logger.info(f"Creating relationships for exam schedule {schedule_id}")
                    await self._execute_neo4j_query(rel_query, schedule_node.to_dict())
            
            await self._log_sync_success("exam schedule", schedule_id)
            return True
        except Exception as e:
            await self._log_sync_error("exam schedule", str(e), schedule_id)
            logger.error(traceback.format_exc())
            return False
    
    async def sync_exam_attempt(self, attempt_model):
        """
        Synchronize an exam attempt from PostgreSQL to Neo4j.
        
        Args:
            attempt_model: An ExamAttempt SQLAlchemy model or dictionary
        
        Returns:
            bool: True if successful, False otherwise
        """
        attempt_id = None
        try:
            # Handle both dictionary and SQLAlchemy model
            if isinstance(attempt_model, dict):
                attempt_id = attempt_model.get("attempt_id")
                attempt_dict = attempt_model
            else:
                attempt_id = attempt_model.attempt_id
                attempt_dict = {
                    "attempt_id": attempt_model.attempt_id,
                    "candidate_exam_id": attempt_model.candidate_exam_id,
                    "attempt_number": attempt_model.attempt_number,
                    "attempt_date": attempt_model.attempt_date,
                    "status": attempt_model.status,
                    "notes": attempt_model.notes
                }
            
            await self._log_sync_start("exam attempt", attempt_id)
            
            # Create Neo4j node
            attempt_node = ExamAttemptNode.from_dict(attempt_dict)
            
            # Create or update node in Neo4j
            query = attempt_node.create_query()
            logger.info(f"Executing Neo4j query for exam attempt {attempt_id}")
            await self._execute_neo4j_query(query, attempt_node.to_dict())
            
            # Create relationships if applicable
            if hasattr(attempt_node, "create_relationships_query") and callable(getattr(attempt_node, "create_relationships_query")):
                rel_query = attempt_node.create_relationships_query()
                if rel_query:
                    logger.info(f"Creating relationships for exam attempt {attempt_id}")
                    await self._execute_neo4j_query(rel_query, attempt_node.to_dict())
            
            await self._log_sync_success("exam attempt", attempt_id)
            return True
        except Exception as e:
            await self._log_sync_error("exam attempt", str(e), attempt_id)
            logger.error(traceback.format_exc())
            return False
            
    async def bulk_sync_exams(self):
        """
        Synchronize all exams from PostgreSQL to Neo4j.
        
        Returns:
            int: Number of successfully synchronized exams
        """
        await self._log_sync_start("exam")
        try:
            # Get repository factory
            repo_factory = RepositoryFactory(self.db)
            exam_repo = repo_factory.get_exam_repository()
            
            # Get all exams
            exams = await exam_repo.get_all()
            logger.info(f"Found {len(exams)} exams to sync")
            
            # Sync each exam
            success_count = 0
            for exam in exams:
                if await self.sync_exam(exam):
                    success_count += 1
            
            await self._log_sync_success("exam", count=success_count)
            return success_count
        except Exception as e:
            await self._log_sync_error("exam", str(e))
            logger.error(traceback.format_exc())
            return 0
            
    async def bulk_sync_exam_locations(self):
        """
        Synchronize all exam locations from PostgreSQL to Neo4j.
        
        Returns:
            int: Number of successfully synchronized exam locations
        """
        await self._log_sync_start("exam location")
        try:
            # Get repository factory
            repo_factory = RepositoryFactory(self.db)
            location_repo = repo_factory.get_exam_location_repository()
            mapping_repo = repo_factory.get_exam_location_mapping_repository()
            
            # Get all exam locations
            locations = await location_repo.get_all()
            logger.info(f"Found {len(locations)} exam locations to sync")
            
            # Sync each exam location
            success_count = 0
            for location in locations:
                if await self.sync_exam_location(location):
                    success_count += 1
            
            # Establish relationships with exams
            mappings = await mapping_repo.get_all()
            logger.info(f"Found {len(mappings)} exam-location mappings to sync")
            
            for mapping in mappings:
                # Create relationship between exam and location
                relationship_query = """
                MATCH (e:Exam {exam_id: $exam_id})
                MATCH (l:ExamLocation {location_id: $location_id})
                MERGE (e)-[r:CONDUCTED_AT]->(l)
                RETURN r
                """
                
                params = {
                    "exam_id": mapping.exam_id,
                    "location_id": mapping.location_id
                }
                
                try:
                    await self._execute_neo4j_query(relationship_query, params)
                    logger.info(f"Created relationship between exam {mapping.exam_id} and location {mapping.location_id}")
                except Exception as e:
                    logger.error(f"Error creating relationship between exam {mapping.exam_id} and location {mapping.location_id}: {str(e)}")
            
            await self._log_sync_success("exam location", count=success_count)
            return success_count
        except Exception as e:
            await self._log_sync_error("exam location", str(e))
            logger.error(traceback.format_exc())
            return 0
            
    async def bulk_sync_exam_rooms(self):
        """
        Synchronize all exam rooms from PostgreSQL to Neo4j.
        
        Returns:
            int: Number of successfully synchronized exam rooms
        """
        await self._log_sync_start("exam room")
        try:
            # Get repository factory
            repo_factory = RepositoryFactory(self.db)
            room_repo = repo_factory.get_exam_room_repository()
            
            # Get all exam rooms
            rooms = await room_repo.get_all()
            logger.info(f"Found {len(rooms)} exam rooms to sync")
            
            # Sync each exam room
            success_count = 0
            for room in rooms:
                if await self.sync_exam_room(room):
                    success_count += 1
            
            await self._log_sync_success("exam room", count=success_count)
            return success_count
        except Exception as e:
            await self._log_sync_error("exam room", str(e))
            logger.error(traceback.format_exc())
            return 0
            
    async def bulk_sync_exam_schedules(self):
        """
        Synchronize all exam schedules from PostgreSQL to Neo4j.
        
        Returns:
            int: Number of successfully synchronized exam schedules
        """
        await self._log_sync_start("exam schedule")
        try:
            # Get repository factory
            repo_factory = RepositoryFactory(self.db)
            schedule_repo = repo_factory.get_exam_schedule_repository()
            
            # Get all exam schedules
            schedules = await schedule_repo.get_all()
            logger.info(f"Found {len(schedules)} exam schedules to sync")
            
            # Sync each exam schedule
            success_count = 0
            for schedule in schedules:
                if await self.sync_exam_schedule(schedule):
                    success_count += 1
            
            await self._log_sync_success("exam schedule", count=success_count)
            return success_count
        except Exception as e:
            await self._log_sync_error("exam schedule", str(e))
            logger.error(traceback.format_exc())
            return 0
            
    async def bulk_sync_exam_attempts(self):
        """
        Synchronize all exam attempts from PostgreSQL to Neo4j.
        
        Returns:
            int: Number of successfully synchronized exam attempts
        """
        await self._log_sync_start("exam attempt")
        try:
            # Get repository factory
            repo_factory = RepositoryFactory(self.db)
            attempt_repo = repo_factory.get_exam_attempt_repository()
            
            # Get all exam attempts
            attempts = await attempt_repo.get_all()
            logger.info(f"Found {len(attempts)} exam attempts to sync")
            
            # Sync each exam attempt
            success_count = 0
            for attempt in attempts:
                if await self.sync_exam_attempt(attempt):
                    success_count += 1
            
            await self._log_sync_success("exam attempt", count=success_count)
            return success_count
        except Exception as e:
            await self._log_sync_error("exam attempt", str(e))
            logger.error(traceback.format_exc())
            return 0 