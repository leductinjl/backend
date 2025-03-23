"""
Exam Room Sync Service Module.

This module provides the ExamRoomSyncService class for synchronizing ExamRoom
data between PostgreSQL and Neo4j.
"""

import logging
from typing import Optional, Tuple, List, Dict, Any

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
    
    async def sync_by_id(self, room_id: str) -> bool:
        """
        Synchronize a single exam room by ID.
        
        Args:
            room_id: ID of the exam room to synchronize
            
        Returns:
            True if synchronization was successful, False otherwise
        """
        try:
            # Get exam room from SQL database
            room = await self.exam_room_repository.get_by_id(room_id)
            if not room:
                logger.warning(f"Exam Room with ID {room_id} not found in SQL database")
                return False
            
            # Convert to Neo4j node and save
            room_node = self._convert_to_node(room)
            result = await self.exam_room_graph_repository.create_or_update(room_node)
            
            if result:
                # Synchronize key relationships
                await self._sync_relationships(room)
                logger.info(f"Successfully synchronized exam room {room_id}")
                return True
            else:
                logger.error(f"Failed to synchronize exam room {room_id}")
                return False
            
        except Exception as e:
            logger.error(f"Error synchronizing exam room {room_id}: {str(e)}")
            return False
    
    async def _sync_relationships(self, room: Dict[str, Any]) -> None:
        """
        Synchronize exam room relationships with other nodes.
        
        Args:
            room: The exam room data dictionary
        """
        room_id = room.get("room_id")
        
        # Sync LOCATED_IN relationship with location
        if "location_id" in room and room["location_id"]:
            # The relationship is already established in the create_relationships_query method
            # of ExamRoomNode, but we could add additional relationships here
            pass
        
        # If there are exams for this room, sync exam relationships
        for exam in room.get("exams", []):
            if "exam_id" in exam:
                await self.exam_room_graph_repository.add_exam_relationship(
                    room_id, 
                    exam["exam_id"]
                )
    
    async def sync_all(self, limit: Optional[int] = None, offset: int = 0) -> Tuple[int, int]:
        """
        Synchronize all exam rooms from PostgreSQL to Neo4j.
        
        Args:
            limit: Optional maximum number of exam rooms to synchronize
            offset: Optional offset for pagination
            
        Returns:
            Tuple containing counts of (successful, failed) synchronizations
        """
        success_count = 0
        failure_count = 0
        
        try:
            # Get all exam rooms from SQL database
            rooms, total = await self.exam_room_repository.get_all(skip=offset, limit=limit or 100)
            
            logger.info(f"Found {total} exam rooms to synchronize")
            
            # Synchronize each exam room
            for room in rooms:
                room_id = room.get("room_id")
                if await self.sync_by_id(room_id):
                    success_count += 1
                else:
                    failure_count += 1
                    
            logger.info(f"Exam Room synchronization complete. Success: {success_count}, Failed: {failure_count}")
            
        except Exception as e:
            logger.error(f"Error during exam room synchronization: {str(e)}")
        
        return success_count, failure_count
    
    def _convert_to_node(self, room: Dict[str, Any]) -> ExamRoomNode:
        """
        Convert a SQL ExamRoom model to an ExamRoomNode.
        
        Args:
            room: SQL ExamRoom dictionary
            
        Returns:
            ExamRoomNode instance ready for Neo4j
        """
        try:
            # Extract equipment as room_facilities if available
            room_facilities = room.get("equipment")
            
            # Create the exam room node
            room_node = ExamRoomNode(
                room_id=room["room_id"],
                room_name=room["room_name"],
                location_id=room["location_id"],
                capacity=room["capacity"],
                floor=room["floor"],
                room_number=room["room_number"],
                room_type=None,  # Not in SQL model but available in Neo4j model
                status=room["is_active"],
                room_facilities=room_facilities,
                additional_info=room.get("description") or room.get("special_requirements")
            )
            
            return room_node
            
        except Exception as e:
            logger.error(f"Error converting exam room to node: {str(e)}")
            # Return a basic node with just the ID as fallback
            return ExamRoomNode(
                room_id=room["room_id"],
                room_name=room.get("room_name", f"Room {room['room_id']}"),
                location_id=room.get("location_id")
            ) 