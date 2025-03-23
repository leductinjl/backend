"""
Major Sync Service Module.

This module provides the MajorSyncService class for synchronizing Major
data between PostgreSQL and Neo4j.
"""

import logging
from typing import Optional, Tuple, List, Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession
from neo4j import AsyncDriver

from app.domain.models.major import Major
from app.domain.graph_models.major_node import MajorNode
from app.repositories.major_repository import MajorRepository
from app.graph_repositories.major_graph_repository import MajorGraphRepository
from app.services.sync.base_sync_service import BaseSyncService

logger = logging.getLogger(__name__)

class MajorSyncService(BaseSyncService):
    """
    Service for synchronizing Major data between PostgreSQL and Neo4j.
    
    This service implements the BaseSyncService abstract class and provides
    methods for synchronizing individual majors by ID and synchronizing
    all majors in the database.
    """
    
    def __init__(
        self,
        session: AsyncSession,
        driver: AsyncDriver,
        major_repository: Optional[MajorRepository] = None,
        major_graph_repository: Optional[MajorGraphRepository] = None
    ):
        """
        Initialize the MajorSyncService.
        
        Args:
            session: SQLAlchemy async session
            driver: Neo4j async driver
            major_repository: Optional MajorRepository instance
            major_graph_repository: Optional MajorGraphRepository instance
        """
        self.db_session = session
        self.neo4j_driver = driver
        self.sql_repository = major_repository or MajorRepository(session)
        self.graph_repository = major_graph_repository or MajorGraphRepository(driver)
    
    async def sync_by_id(self, major_id: str) -> bool:
        """
        Synchronize a single major by ID.
        
        Args:
            major_id: ID of the major to synchronize
            
        Returns:
            True if synchronization was successful, False otherwise
        """
        try:
            # Get major from SQL database
            major = await self.sql_repository.get_by_id(major_id)
            if not major:
                logger.warning(f"Major with ID {major_id} not found in SQL database")
                return False
            
            # Convert to Neo4j node and save
            major_node = self._convert_to_node(major)
            result = await self.graph_repository.create_or_update(major_node)
            
            if result:
                logger.info(f"Successfully synchronized major {major_id}")
                return True
            else:
                logger.error(f"Failed to synchronize major {major_id}")
                return False
            
        except Exception as e:
            logger.error(f"Error synchronizing major {major_id}: {str(e)}")
            return False
    
    async def sync_all(self, limit: Optional[int] = None, offset: int = 0) -> Tuple[int, int]:
        """
        Synchronize all majors from PostgreSQL to Neo4j.
        
        Args:
            limit: Optional maximum number of majors to synchronize
            offset: Optional offset for pagination
            
        Returns:
            Tuple containing counts of (successful, failed) synchronizations
        """
        success_count = 0
        failure_count = 0
        
        try:
            # Get all majors from SQL database
            majors, total = await self.sql_repository.get_all(skip=offset, limit=limit or 100)
            
            logger.info(f"Found {total} majors to synchronize")
            
            # Synchronize each major
            for major in majors:
                if await self.sync_by_id(major.major_id):
                    success_count += 1
                else:
                    failure_count += 1
                    
            logger.info(f"Major synchronization complete. Success: {success_count}, Failed: {failure_count}")
            
        except Exception as e:
            logger.error(f"Error during major synchronization: {str(e)}")
        
        return success_count, failure_count
    
    def _convert_to_node(self, major: Major) -> MajorNode:
        """
        Convert a SQL Major model to a MajorNode.
        
        Args:
            major: SQL Major model instance
            
        Returns:
            MajorNode instance ready for Neo4j
        """
        try:
            # Create the major node
            major_node = MajorNode.from_sql_model(major)
            return major_node
            
        except Exception as e:
            logger.error(f"Error converting major to node: {str(e)}")
            # Return a basic node with just the ID as fallback
            return MajorNode(
                major_id=major.major_id,
                major_name=major.major_name
            ) 