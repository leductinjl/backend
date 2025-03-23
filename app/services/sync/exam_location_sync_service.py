"""
Exam Location Sync Service Module.

This module provides the ExamLocationSyncService class for synchronizing ExamLocation
data between PostgreSQL and Neo4j.
"""

import logging
from typing import Optional, Tuple, List, Dict, Any

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
    
    async def sync_by_id(self, location_id: str) -> bool:
        """
        Synchronize a single exam location by ID.
        
        Args:
            location_id: ID of the exam location to synchronize
            
        Returns:
            True if synchronization was successful, False otherwise
        """
        try:
            # Get exam location from SQL database with details
            location = await self.exam_location_repository.get_by_id(location_id)
            if not location:
                logger.warning(f"Exam Location with ID {location_id} not found in SQL database")
                return False
            
            # Convert to Neo4j node and save
            location_node = self._convert_to_node(location)
            result = await self.exam_location_graph_repository.create_or_update(location_node)
            
            if result:
                logger.info(f"Successfully synchronized exam location {location_id}")
                return True
            else:
                logger.error(f"Failed to synchronize exam location {location_id}")
                return False
            
        except Exception as e:
            logger.error(f"Error synchronizing exam location {location_id}: {str(e)}")
            return False
    
    async def sync_all(self, limit: Optional[int] = None, offset: int = 0) -> Tuple[int, int]:
        """
        Synchronize all exam locations from PostgreSQL to Neo4j.
        
        Args:
            limit: Optional maximum number of exam locations to synchronize
            offset: Optional offset for pagination
            
        Returns:
            Tuple containing counts of (successful, failed) synchronizations
        """
        success_count = 0
        failure_count = 0
        
        try:
            # Get all exam locations from SQL database with details
            locations, total = await self.exam_location_repository.get_all(skip=offset, limit=limit or 100)
            
            logger.info(f"Found {total} exam locations to synchronize")
            
            # Synchronize each exam location
            for location in locations:
                location_id = location.get("location_id")
                if await self.sync_by_id(location_id):
                    success_count += 1
                else:
                    failure_count += 1
                    
            logger.info(f"Exam Location synchronization complete. Success: {success_count}, Failed: {failure_count}")
            
        except Exception as e:
            logger.error(f"Error during exam location synchronization: {str(e)}")
        
        return success_count, failure_count
    
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