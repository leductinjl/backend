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
        sql_repository: Optional[RecognitionRepository] = None,
        graph_repository: Optional[RecognitionGraphRepository] = None
    ):
        """
        Initialize the RecognitionSyncService.
        
        Args:
            session: SQLAlchemy async session
            driver: Neo4j async driver
            sql_repository: Optional RecognitionRepository instance
            graph_repository: Optional RecognitionGraphRepository instance
        """
        super().__init__(session, driver, sql_repository, graph_repository)
        self.db_session = session
        self.neo4j_driver = driver
        self.sql_repository = sql_repository or RecognitionRepository(session)
        self.graph_repository = graph_repository or RecognitionGraphRepository(driver)
    
    async def sync_node_by_id(self, recognition_id: str) -> bool:
        """
        Synchronize a specific recognition node by ID, only creating the node and INSTANCE_OF relationship.
        
        Args:
            recognition_id: The ID of the recognition to sync
            
        Returns:
            True if sync was successful, False otherwise
        """
        logger.info(f"Synchronizing recognition node {recognition_id}")
        
        try:
            # Get recognition from SQL database
            recognition = await self.sql_repository.get_by_id(recognition_id)
            if not recognition:
                logger.error(f"Recognition {recognition_id} not found in SQL database")
                return False
            
            # Convert to Neo4j format
            neo4j_data = self._convert_to_node(recognition)
            
            # Create or update node in Neo4j
            result = await self.graph_repository.create_or_update(neo4j_data)
            
            logger.info(f"Successfully synchronized recognition node {recognition_id}")
            return result
            
        except Exception as e:
            logger.error(f"Error syncing recognition node {recognition_id}: {e}")
            return False
    
    async def sync_all_nodes(self, limit: Optional[int] = None) -> Tuple[int, int]:
        """
        Synchronize all recognition nodes, without their relationships (except INSTANCE_OF).
        
        Args:
            limit: Optional limit on number of recognitions to sync
            
        Returns:
            Tuple of (success_count, failed_count)
        """
        logger.info(f"Synchronizing all recognition nodes (limit={limit})")
        
        try:
            # Get all recognitions from SQL database
            recognitions, _ = await self.sql_repository.get_all(limit=limit)
            
            success_count = 0
            failed_count = 0
            
            for recognition in recognitions:
                try:
                    # Sync only the recognition node - handle both ORM objects and dictionaries
                    recognition_id = recognition.recognition_id if hasattr(recognition, 'recognition_id') else recognition.get("recognition_id")
                    if not recognition_id:
                        logger.error(f"Missing recognition_id in recognition object: {recognition}")
                        failed_count += 1
                        continue
                        
                    if await self.sync_node_by_id(recognition_id):
                        success_count += 1
                    else:
                        failed_count += 1
                except Exception as e:
                    # Get recognition_id safely for logging
                    recognition_id = getattr(recognition, 'recognition_id', None) if hasattr(recognition, 'recognition_id') else recognition.get("recognition_id", "unknown")
                    logger.error(f"Error syncing recognition node {recognition_id}: {e}")
                    failed_count += 1
            
            logger.info(f"Completed synchronizing recognition nodes: {success_count} successful, {failed_count} failed")
            return (success_count, failed_count)
            
        except Exception as e:
            logger.error(f"Error during recognition nodes synchronization: {e}")
            return (0, 0)
    
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
            
    async def sync_relationship_by_id(self, recognition_id: str) -> Dict[str, int]:
        """
        Synchronize relationships for a specific recognition.
        
        Args:
            recognition_id: ID of the recognition to synchronize relationships for
            
        Returns:
            Dictionary with counts of successfully synced relationships by type
        """
        logger.info(f"Synchronizing relationships for recognition {recognition_id}")
        
        # Check if recognition node exists before syncing relationships
        recognition_node = await self.graph_repository.get_by_id(recognition_id)
        if not recognition_node:
            logger.warning(f"Recognition node {recognition_id} not found in Neo4j, skipping relationship sync")
            return {
                "error": "Recognition node not found in Neo4j",
                "candidate": 0,
                "award": 0,
                "organization": 0
            }
        
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
            
            logger.info(f"Recognition relationship synchronization completed for {recognition_id}: {relationship_counts}")
            return relationship_counts
            
        except Exception as e:
            logger.error(f"Error synchronizing relationships for recognition {recognition_id}: {e}")
            return relationship_counts
    
    async def sync_all_relationships(self, limit: Optional[int] = None) -> Dict[str, int]:
        """
        Synchronize relationships for all recognitions.
        
        Args:
            limit: Optional maximum number of recognitions to process
            
        Returns:
            Dictionary with counts of synced relationships by type
        """
        logger.info(f"Synchronizing relationships for all recognitions (limit={limit})")
        
        try:
            # Get all recognitions from SQL database
            recognitions, total_count = await self.sql_repository.get_all(limit=limit)
            
            total_recognitions = len(recognitions)
            success_count = 0
            failure_count = 0
            
            # Aggregated counts for all relationship types
            relationship_counts = {
                "candidate": 0,
                "award": 0,
                "organization": 0
            }
            
            # For each recognition, sync relationships
            for recognition in recognitions:
                try:
                    # Get recognition_id safely - handle both ORM objects and dictionaries
                    recognition_id = recognition.recognition_id if hasattr(recognition, 'recognition_id') else recognition.get("recognition_id")
                    if not recognition_id:
                        logger.error(f"Missing recognition_id in recognition object: {recognition}")
                        failure_count += 1
                        continue
                    
                    # Verify recognition exists in Neo4j
                    recognition_node = await self.graph_repository.get_by_id(recognition_id)
                    if not recognition_node:
                        logger.warning(f"Recognition {recognition_id} not found in Neo4j, skipping relationship sync")
                        failure_count += 1
                        continue
                    
                    # Sync relationships for this recognition
                    results = await self.sync_relationship_by_id(recognition_id)
                    
                    # Update aggregated counts
                    for key, value in results.items():
                        if key in relationship_counts:
                            relationship_counts[key] += value
                    
                    success_count += 1
                    
                except Exception as e:
                    # Get recognition_id safely for logging
                    recognition_id = getattr(recognition, 'recognition_id', None) if hasattr(recognition, 'recognition_id') else recognition.get("recognition_id", "unknown")
                    logger.error(f"Error synchronizing relationships for recognition {recognition_id}: {e}")
                    failure_count += 1
            
            # Prepare final result
            result = {
                "total_recognitions": total_recognitions,
                "success": success_count,
                "failed": failure_count,
                "relationships": relationship_counts
            }
            
            logger.info(f"Completed synchronizing relationships for all recognitions: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error during recognition relationships synchronization: {e}")
            return {
                "total_recognitions": 0,
                "success": 0,
                "failed": 0,
                "error": str(e),
                "relationships": {}
            } 