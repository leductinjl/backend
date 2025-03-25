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
                
            # Add detailed logging for debugging
            logger.info(f"Location data keys: {list(location.keys()) if location else []}")
            
            # Verify location node in Neo4j
            # If it doesn't exist, create it first
            location_node = await self.graph_repository.get_by_id(location_id)
            if not location_node:
                logger.warning(f"Exam location node {location_id} not found in Neo4j, creating it first")
                await self.sync_node_by_id(location_id)
            
            # Sync HOSTS_EXAM relationships (location-exam)
            exams = location.get("exams", [])
            if exams:
                logger.info(f"Found {len(exams)} exams for location {location_id}")
                for exam in exams:
                    # Extract exam_id safely
                    exam_id = None
                    if isinstance(exam, dict):
                        exam_id = exam.get("exam_id")
                    else:
                        # Handle if exam is a SQLAlchemy model
                        exam_id = getattr(exam, "exam_id", None)
                        
                    if exam_id:
                        try:
                            success = await self.graph_repository.add_hosts_exam_relationship(location_id, exam_id)
                            if success:
                                relationship_counts["exams"] += 1
                                logger.info(f"Added HOSTS_EXAM relationship between {location_id} and {exam_id}")
                        except Exception as exam_e:
                            logger.error(f"Error adding HOSTS_EXAM relationship: {exam_e}")
                    else:
                        logger.warning(f"Could not extract exam_id from exam data: {exam}")
            else:
                logger.warning(f"No exams found for location {location_id}")
            
            # Sync HAS_ROOM relationships (location-room)
            rooms = location.get("exam_rooms", []) or location.get("rooms", [])
            if rooms:
                logger.info(f"Found {len(rooms)} rooms for location {location_id}")
                for room in rooms:
                    # Extract room_id safely
                    room_id = None
                    if isinstance(room, dict):
                        room_id = room.get("room_id")
                    else:
                        # Handle if room is a SQLAlchemy model
                        room_id = getattr(room, "room_id", None)
                        
                    if room_id:
                        try:
                            success = await self.graph_repository.add_has_room_relationship(location_id, room_id)
                            if success:
                                relationship_counts["rooms"] += 1
                                logger.info(f"Added HAS_ROOM relationship between {location_id} and {room_id}")
                        except Exception as room_e:
                            logger.error(f"Error adding HAS_ROOM relationship: {room_e}")
                    else:
                        logger.warning(f"Could not extract room_id from room data: {room}")
            else:
                logger.info(f"No rooms found for location {location_id}")
            
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
            
            # Debug: print first location to understand structure
            if locations and len(locations) > 0:
                first_location = locations[0]
                logger.info(f"DEBUG: First location type: {type(first_location)}")
                logger.info(f"DEBUG: First location attributes: {dir(first_location) if hasattr(first_location, '__dict__') else 'No attributes'}")
                logger.info(f"DEBUG: First location dictionary keys: {list(first_location.keys()) if isinstance(first_location, dict) else 'Not a dictionary'}")
                
                # Attempt to safely extract and display the location_id
                if hasattr(first_location, 'location_id'):
                    logger.info(f"DEBUG: First location has location_id attribute: {first_location.location_id}")
                elif isinstance(first_location, dict) and 'location_id' in first_location:
                    logger.info(f"DEBUG: First location has location_id key: {first_location['location_id']}")
                else:
                    logger.info(f"DEBUG: First location object dump: {first_location}")
            
            # For each exam location, sync relationships
            for location in locations:
                try:
                    # Debug: Print current location before accessing attributes
                    logger.info(f"Processing location: {location}")
                    
                    # Get location_id safely - handle both ORM objects and dictionaries
                    location_id = None
                    
                    # Try multiple approaches to get location_id
                    if hasattr(location, 'location_id'):
                        location_id = location.location_id
                        logger.info(f"Found location_id as attribute: {location_id}")
                    elif isinstance(location, dict):
                        if 'location_id' in location:
                            location_id = location['location_id']
                            logger.info(f"Found location_id as dictionary key: {location_id}")
                        else:
                            logger.info(f"Dictionary keys available: {list(location.keys())}")
                    else:
                        logger.info(f"Location object is neither ORM nor dictionary: {type(location)}")
                    
                    if not location_id:
                        logger.error(f"Missing location_id in location object: {location}")
                        failure_count += 1
                        continue
                    
                    # First ensure node exists in Neo4j - if not, create it
                    location_node = await self.graph_repository.get_by_id(location_id)
                    if not location_node:
                        logger.info(f"Creating exam location node in Neo4j for {location_id}")
                        node_created = await self.sync_node_by_id(location_id)
                        if not node_created:
                            logger.error(f"Failed to create exam location node for {location_id}, skipping relationship sync")
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
                    location_id = "unknown"
                    if hasattr(location, 'location_id'):
                        location_id = location.location_id
                    elif isinstance(location, dict) and 'location_id' in location:
                        location_id = location['location_id']
                        
                    logger.error(f"Error synchronizing relationships for exam location {location_id}: {e}")
                    logger.exception("Full exception details")
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