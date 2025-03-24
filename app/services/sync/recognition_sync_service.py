"""
Recognition Sync Service Module.

This module provides the RecognitionSyncService class for synchronizing Recognition
data between PostgreSQL and Neo4j.
"""

import logging
from typing import Optional, Tuple, List, Dict, Any, Union

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
    
    async def sync_by_id(self, recognition_id: str, skip_relationships: bool = False) -> bool:
        """
        Synchronize a specific recognition by ID.
        
        Args:
            recognition_id: The ID of the recognition to sync
            skip_relationships: If True, only sync node without its relationships
            
        Returns:
            True if sync was successful, False otherwise
        """
        logger.info(f"Synchronizing recognition {recognition_id} (skip_relationships={skip_relationships})")
        
        try:
            # Get recognition from SQL database
            recognition = await self.sql_repository.get_by_id(recognition_id)
            if not recognition:
                logger.error(f"Recognition {recognition_id} not found in SQL database")
                return False
            
            # Convert to Neo4j format
            neo4j_data = self._convert_to_node(recognition)
            
            # Create or update node in Neo4j
            await self.graph_repository.create_or_update(neo4j_data)
            
            # Sync relationships if needed
            if not skip_relationships:
                await self.sync_relationships(recognition_id)
            
            return True
            
        except Exception as e:
            logger.error(f"Error syncing recognition {recognition_id}: {e}")
            return False
    
    async def sync_all(self, limit: Optional[int] = None, skip_relationships: bool = False) -> Union[Tuple[int, int], Dict[str, int]]:
        """
        Synchronize all recognitions.
        
        Args:
            limit: Optional limit on number of recognitions to sync
            skip_relationships: If True, only sync nodes without their relationships
            
        Returns:
            Tuple of (success_count, failed_count) or dict with success/failed counts
        """
        logger.info(f"Synchronizing all recognitions (skip_relationships={skip_relationships})")
        
        try:
            # Get all recognitions from SQL database
            recognitions, _ = await self.sql_repository.get_all(limit=limit)
            
            success_count = 0
            failed_count = 0
            
            for recognition in recognitions:
                try:
                    # Sync the recognition node - handle both ORM objects and dictionaries
                    recognition_id = recognition.recognition_id if hasattr(recognition, 'recognition_id') else recognition.get("recognition_id")
                    if not recognition_id:
                        logger.error(f"Missing recognition_id in recognition object: {recognition}")
                        failed_count += 1
                        continue
                        
                    await self.sync_by_id(recognition_id, skip_relationships=skip_relationships)
                    success_count += 1
                except Exception as e:
                    # Get recognition_id safely for logging
                    recognition_id = getattr(recognition, 'recognition_id', None) if hasattr(recognition, 'recognition_id') else recognition.get("recognition_id", "unknown")
                    logger.error(f"Error syncing recognition {recognition_id}: {e}")
                    failed_count += 1
            
            return (success_count, failed_count)
            
        except Exception as e:
            logger.error(f"Error during recognition synchronization: {e}")
            return {"success": 0, "failed": 0}
    
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
            
    async def sync_relationships(self, recognition_id: str) -> Dict[str, int]:
        """
        Synchronize relationships for a specific recognition.
        
        Args:
            recognition_id: ID of the recognition to synchronize relationships for
            
        Returns:
            Dictionary with counts of successfully synced relationships by type
        """
        logger.info(f"Synchronizing relationships for recognition {recognition_id}")
        
        relationship_counts = {
            "candidate": 0,
            "award": 0,
            "organization": 0
        }
        
        try:
            # Get recognition from SQL database with full details
            recognition = await self.sql_repository.get_by_id(recognition_id)
            if not recognition:
                logger.error(f"Recognition {recognition_id} not found in SQL database")
                return relationship_counts
            
            # Extract candidate_id if available
            candidate_id = getattr(recognition, 'candidate_id', None)
            
            # Sync RECEIVED_BY relationship (recognition-candidate)
            if candidate_id:
                success = await self.graph_repository.add_received_by_relationship(recognition_id, candidate_id)
                if success:
                    relationship_counts["candidate"] += 1
            
            # Extract award_id if available
            award_id = getattr(recognition, 'award_id', None)
            
            # Sync FOR_AWARD relationship (recognition-award)
            if award_id:
                success = await self.graph_repository.add_for_award_relationship(recognition_id, award_id)
                if success:
                    relationship_counts["award"] += 1
            
            # Extract issuing_organization if available
            issuing_org = getattr(recognition, 'issuing_organization', None)
            if issuing_org:
                # In a real implementation, we would add relationship to organization
                # This is a placeholder for future implementation
                relationship_counts["organization"] += 0
            
            logger.info(f"Recognition relationship synchronization completed for {recognition_id}")
            return relationship_counts
            
        except Exception as e:
            logger.error(f"Error synchronizing relationships for recognition {recognition_id}: {e}")
            return relationship_counts 