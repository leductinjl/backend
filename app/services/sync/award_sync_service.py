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
        sql_repository: Optional[AwardRepository] = None,
        graph_repository: Optional[AwardGraphRepository] = None
    ):
        """
        Initialize the AwardSyncService.
        
        Args:
            session: SQLAlchemy async session
            driver: Neo4j async driver
            sql_repository: Optional AwardRepository instance
            graph_repository: Optional AwardGraphRepository instance
        """
        super().__init__(session, driver, sql_repository, graph_repository)
        self.session = session
        self.driver = driver
        self.sql_repository = sql_repository or AwardRepository(session)
        self.graph_repository = graph_repository or AwardGraphRepository(driver)
    
    async def sync_node_by_id(self, award_id: str) -> bool:
        """
        Synchronize a specific award node by ID, only creating the node and INSTANCE_OF relationship.
        
        Args:
            award_id: The ID of the award to sync
            
        Returns:
            True if sync was successful, False otherwise
        """
        logger.info(f"Synchronizing award node {award_id}")
        
        try:
            # Get award from SQL database
            award = await self.sql_repository.get_by_id(award_id)
            if not award:
                logger.error(f"Award {award_id} not found in SQL database")
                return False
            
            # Convert to Neo4j format
            neo4j_data = self._convert_to_node(award)
            
            # Create or update node in Neo4j
            result = await self.graph_repository.create_or_update(neo4j_data)
            
            logger.info(f"Successfully synchronized award node {award_id}")
            return result
            
        except Exception as e:
            logger.error(f"Error syncing award node {award_id}: {e}")
            return False
    
    async def sync_all_nodes(self, limit: Optional[int] = None) -> Tuple[int, int]:
        """
        Synchronize all award nodes, without their relationships (except INSTANCE_OF).
        
        Args:
            limit: Optional limit on number of awards to sync
            
        Returns:
            Tuple of (success_count, failed_count)
        """
        logger.info(f"Synchronizing all award nodes (limit={limit})")
        
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
                    # Sync only the award node - handle both ORM objects and dictionaries
                    award_id = award.award_id if hasattr(award, 'award_id') else award.get("award_id")
                    if not award_id:
                        logger.error(f"Missing award_id in award object: {award}")
                        failed_count += 1
                        continue
                        
                    if await self.sync_node_by_id(award_id):
                        success_count += 1
                    else:
                        failed_count += 1
                except Exception as e:
                    # Get award_id safely for logging
                    award_id = getattr(award, 'award_id', None) if hasattr(award, 'award_id') else award.get("award_id", "unknown")
                    logger.error(f"Error syncing award node {award_id}: {e}")
                    failed_count += 1
            
            logger.info(f"Completed synchronizing award nodes: {success_count} successful, {failed_count} failed")
            return (success_count, failed_count)
            
        except Exception as e:
            logger.error(f"Error during award nodes synchronization: {e}")
            return (0, 0)
    
    def _convert_to_node(self, award: Award) -> AwardNode:
        """
        Convert a SQL Award model to an AwardNode.
        
        Args:
            award: SQL Award model instance
            
        Returns:
            AwardNode instance ready for Neo4j
        """
        # Tạo award_name từ achievement hoặc award_type nếu không có award_name
        award_name = getattr(award, 'award_name', None)
        if not award_name:
            if hasattr(award, 'achievement') and award.achievement:
                award_name = award.achievement
            elif hasattr(award, 'award_type') and award.award_type:
                award_name = award.award_type
            else:
                award_name = f"Award {award.award_id}"
                
        # Tạo AwardNode trực tiếp với chỉ thuộc tính node, không có thông tin relationship
        return AwardNode(
            award_id=award.award_id,
            award_name=award_name,
            award_type=getattr(award, 'award_type', None),
            award_date=getattr(award, 'award_date', None),
            description=getattr(award, 'achievement', None),
            award_image_url=getattr(award, 'certificate_image_url', None),
            additional_info=getattr(award, 'additional_info', None)
        )
        
    async def sync_relationship_by_id(self, award_id: str) -> Dict[str, int]:
        """
        Synchronize relationships for a specific award.
        
        Args:
            award_id: ID of the award to synchronize relationships for
            
        Returns:
            Dictionary with counts of successfully synced relationships by type
        """
        logger.info(f"Synchronizing relationships for award {award_id}")
        
        # Check if award node exists before syncing relationships
        award_node = await self.graph_repository.get_by_id(award_id)
        if not award_node:
            logger.warning(f"Award node {award_id} not found in Neo4j, skipping relationship sync")
            return {
                "error": "Award node not found in Neo4j",
                "candidate": 0,
                "exam": 0,
                "organization": 0
            }
        
        relationship_counts = {
            "candidate": 0,
            "exam": 0,
            "organization": 0
        }
        
        try:
            # Get award from SQL database with full details
            award = await self.sql_repository.get_by_id(award_id)
            if not award:
                logger.error(f"Award {award_id} not found in SQL database")
                return relationship_counts
            
            # Extract candidate_id if available
            candidate_id = getattr(award, 'candidate_id', None)
            
            # Sync AWARDED_TO relationship (award-candidate)
            if candidate_id:
                success = await self.graph_repository.add_awarded_to_relationship(award_id, candidate_id)
                if success:
                    relationship_counts["candidate"] += 1
            
            # Extract issuing_organization if available
            issuing_org = getattr(award, 'issuing_organization', None)
            if issuing_org:
                # In a real implementation, we would add relationship to organization
                # This is a placeholder for future implementation
                relationship_counts["organization"] += 0
            
            logger.info(f"Award relationship synchronization completed for {award_id}: {relationship_counts}")
            return relationship_counts
            
        except Exception as e:
            logger.error(f"Error synchronizing relationships for award {award_id}: {e}")
            return relationship_counts
            
    async def sync_all_relationships(self, limit: Optional[int] = None) -> Dict[str, int]:
        """
        Synchronize relationships for all awards.
        
        Args:
            limit: Optional maximum number of awards to process
            
        Returns:
            Dictionary with counts of synced relationships by type
        """
        logger.info(f"Synchronizing relationships for all awards (limit={limit})")
        
        try:
            # Get all awards from SQL database
            query = select(Award)
            if limit:
                query = query.limit(limit)
                
            result = await self.session.execute(query)
            awards = result.scalars().all()
            
            total_awards = len(awards)
            success_count = 0
            failure_count = 0
            
            # Aggregated counts for all relationship types
            relationship_counts = {
                "candidate": 0,
                "exam": 0,
                "organization": 0
            }
            
            # For each award, sync relationships
            for award in awards:
                try:
                    # Get award_id safely - handle both ORM objects and dictionaries
                    award_id = award.award_id if hasattr(award, 'award_id') else award.get("award_id")
                    if not award_id:
                        logger.error(f"Missing award_id in award object: {award}")
                        failure_count += 1
                        continue
                    
                    # Verify award exists in Neo4j
                    award_node = await self.graph_repository.get_by_id(award_id)
                    if not award_node:
                        logger.warning(f"Award {award_id} not found in Neo4j, skipping relationship sync")
                        failure_count += 1
                        continue
                    
                    # Sync relationships for this award
                    results = await self.sync_relationship_by_id(award_id)
                    
                    # Update aggregated counts
                    for key, value in results.items():
                        if key in relationship_counts:
                            relationship_counts[key] += value
                    
                    success_count += 1
                    
                except Exception as e:
                    # Get award_id safely for logging
                    award_id = getattr(award, 'award_id', None) if hasattr(award, 'award_id') else award.get("award_id", "unknown")
                    logger.error(f"Error synchronizing relationships for award {award_id}: {e}")
                    failure_count += 1
            
            # Prepare final result
            result = {
                "total_awards": total_awards,
                "success": success_count,
                "failed": failure_count,
                "relationships": relationship_counts
            }
            
            logger.info(f"Completed synchronizing relationships for all awards: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error during award relationships synchronization: {e}")
            return {
                "total_awards": 0,
                "success": 0,
                "failed": 0,
                "error": str(e),
                "relationships": {}
            } 