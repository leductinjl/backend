"""
Exam Room Sync Service Module.

This module provides the ExamRoomSyncService class for synchronizing ExamRoom
data between PostgreSQL and Neo4j.
"""

import logging
from typing import Optional, Tuple, List, Dict, Any, Union

from sqlalchemy.ext.asyncio import AsyncSession
from neo4j import AsyncDriver

from app.domain.models.exam_room import ExamRoom
from app.domain.graph_models.exam_room_node import ExamRoomNode
from app.repositories.exam_room_repository import ExamRoomRepository
from app.graph_repositories.exam_room_graph_repository import ExamRoomGraphRepository
from app.services.sync.base_sync_service import BaseSyncService

logger = logging.getLogger(__name__)

class ExamRoomSyncService(BaseSyncService):
    """
    Service for synchronizing ExamRoom data between PostgreSQL and Neo4j.
    
    This service implements the BaseSyncService abstract class and provides
    methods for synchronizing individual exam rooms by ID and synchronizing
    all exam rooms in the database.
    """
    
    def __init__(
        self,
        session: AsyncSession,
        driver: AsyncDriver,
        sql_repository: Optional[ExamRoomRepository] = None,
        graph_repository: Optional[ExamRoomGraphRepository] = None
    ):
        """
        Initialize the ExamRoomSyncService.
        
        Args:
            session: SQLAlchemy async session
            driver: Neo4j async driver
            sql_repository: Optional ExamRoomRepository instance
            graph_repository: Optional ExamRoomGraphRepository instance
        """
        super().__init__(session, driver, sql_repository, graph_repository)
        self.session = session
        self.driver = driver
        self.sql_repository = sql_repository or ExamRoomRepository(session)
        self.graph_repository = graph_repository or ExamRoomGraphRepository(driver)
    
    async def sync_node_by_id(self, room_id: str) -> bool:
        """
        Synchronize a specific exam room node by ID, only creating the node and INSTANCE_OF relationship.
        
        Args:
            room_id: The ID of the room to sync
            
        Returns:
            True if sync was successful, False otherwise
        """
        logger.info(f"Synchronizing exam room node {room_id}")
        
        try:
            # Get room from SQL database
            room = await self.sql_repository.get_by_id(room_id)
            if not room:
                logger.error(f"Exam room {room_id} not found in SQL database")
                return False
            
            # Convert to Neo4j format and save
            room_node = self._convert_to_node(room)
            result = await self.graph_repository.create_or_update(room_node)
            
            logger.info(f"Successfully synchronized exam room node {room_id}")
            return result
            
        except Exception as e:
            logger.error(f"Error syncing exam room node {room_id}: {e}")
            return False
    
    async def sync_relationship_by_id(self, room_id: str) -> Dict[str, int]:
        """
        Synchronize relationships for a specific exam room.
        
        Args:
            room_id: ID of the exam room to synchronize relationships for
            
        Returns:
            Dictionary with counts of successfully synced relationships by type
        """
        logger.info(f"Synchronizing relationships for exam room {room_id}")
        
        # Check if exam room node exists before syncing relationships
        room_node = await self.graph_repository.get_by_id(room_id)
        if not room_node:
            logger.warning(f"Exam room node {room_id} not found in Neo4j, skipping relationship sync")
            return {
                "error": "Exam room node not found in Neo4j",
                "location": 0,
                "schedules": 0
            }
        
        try:
            # Get the room data from SQL
            room = await self.sql_repository.get_by_id(room_id)
            if not room:
                logger.error(f"Exam room {room_id} not found in SQL database")
                return {
                    "location": 0,
                    "schedules": 0
                }
            
            # Use the existing _sync_relationships method and get the result
            relationship_counts = await self._sync_relationships(room)
            
            logger.info(f"Exam room relationship synchronization completed for {room_id}: {relationship_counts}")
            return relationship_counts
            
        except Exception as e:
            logger.error(f"Error synchronizing relationships for exam room {room_id}: {e}")
            return {
                "location": 0,
                "schedules": 0
            }
    
    async def _sync_relationships(self, room: Any) -> Dict[str, int]:
        """
        Synchronize exam room relationships with other nodes.
        
        Args:
            room: The exam room data (ORM model or dictionary)
            
        Returns:
            Dictionary with counts of successfully synced relationships by type
        """
        # Initialize relationship counts
        relationship_counts = {
            "location": 0,
            "schedules": 0
        }
        
        # Extract room_id based on input type
        if isinstance(room, dict):
            room_id = room.get("room_id")
            location_id = room.get("location_id")
            schedules = room.get("schedules", [])
        elif hasattr(room, "room_id"):
            room_id = room.room_id
            location_id = getattr(room, "location_id", None)
            schedules = getattr(room, "schedules", [])
        else:
            logger.warning(f"Cannot sync relationships for unsupported room type: {type(room)}")
            return relationship_counts
        
        # Sync LOCATED_IN relationship with location
        if location_id:
            # The relationship is already established in the create_relationships_query method
            # of ExamRoomNode, but we could add additional relationships here
            logger.info(f"Room {room_id} is located in location {location_id}")
            relationship_counts["location"] += 1
        
        # Sync HAS_SCHEDULE relationships
        if schedules:
            logger.info(f"Found {len(schedules)} schedules for room {room_id}")
            # Log all schedules for debugging
            for i, schedule in enumerate(schedules):
                if isinstance(schedule, dict):
                    logger.debug(f"Schedule {i+1} data: {schedule}")
                else:
                    logger.debug(f"Schedule {i+1} attributes: {dir(schedule)}")
                
            for schedule in schedules:
                # Extract schedule_id safely
                schedule_id = None
                if isinstance(schedule, dict):
                    schedule_id = schedule.get("schedule_id")
                    logger.debug(f"Processing schedule: {schedule}")
                elif hasattr(schedule, "schedule_id"):
                    schedule_id = schedule.schedule_id
                elif hasattr(schedule, "exam_schedule_id"):
                    schedule_id = schedule.exam_schedule_id
                    
                if schedule_id:
                    logger.info(f"Attempting to create relationship for schedule {schedule_id}")
                    success = await self.graph_repository.add_schedule_relationship(room_id, schedule_id)
                    if success:
                        relationship_counts["schedules"] += 1
                        logger.info(f"Added HAS_SCHEDULE relationship between {room_id} and {schedule_id}")
                    else:
                        logger.warning(f"Failed to add HAS_SCHEDULE relationship between {room_id} and {schedule_id}")
                else:
                    logger.warning(f"Could not extract schedule_id from schedule data: {schedule}")
        else:
            logger.info(f"No schedules found for room {room_id}")
            
        return relationship_counts
    
    async def sync_all_nodes(self, limit: Optional[int] = None) -> Tuple[int, int]:
        """
        Synchronize all exam room nodes, without their relationships (except INSTANCE_OF).
        
        Args:
            limit: Optional limit on number of exam rooms to sync
            
        Returns:
            Tuple of (success_count, failed_count)
        """
        logger.info(f"Synchronizing all exam room nodes (limit={limit})")
        
        try:
            # Get all exam rooms from SQL database
            rooms, _ = await self.sql_repository.get_all(limit=limit)
            
            success_count = 0
            failed_count = 0
            
            for room in rooms:
                try:
                    # Get room_id based on input type
                    if isinstance(room, ExamRoom):
                        room_id = room.room_id
                    elif isinstance(room, dict):
                        room_id = room.get("room_id")
                    else:
                        logger.warning(f"Unexpected room data type: {type(room)}")
                        failed_count += 1
                        continue
                    
                    # Sync only the exam room node
                    if await self.sync_node_by_id(room_id):
                        success_count += 1
                    else:
                        failed_count += 1
                except Exception as e:
                    # Get room_id safely for logging
                    if isinstance(room, ExamRoom):
                        room_id = room.room_id
                    elif isinstance(room, dict):
                        room_id = room.get("room_id", "unknown")
                    else:
                        room_id = "unknown"
                    logger.error(f"Error syncing exam room node {room_id}: {e}")
                    failed_count += 1
            
            logger.info(f"Completed synchronizing exam room nodes: {success_count} successful, {failed_count} failed")
            return (success_count, failed_count)
            
        except Exception as e:
            logger.error(f"Error during exam room nodes synchronization: {e}")
            return (0, 0)
    
    async def sync_all_relationships(self, limit: Optional[int] = None) -> Dict[str, int]:
        """
        Synchronize relationships for all exam rooms.
        
        Args:
            limit: Optional maximum number of exam rooms to process
            
        Returns:
            Dictionary with counts of synced relationships by type
        """
        logger.info(f"Synchronizing relationships for all exam rooms (limit={limit})")
        
        try:
            # Get all exam rooms from SQL database
            rooms, total_count = await self.sql_repository.get_all(limit=limit)
            
            total_rooms = len(rooms)
            success_count = 0
            failure_count = 0
            
            # Aggregated counts for all relationship types
            relationship_counts = {
                "location": 0,
                "schedules": 0
            }
            
            # For each exam room, sync relationships
            for room in rooms:
                try:
                    # Get room_id safely - handle both ORM objects and dictionaries
                    if isinstance(room, ExamRoom):
                        room_id = room.room_id
                    elif isinstance(room, dict):
                        room_id = room.get("room_id")
                    else:
                        logger.warning(f"Unexpected room data type: {type(room)}")
                        failure_count += 1
                        continue
                    
                    # Verify exam room exists in Neo4j
                    room_node = await self.graph_repository.get_by_id(room_id)
                    if not room_node:
                        logger.warning(f"Exam room {room_id} not found in Neo4j, skipping relationship sync")
                        failure_count += 1
                        continue
                    
                    # Sync relationships for this exam room
                    results = await self.sync_relationship_by_id(room_id)
                    
                    # Update aggregated counts
                    for key, value in results.items():
                        if key in relationship_counts:
                            relationship_counts[key] += value
                    
                    success_count += 1
                    
                except Exception as e:
                    # Get room_id safely for logging
                    if isinstance(room, ExamRoom):
                        room_id = room.room_id
                    elif isinstance(room, dict):
                        room_id = room.get("room_id", "unknown")
                    else:
                        room_id = "unknown"
                    logger.error(f"Error synchronizing relationships for exam room {room_id}: {e}")
                    failure_count += 1
            
            # Prepare final result
            result = {
                "total_rooms": total_rooms,
                "success": success_count,
                "failed": failure_count,
                "relationships": relationship_counts
            }
            
            logger.info(f"Completed synchronizing relationships for all exam rooms: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error during exam room relationships synchronization: {e}")
            return {
                "total_rooms": 0,
                "success": 0,
                "failed": 0,
                "error": str(e),
                "relationships": {}
            }
    
    def _convert_to_node(self, room: Any) -> ExamRoomNode:
        """
        Convert a SQL ExamRoom model to an ExamRoomNode.
        
        Args:
            room: SQL ExamRoom model or dictionary
            
        Returns:
            ExamRoomNode instance ready for Neo4j
        """
        try:
            # Handle different input types
            if isinstance(room, dict):
                room_data = room
            elif isinstance(room, ExamRoom):
                # Convert ORM model to dictionary
                room_data = {
                    "room_id": room.room_id,
                    "room_name": room.room_name,
                    "capacity": room.capacity,
                    "floor": room.floor,
                    "room_number": room.room_number,
                    "is_active": room.is_active,
                    "equipment": getattr(room, "equipment", None),
                    "description": getattr(room, "description", None),
                    "special_requirements": getattr(room, "special_requirements", None)
                }
            else:
                raise ValueError(f"Unsupported room data type: {type(room)}")
            
            # Extract equipment as room_facilities if available
            room_facilities = room_data.get("equipment")
            
            # Create the exam room node
            room_node = ExamRoomNode(
                room_id=room_data["room_id"],
                room_name=room_data["room_name"],
                capacity=room_data.get("capacity"),
                floor=room_data.get("floor"),
                room_number=room_data.get("room_number"),
                room_type=None,  # Not in SQL model but available in Neo4j model
                status=room_data.get("is_active"),
                room_facilities=room_facilities,
                additional_info=room_data.get("description") or room_data.get("special_requirements")
            )
            
            return room_node
            
        except Exception as e:
            logger.error(f"Error converting exam room to node: {str(e)}")
            # Return a basic node with just the ID as fallback
            if isinstance(room, dict):
                room_id = room.get("room_id")
                room_name = room.get("room_name", f"Room {room_id}")
            else:
                room_id = getattr(room, "room_id", "unknown")
                room_name = getattr(room, "room_name", f"Room {room_id}")
                
            return ExamRoomNode(
                room_id=room_id,
                room_name=room_name
            ) 