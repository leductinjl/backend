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
        exam_room_repository: Optional[ExamRoomRepository] = None,
        exam_room_graph_repository: Optional[ExamRoomGraphRepository] = None
    ):
        """
        Initialize the ExamRoomSyncService.
        
        Args:
            session: SQLAlchemy async session
            driver: Neo4j async driver
            exam_room_repository: Optional ExamRoomRepository instance
            exam_room_graph_repository: Optional ExamRoomGraphRepository instance
        """
        self.session = session
        self.driver = driver
        self.exam_room_repository = exam_room_repository or ExamRoomRepository(session)
        self.exam_room_graph_repository = exam_room_graph_repository or ExamRoomGraphRepository(driver)
    
    async def sync_by_id(self, room_id: str, skip_relationships: bool = False) -> bool:
        """
        Synchronize a specific exam room by ID.
        
        Args:
            room_id: The ID of the room to sync
            skip_relationships: If True, only sync node without its relationships
            
        Returns:
            True if sync was successful, False otherwise
        """
        logger.info(f"Synchronizing exam room {room_id} (skip_relationships={skip_relationships})")
        
        try:
            # Get room from SQL database
            room = await self.exam_room_repository.get_by_id(room_id)
            if not room:
                logger.error(f"Exam room {room_id} not found in SQL database")
                return False
            
            # Convert to Neo4j format and save
            room_node = self._convert_to_node(room)
            await self.exam_room_graph_repository.create_or_update(room_node)
            
            # Sync relationships if needed
            if not skip_relationships:
                await self.sync_relationships(room_id)
            
            return True
            
        except Exception as e:
            logger.error(f"Error syncing exam room {room_id}: {e}")
            return False
    
    async def sync_relationships(self, room_id: str) -> Dict[str, int]:
        """
        Synchronize relationships for a specific exam room.
        
        Args:
            room_id: ID of the exam room to synchronize relationships for
            
        Returns:
            Dictionary with counts of successfully synced relationships by type
        """
        logger.info(f"Synchronizing relationships for exam room {room_id}")
        
        relationship_counts = {
            "location": 0,
            "schedules": 0
        }
        
        try:
            # Get the room data from SQL
            room = await self.exam_room_repository.get_by_id(room_id)
            if not room:
                logger.error(f"Exam room {room_id} not found in SQL database")
                return relationship_counts
            
            # Use the existing _sync_relationships method
            await self._sync_relationships(room)
            
            # Count relationships
            if room.get("location_id"):
                relationship_counts["location"] += 1
            
            logger.info(f"Exam room relationship synchronization completed for {room_id}")
            return relationship_counts
            
        except Exception as e:
            logger.error(f"Error synchronizing relationships for exam room {room_id}: {e}")
            return relationship_counts
    
    async def _sync_relationships(self, room: Any) -> None:
        """
        Synchronize exam room relationships with other nodes.
        
        Args:
            room: The exam room data (ORM model or dictionary)
        """
        # Extract room_id based on input type
        if isinstance(room, dict):
            room_id = room.get("room_id")
            location_id = room.get("location_id")
            exams = room.get("exams", [])
        elif hasattr(room, "room_id"):
            room_id = room.room_id
            location_id = getattr(room, "location_id", None)
            exams = getattr(room, "exams", [])
        else:
            logger.warning(f"Cannot sync relationships for unsupported room type: {type(room)}")
            return
        
        # Sync LOCATED_IN relationship with location
        if location_id:
            # The relationship is already established in the create_relationships_query method
            # of ExamRoomNode, but we could add additional relationships here
            pass
        
        # If there are exams for this room, sync exam relationships
        for exam in exams:
            exam_id = None
            if isinstance(exam, dict):
                exam_id = exam.get("exam_id")
            elif hasattr(exam, "exam_id"):
                exam_id = exam.exam_id
                
            if exam_id:
                await self.exam_room_graph_repository.add_exam_relationship(
                    room_id, 
                    exam_id
                )
    
    async def sync_all(self, limit: Optional[int] = None, skip_relationships: bool = False) -> Union[Tuple[int, int], Dict[str, int]]:
        """
        Synchronize all exam rooms.
        
        Args:
            limit: Optional limit on number of exam rooms to sync
            skip_relationships: If True, only sync nodes without their relationships
            
        Returns:
            Tuple of (success_count, failed_count) or dict with success/failed counts
        """
        logger.info(f"Synchronizing all exam rooms (skip_relationships={skip_relationships})")
        
        try:
            # Get all exam rooms from SQL database
            rooms, _ = await self.exam_room_repository.get_all(limit=limit)
            
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
                    
                    # Sync the exam room node
                    await self.sync_by_id(room_id, skip_relationships=skip_relationships)
                    success_count += 1
                except Exception as e:
                    logger.error(f"Error syncing exam room {room_id}: {e}")
                    failed_count += 1
            
            return (success_count, failed_count)
            
        except Exception as e:
            logger.error(f"Error during exam room synchronization: {e}")
            return {"success": 0, "failed": 0}
    
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
                    "location_id": room.location_id,
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
                location_id=room_data["location_id"],
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
                location_id = room.get("location_id")
            else:
                room_id = getattr(room, "room_id", "unknown")
                room_name = getattr(room, "room_name", f"Room {room_id}")
                location_id = getattr(room, "location_id", None)
                
            return ExamRoomNode(
                room_id=room_id,
                room_name=room_name,
                location_id=location_id
            ) 