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
        sql_repository: Optional[ExamLocationRepository] = None,
        graph_repository: Optional[ExamLocationGraphRepository] = None
    ):
        """
        Initialize the ExamLocationSyncService.
        
        Args:
            session: SQLAlchemy async session
            driver: Neo4j async driver
            sql_repository: Optional ExamLocationRepository instance
            graph_repository: Optional ExamLocationGraphRepository instance
        """
        super().__init__(session, driver, sql_repository, graph_repository)
        self.session = session
        self.driver = driver
        self.sql_repository = sql_repository or ExamLocationRepository(session)
        self.graph_repository = graph_repository or ExamLocationGraphRepository(driver)
    
    async def sync_node_by_id(self, location_id: str) -> bool:
        """
        Synchronize a specific exam location node by ID, only creating the node and INSTANCE_OF relationship.
        
        Args:
            location_id: The ID of the exam location to sync
            
        Returns:
            True if sync was successful, False otherwise
        """
        logger.info(f"Synchronizing exam location node {location_id}")
        
        try:
            # Get exam location from SQL database
            location = await self.sql_repository.get_by_id(location_id)
            if not location:
                logger.error(f"Exam location {location_id} not found in SQL database")
                return False
            
            # Convert to Neo4j format
            neo4j_data = self._convert_to_node(location)
            
            # Create or update node in Neo4j
            result = await self.graph_repository.create_or_update(neo4j_data)
            
            logger.info(f"Successfully synchronized exam location node {location_id}")
            return result
            
        except Exception as e:
            logger.error(f"Error syncing exam location node {location_id}: {e}")
            return False
    
    async def sync_all_nodes(self, limit: Optional[int] = None) -> Tuple[int, int]:
        """
        Synchronize all exam location nodes, without their relationships (except INSTANCE_OF).
        
        Args:
            limit: Optional limit on number of exam locations to sync
            
        Returns:
            Tuple of (success_count, failed_count)
        """
        logger.info(f"Synchronizing all exam location nodes (limit={limit})")
        
        try:
            # Get all exam locations from SQL database
            locations, _ = await self.sql_repository.get_all(limit=limit)
            
            success_count = 0
            failed_count = 0
            
            for location in locations:
                try:
                    # Sync only the location node - handle both ORM objects and dictionaries
                    location_id = location.location_id if hasattr(location, 'location_id') else location.get("location_id")
                    if not location_id:
                        logger.error(f"Missing location_id in location object: {location}")
                        failed_count += 1
                        continue
                        
                    if await self.sync_node_by_id(location_id):
                        success_count += 1
                    else:
                        failed_count += 1
                except Exception as e:
                    # Get location_id safely for logging
                    location_id = getattr(location, 'location_id', None) if hasattr(location, 'location_id') else location.get("location_id", "unknown")
                    logger.error(f"Error syncing location node {location_id}: {e}")
                    failed_count += 1
            
            logger.info(f"Completed synchronizing exam location nodes: {success_count} successful, {failed_count} failed")
            return (success_count, failed_count)
            
        except Exception as e:
            logger.error(f"Error during exam location nodes synchronization: {e}")
            return (0, 0)
    
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
    
    async def sync_relationship_by_id(self, location_id: str) -> Dict[str, int]:
        """
        Synchronize relationships for a specific exam location.
        
        Args:
            location_id: ID of the exam location to synchronize relationships for
            
        Returns:
            Dictionary with counts of successfully synced relationships by type
        """
        logger.info(f"Synchronizing relationships for exam location {location_id}")
        
        # Check if exam location node exists before syncing relationships
        location_node = await self.graph_repository.get_by_id(location_id)
        if not location_node:
            logger.warning(f"Exam location node {location_id} not found in Neo4j, skipping relationship sync")
            return {
                "error": "Exam location node not found in Neo4j",
                "exams": 0,
                "rooms": 0
            }
        
        relationship_counts = {
            "exams": 0,
            "rooms": 0
        }
        
        try:
            # Get exam location from SQL database with full details
            location = await self.sql_repository.get_by_id(location_id)
            if not location:
                logger.error(f"Exam location {location_id} not found in SQL database")
                return relationship_counts
            
            # Sync HAS_ROOM relationships (location-room)
            if "rooms" in location:
                for room in location["rooms"]:
                    room_id = room.get("room_id")
                    if room_id:
                        success = await self.graph_repository.add_has_room_relationship(location_id, room_id)
                        if success:
                            relationship_counts["rooms"] += 1
            
            # Sync HOSTS_EXAM relationships (location-exam)
            if "exams" in location:
                for exam in location["exams"]:
                    exam_id = exam.get("exam_id")
                    if exam_id:
                        success = await self.graph_repository.add_hosts_exam_relationship(location_id, exam_id)
                        if success:
                            relationship_counts["exams"] += 1
            
            logger.info(f"Exam location relationship synchronization completed for {location_id}: {relationship_counts}")
            return relationship_counts
            
        except Exception as e:
            logger.error(f"Error synchronizing relationships for exam location {location_id}: {e}")
            return relationship_counts
    
    async def sync_all_relationships(self, limit: Optional[int] = None) -> Dict[str, int]:
        """
        Synchronize relationships for all exam locations.
        
        Args:
            limit: Optional maximum number of exam locations to process
            
        Returns:
            Dictionary with counts of synced relationships by type
        """
        logger.info(f"Synchronizing relationships for all exam locations (limit={limit})")
        
        try:
            # Get all exam locations from SQL database
            locations, total_count = await self.sql_repository.get_all(limit=limit)
            
            total_locations = len(locations)
            success_count = 0
            failure_count = 0
            
            # Aggregated counts for all relationship types
            relationship_counts = {
                "exams": 0,
                "rooms": 0
            }
            
            # For each exam location, sync relationships
            for location in locations:
                try:
                    # Get location_id safely - handle both ORM objects and dictionaries
                    location_id = location.location_id if hasattr(location, 'location_id') else location.get("location_id")
                    if not location_id:
                        logger.error(f"Missing location_id in location object: {location}")
                        failure_count += 1
                        continue
                    
                    # Verify exam location exists in Neo4j
                    location_node = await self.graph_repository.get_by_id(location_id)
                    if not location_node:
                        logger.warning(f"Exam location {location_id} not found in Neo4j, skipping relationship sync")
                        failure_count += 1
                        continue
                    
                    # Sync relationships for this exam location
                    results = await self.sync_relationship_by_id(location_id)
                    
                    # Update aggregated counts
                    for key, value in results.items():
                        if key in relationship_counts:
                            relationship_counts[key] += value
                    
                    success_count += 1
                    
                except Exception as e:
                    # Get location_id safely for logging
                    location_id = getattr(location, 'location_id', None) if hasattr(location, 'location_id') else location.get("location_id", "unknown")
                    logger.error(f"Error synchronizing relationships for exam location {location_id}: {e}")
                    failure_count += 1
            
            # Prepare final result
            result = {
                "total_locations": total_locations,
                "success": success_count,
                "failed": failure_count,
                "relationships": relationship_counts
            }
            
            logger.info(f"Completed synchronizing relationships for all exam locations: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error during exam location relationships synchronization: {e}")
            return {
                "total_locations": 0,
                "success": 0,
                "failed": 0,
                "error": str(e),
                "relationships": {}
            } 