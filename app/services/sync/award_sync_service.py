"""
Award Sync Service Module.

This module provides the AwardSyncService class for synchronizing Award
data between PostgreSQL and Neo4j.
"""

import logging
from typing import Optional, Tuple, List

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
    
    async def sync_by_id(self, award_id: str) -> bool:
        """
        Synchronize a single award by ID.
        
        Args:
            award_id: ID of the award to synchronize
            
        Returns:
            True if synchronization was successful, False otherwise
        """
        try:
            # Get award from SQL database
            award = await self.award_repository.get_by_id(award_id)
            if not award:
                logger.warning(f"Award with ID {award_id} not found in SQL database")
                return False
            
            # Convert to Neo4j node and save
            award_node = self._convert_to_node(award)
            await self.award_graph_repository.create_or_update(award_node)
            
            logger.info(f"Successfully synchronized award {award_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error synchronizing award {award_id}: {str(e)}")
            return False
    
    async def sync_all(self, limit: Optional[int] = None, offset: int = 0) -> Tuple[int, int]:
        """
        Synchronize all awards from PostgreSQL to Neo4j.
        
        Args:
            limit: Optional maximum number of awards to synchronize
            offset: Optional offset for pagination
            
        Returns:
            Tuple containing counts of (successful, failed) synchronizations
        """
        success_count = 0
        failure_count = 0
        
        try:
            # Get all awards from SQL database
            query = select(Award)
            if limit:
                query = query.limit(limit)
            if offset:
                query = query.offset(offset)
                
            result = await self.session.execute(query)
            awards = result.scalars().all()
            
            total_count = len(awards)
            logger.info(f"Found {total_count} awards to synchronize")
            
            # Synchronize each award
            for award in awards:
                if await self.sync_by_id(award.award_id):
                    success_count += 1
                else:
                    failure_count += 1
                    
            logger.info(f"Award synchronization complete. Success: {success_count}, Failed: {failure_count}")
            
        except Exception as e:
            logger.error(f"Error during award synchronization: {str(e)}")
        
        return success_count, failure_count
    
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