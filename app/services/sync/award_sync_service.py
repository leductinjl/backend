"""
Award Sync Service Module.

This module provides the AwardSyncService class for synchronizing Award
data between PostgreSQL and Neo4j.
"""

import logging
from typing import Optional, Tuple, List, Union, Dict

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from neo4j import AsyncDriver

from app.domain.models.award import Award
from app.domain.graph_models.award_node import AwardNode
from app.repositories.award_repository import AwardRepository
from app.graph_repositories.award_graph_repository import AwardGraphRepository
from app.services.sync.base_sync_service import BaseSyncService

logger = logging.getLogger(__name__)

class AwardSyncService(BaseSyncService):
    """
    Service for synchronizing Award data between PostgreSQL and Neo4j.
    
    This service implements the BaseSyncService abstract class and provides
    methods for synchronizing individual awards by ID and synchronizing
    all awards in the database.
    """
    
    def __init__(
        self,
        session: AsyncSession,
        driver: AsyncDriver,
        award_repository: Optional[AwardRepository] = None,
        award_graph_repository: Optional[AwardGraphRepository] = None
    ):
        """
        Initialize the AwardSyncService.
        
        Args:
            session: SQLAlchemy async session
            driver: Neo4j async driver
            award_repository: Optional AwardRepository instance
            award_graph_repository: Optional AwardGraphRepository instance
        """
        self.session = session
        self.driver = driver
        self.award_repository = award_repository or AwardRepository(session)
        self.award_graph_repository = award_graph_repository or AwardGraphRepository(driver)
    
    async def sync_by_id(self, award_id: str, skip_relationships: bool = False) -> bool:
        """
        Synchronize a specific award by ID.
        
        Args:
            award_id: The ID of the award to sync
            skip_relationships: If True, only sync node without its relationships
            
        Returns:
            True if sync was successful, False otherwise
        """
        logger.info(f"Synchronizing award {award_id} (skip_relationships={skip_relationships})")
        
        try:
            # Get award from SQL database
            award = await self.award_repository.get_by_id(award_id)
            if not award:
                logger.error(f"Award {award_id} not found in SQL database")
                return False
            
            # Convert to Neo4j format
            neo4j_data = self._convert_to_node(award)
            
            # Create or update node in Neo4j
            await self.award_graph_repository.create_or_update(neo4j_data)
            
            # Sync relationships if needed
            if not skip_relationships:
                await self.sync_relationships(award_id)
            
            return True
            
        except Exception as e:
            logger.error(f"Error syncing award {award_id}: {e}")
            return False
    
    async def sync_all(self, limit: Optional[int] = None, skip_relationships: bool = False) -> Union[Tuple[int, int], Dict[str, int]]:
        """
        Synchronize all awards.
        
        Args:
            limit: Optional limit on number of awards to sync
            skip_relationships: If True, only sync nodes without their relationships
            
        Returns:
            Tuple of (success_count, failed_count) or dict with success/failed counts
        """
        logger.info(f"Synchronizing all awards (skip_relationships={skip_relationships})")
        
        try:
            # Get all awards from SQL database
            query = select(Award)
            if limit:
                query = query.limit(limit)
                
            result = await self.session.execute(query)
            awards = result.scalars().all()
            
            success_count = 0
            failed_count = 0
            
            for award in awards:
                try:
                    # Sync the award node - handle both ORM objects and dictionaries
                    award_id = award.award_id if hasattr(award, 'award_id') else award.get("award_id")
                    if not award_id:
                        logger.error(f"Missing award_id in award object: {award}")
                        failed_count += 1
                        continue
                        
                    await self.sync_by_id(award_id, skip_relationships=skip_relationships)
                    success_count += 1
                except Exception as e:
                    # Get award_id safely for logging
                    award_id = getattr(award, 'award_id', None) if hasattr(award, 'award_id') else award.get("award_id", "unknown")
                    logger.error(f"Error syncing award {award_id}: {e}")
                    failed_count += 1
            
            return (success_count, failed_count)
            
        except Exception as e:
            logger.error(f"Error during award synchronization: {e}")
            return {"success": 0, "failed": 0}
    
    def _convert_to_node(self, award: Award) -> AwardNode:
        """
        Convert a SQL Award model to an AwardNode.
        
        Args:
            award: SQL Award model instance
            
        Returns:
            AwardNode instance ready for Neo4j
        """
        # Create the Neo4j node from the SQL model
        award_node = AwardNode.from_sql_model(award)
        return award_node
        
    async def sync_relationships(self, award_id: str) -> Dict[str, int]:
        """
        Synchronize relationships for a specific award.
        
        Args:
            award_id: ID of the award to synchronize relationships for
            
        Returns:
            Dictionary with counts of successfully synced relationships by type
        """
        logger.info(f"Synchronizing relationships for award {award_id}")
        
        relationship_counts = {
            "candidate": 0,
            "exam": 0,
            "organization": 0
        }
        
        try:
            # Get award from SQL database with full details
            award = await self.award_repository.get_by_id(award_id)
            if not award:
                logger.error(f"Award {award_id} not found in SQL database")
                return relationship_counts
            
            # Extract candidate_id if available
            candidate_id = getattr(award, 'candidate_id', None)
            
            # Sync AWARDED_TO relationship (award-candidate)
            if candidate_id:
                success = await self.award_graph_repository.add_awarded_to_relationship(award_id, candidate_id)
                if success:
                    relationship_counts["candidate"] += 1
            
            # Extract issuing_organization if available
            issuing_org = getattr(award, 'issuing_organization', None)
            if issuing_org:
                # In a real implementation, we would add relationship to organization
                # This is a placeholder for future implementation
                relationship_counts["organization"] += 0
            
            logger.info(f"Award relationship synchronization completed for {award_id}")
            return relationship_counts
            
        except Exception as e:
            logger.error(f"Error synchronizing relationships for award {award_id}: {e}")
            return relationship_counts 