"""
Exam Location Sync Service Module.

This module provides the ExamLocationSyncService class for synchronizing ExamLocation
data between PostgreSQL and Neo4j.
"""

import logging
from typing import Optional, Tuple, List, Dict, Any, Union

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from neo4j import AsyncDriver

from app.domain.models.exam_location import ExamLocation
from app.domain.graph_models.exam_location_node import ExamLocationNode
from app.repositories.exam_location_repository import ExamLocationRepository
from app.graph_repositories.exam_location_graph_repository import ExamLocationGraphRepository
from app.services.sync.base_sync_service import BaseSyncService

logger = logging.getLogger(__name__)

class ExamLocationSyncService(BaseSyncService):
    """
    Service for synchronizing ExamLocation data between PostgreSQL and Neo4j.
    
    This service implements the BaseSyncService abstract class and provides
    methods for synchronizing individual exam locations by ID and synchronizing
    all exam locations in the database.
    """
    
    def __init__(
        self,
        session: AsyncSession,
        driver: AsyncDriver,
        exam_location_repository: Optional[ExamLocationRepository] = None,
        exam_location_graph_repository: Optional[ExamLocationGraphRepository] = None
    ):
        """
        Initialize the ExamLocationSyncService.
        
        Args:
            session: SQLAlchemy async session
            driver: Neo4j async driver
            exam_location_repository: Optional ExamLocationRepository instance
            exam_location_graph_repository: Optional ExamLocationGraphRepository instance
        """
        self.session = session
        self.driver = driver
        self.exam_location_repository = exam_location_repository or ExamLocationRepository(session)
        self.exam_location_graph_repository = exam_location_graph_repository or ExamLocationGraphRepository(driver)
    
    async def sync_by_id(self, location_id: str, skip_relationships: bool = False) -> bool:
        """
        Synchronize a specific exam location by ID.
        
        Args:
            location_id: The ID of the exam location to sync
            skip_relationships: If True, only sync node without its relationships
            
        Returns:
            True if sync was successful, False otherwise
        """
        logger.info(f"Synchronizing exam location {location_id} (skip_relationships={skip_relationships})")
        
        try:
            # Get exam location from SQL database
            location = await self.exam_location_repository.get_by_id(location_id)
            if not location:
                logger.error(f"Exam location {location_id} not found in SQL database")
                return False
            
            # Convert to Neo4j format
            neo4j_data = self._convert_to_node(location)
            
            # Create or update node in Neo4j
            await self.exam_location_graph_repository.create_or_update(neo4j_data)
            
            # Sync relationships if needed
            if not skip_relationships:
                await self.sync_relationships(location_id)
            
            return True
            
        except Exception as e:
            logger.error(f"Error syncing exam location {location_id}: {e}")
            return False
    
    async def sync_all(self, limit: Optional[int] = None, skip_relationships: bool = False) -> Union[Tuple[int, int], Dict[str, int]]:
        """
        Synchronize all exam locations.
        
        Args:
            limit: Optional limit on number of exam locations to sync
            skip_relationships: If True, only sync nodes without their relationships
            
        Returns:
            Tuple of (success_count, failed_count) or dict with success/failed counts
        """
        logger.info(f"Synchronizing all exam locations (skip_relationships={skip_relationships})")
        
        try:
            # Get all exam locations from SQL database
            locations, _ = await self.exam_location_repository.get_all(limit=limit)
            
            success_count = 0
            failed_count = 0
            
            for location in locations:
                try:
                    # Sync the location node - handle both ORM objects and dictionaries
                    location_id = location.location_id if hasattr(location, 'location_id') else location.get("location_id")
                    if not location_id:
                        logger.error(f"Missing location_id in location object: {location}")
                        failed_count += 1
                        continue
                        
                    await self.sync_by_id(location_id, skip_relationships=skip_relationships)
                    success_count += 1
                except Exception as e:
                    # Get location_id safely for logging
                    location_id = getattr(location, 'location_id', None) if hasattr(location, 'location_id') else location.get("location_id", "unknown")
                    logger.error(f"Error syncing location {location_id}: {e}")
                    failed_count += 1
            
            return (success_count, failed_count)
            
        except Exception as e:
            logger.error(f"Error during exam location synchronization: {e}")
            return {"success": 0, "failed": 0}
    
    def _convert_to_node(self, location: Dict[str, Any]) -> ExamLocationNode:
        """
        Convert a SQL ExamLocation model to an ExamLocationNode.
        
        Args:
            location: SQL ExamLocation dictionary
            
        Returns:
            ExamLocationNode instance ready for Neo4j
        """
        try:
            # Create the exam location node
            location_node = ExamLocationNode(
                location_id=location["location_id"],
                location_name=location["location_name"],
                address=location["address"],
                capacity=location["capacity"],
                coordinates=None,  # Not in default model but available in Neo4j model
                status=location["is_active"],
                contact_info=location["contact_info"],
                additional_info=location["additional_info"]
            )
            
            return location_node
            
        except Exception as e:
            logger.error(f"Error converting exam location to node: {str(e)}")
            # Return a basic node with just the ID as fallback
            return ExamLocationNode(
                location_id=location["location_id"],
                location_name=location.get("location_name", f"Location {location['location_id']}")
            )
            
    async def sync_relationships(self, location_id: str) -> Dict[str, int]:
        """
        Synchronize relationships for a specific exam location.
        
        Args:
            location_id: ID of the exam location to synchronize relationships for
            
        Returns:
            Dictionary with counts of successfully synced relationships by type
        """
        logger.info(f"Synchronizing relationships for exam location {location_id}")
        
        relationship_counts = {
            "exams": 0,
            "rooms": 0
        }
        
        try:
            # Get exam location from SQL database with full details
            location = await self.exam_location_repository.get_by_id(location_id)
            if not location:
                logger.error(f"Exam location {location_id} not found in SQL database")
                return relationship_counts
            
            # Sync HAS_ROOM relationships (location-room)
            if "rooms" in location:
                for room in location["rooms"]:
                    room_id = room.get("room_id")
                    if room_id:
                        success = await self.exam_location_graph_repository.add_has_room_relationship(location_id, room_id)
                        if success:
                            relationship_counts["rooms"] += 1
            
            # Sync HOSTS_EXAM relationships (location-exam)
            if "exams" in location:
                for exam in location["exams"]:
                    exam_id = exam.get("exam_id")
                    if exam_id:
                        success = await self.exam_location_graph_repository.add_hosts_exam_relationship(location_id, exam_id)
                        if success:
                            relationship_counts["exams"] += 1
            
            logger.info(f"Exam location relationship synchronization completed for {location_id}")
            return relationship_counts
            
        except Exception as e:
            logger.error(f"Error synchronizing relationships for exam location {location_id}: {e}")
            return relationship_counts 