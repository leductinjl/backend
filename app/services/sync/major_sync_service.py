"""
Major Sync Service Module.

This module provides the MajorSyncService class for synchronizing Major
data between PostgreSQL and Neo4j.
"""

import logging
from typing import Optional, Tuple, List, Dict, Any, Union

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
    
    async def sync_by_id(self, major_id: str, skip_relationships: bool = False) -> bool:
        """
        Synchronize a specific major by ID.
        
        Args:
            major_id: The ID of the major to sync
            skip_relationships: If True, only sync node without its relationships
            
        Returns:
            True if sync was successful, False otherwise
        """
        logger.info(f"Synchronizing major {major_id} (skip_relationships={skip_relationships})")
        
        try:
            # Get major from SQL database
            major = await self.sql_repository.get_by_id(major_id)
            if not major:
                logger.error(f"Major {major_id} not found in SQL database")
                return False
            
            # Convert to Neo4j format
            neo4j_data = self._convert_to_node(major)
            
            # Create or update node in Neo4j
            await self.graph_repository.create_or_update(neo4j_data)
            
            # Sync relationships if needed
            if not skip_relationships:
                await self.sync_relationships(major_id)
            
            return True
            
        except Exception as e:
            logger.error(f"Error syncing major {major_id}: {e}")
            return False
    
    async def sync_all(self, limit: Optional[int] = None, skip_relationships: bool = False) -> Union[Tuple[int, int], Dict[str, int]]:
        """
        Synchronize all majors.
        
        Args:
            limit: Optional limit on number of majors to sync
            skip_relationships: If True, only sync nodes without their relationships
            
        Returns:
            Tuple of (success_count, failed_count) or dict with success/failed counts
        """
        logger.info(f"Synchronizing all majors (skip_relationships={skip_relationships})")
        
        try:
            # Get all majors from SQL database
            majors, _ = await self.sql_repository.get_all(limit=limit)
            
            success_count = 0
            failed_count = 0
            
            for major in majors:
                try:
                    # Sync the major node - handle both ORM objects and dictionaries
                    major_id = major.major_id if hasattr(major, 'major_id') else major.get("major_id")
                    if not major_id:
                        logger.error(f"Missing major_id in major object: {major}")
                        failed_count += 1
                        continue
                        
                    await self.sync_by_id(major_id, skip_relationships=skip_relationships)
                    success_count += 1
                except Exception as e:
                    # Get major_id safely for logging
                    major_id = getattr(major, 'major_id', None) if hasattr(major, 'major_id') else major.get("major_id", "unknown")
                    logger.error(f"Error syncing major {major_id}: {e}")
                    failed_count += 1
            
            return (success_count, failed_count)
            
        except Exception as e:
            logger.error(f"Error during major synchronization: {e}")
            return {"success": 0, "failed": 0}
    
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
            
    async def sync_relationships(self, major_id: str) -> Dict[str, int]:
        """
        Synchronize relationships for a specific major.
        
        Args:
            major_id: ID of the major to synchronize relationships for
            
        Returns:
            Dictionary with counts of successfully synced relationships by type
        """
        logger.info(f"Synchronizing relationships for major {major_id}")
        
        relationship_counts = {
            "schools": 0,
            "degrees": 0
        }
        
        try:
            # Get major from SQL database with full details
            major = await self.sql_repository.get_by_id(major_id)
            if not major:
                logger.error(f"Major {major_id} not found in SQL database")
                return relationship_counts
            
            # Sync OFFERED_BY relationships (major-school)
            if hasattr(major, 'school_majors') and major.school_majors:
                for school_major in major.school_majors:
                    if hasattr(school_major, 'school_id') and school_major.school_id:
                        success = await self.graph_repository.add_offered_by_relationship(
                            major_id, 
                            school_major.school_id,
                            school_major.start_year
                        )
                        if success:
                            relationship_counts["schools"] += 1
            
            # Sync HAS_MAJOR relationships (degree-major)
            if hasattr(major, 'degrees') and major.degrees:
                for degree in major.degrees:
                    degree_id = degree.degree_id
                    success = await self.graph_repository.add_has_major_relationship(degree_id, major_id)
                    if success:
                        relationship_counts["degrees"] += 1
            
            logger.info(f"Major relationship synchronization completed for {major_id}")
            return relationship_counts
            
        except Exception as e:
            logger.error(f"Error synchronizing relationships for major {major_id}: {e}")
            return relationship_counts 