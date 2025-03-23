"""
Recognition Sync Service Module.

This module provides the RecognitionSyncService class for synchronizing Recognition
data between PostgreSQL and Neo4j.
"""

import logging
from typing import Optional, Tuple, List, Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession
from neo4j import AsyncDriver

from app.domain.models.recognition import Recognition
from app.domain.graph_models.recognition_node import RecognitionNode
from app.repositories.recognition_repository import RecognitionRepository
from app.graph_repositories.recognition_graph_repository import RecognitionGraphRepository
from app.services.sync.base_sync_service import BaseSyncService

logger = logging.getLogger(__name__)

class RecognitionSyncService(BaseSyncService):
    """
    Service for synchronizing Recognition data between PostgreSQL and Neo4j.
    
    This service implements the BaseSyncService abstract class and provides
    methods for synchronizing individual recognitions by ID and synchronizing
    all recognitions in the database.
    """
    
    def __init__(
        self,
        session: AsyncSession,
        driver: AsyncDriver,
        recognition_repository: Optional[RecognitionRepository] = None,
        recognition_graph_repository: Optional[RecognitionGraphRepository] = None
    ):
        """
        Initialize the RecognitionSyncService.
        
        Args:
            session: SQLAlchemy async session
            driver: Neo4j async driver
            recognition_repository: Optional RecognitionRepository instance
            recognition_graph_repository: Optional RecognitionGraphRepository instance
        """
        self.db_session = session
        self.neo4j_driver = driver
        self.sql_repository = recognition_repository or RecognitionRepository(session)
        self.graph_repository = recognition_graph_repository or RecognitionGraphRepository(driver)
    
    async def sync_by_id(self, recognition_id: str) -> bool:
        """
        Synchronize a single recognition by ID.
        
        Args:
            recognition_id: ID of the recognition to synchronize
            
        Returns:
            True if synchronization was successful, False otherwise
        """
        try:
            # Get recognition from SQL database
            recognition = await self.sql_repository.get_by_id(recognition_id)
            if not recognition:
                logger.warning(f"Recognition with ID {recognition_id} not found in SQL database")
                return False
            
            # Convert to Neo4j node and save
            recognition_node = self._convert_to_node(recognition)
            result = await self.graph_repository.create_or_update(recognition_node)
            
            if result:
                logger.info(f"Successfully synchronized recognition {recognition_id}")
                return True
            else:
                logger.error(f"Failed to synchronize recognition {recognition_id}")
                return False
            
        except Exception as e:
            logger.error(f"Error synchronizing recognition {recognition_id}: {str(e)}")
            return False
    
    async def sync_all(self, limit: Optional[int] = None, offset: int = 0) -> Tuple[int, int]:
        """
        Synchronize all recognitions from PostgreSQL to Neo4j.
        
        Args:
            limit: Optional maximum number of recognitions to synchronize
            offset: Optional offset for pagination
            
        Returns:
            Tuple containing counts of (successful, failed) synchronizations
        """
        success_count = 0
        failure_count = 0
        
        try:
            # Get all recognitions from SQL database
            recognitions, total = await self.sql_repository.get_all(skip=offset, limit=limit or 100)
            
            logger.info(f"Found {total} recognitions to synchronize")
            
            # Synchronize each recognition
            for recognition in recognitions:
                if await self.sync_by_id(recognition.recognition_id):
                    success_count += 1
                else:
                    failure_count += 1
                    
            logger.info(f"Recognition synchronization complete. Success: {success_count}, Failed: {failure_count}")
            
        except Exception as e:
            logger.error(f"Error during recognition synchronization: {str(e)}")
        
        return success_count, failure_count
    
    def _convert_to_node(self, recognition: Recognition) -> RecognitionNode:
        """
        Convert a SQL Recognition model to a RecognitionNode.
        
        Args:
            recognition: SQL Recognition model instance
            
        Returns:
            RecognitionNode instance ready for Neo4j
        """
        try:
            # Create the recognition node
            recognition_node = RecognitionNode.from_sql_model(recognition)
            return recognition_node
            
        except Exception as e:
            logger.error(f"Error converting recognition to node: {str(e)}")
            # Return a basic node with just the ID as fallback
            recognition_name = getattr(recognition, 'title', f"Recognition {recognition.recognition_id}")
            return RecognitionNode(
                recognition_id=recognition.recognition_id,
                recognition_name=recognition_name
            ) 