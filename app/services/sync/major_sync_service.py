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
        sql_repository: Optional[MajorRepository] = None,
        graph_repository: Optional[MajorGraphRepository] = None
    ):
        """
        Initialize the MajorSyncService.
        
        Args:
            session: SQLAlchemy async session
            driver: Neo4j async driver
            sql_repository: Optional MajorRepository instance
            graph_repository: Optional MajorGraphRepository instance
        """
        super().__init__(session, driver, sql_repository, graph_repository)
        self.db_session = session
        self.neo4j_driver = driver
        self.sql_repository = sql_repository or MajorRepository(session)
        self.graph_repository = graph_repository or MajorGraphRepository(driver)
    
    async def sync_node_by_id(self, major_id: str) -> bool:
        """
        Synchronize a specific major node by ID, only creating the node and INSTANCE_OF relationship.
        
        Args:
            major_id: The ID of the major to sync
            
        Returns:
            True if sync was successful, False otherwise
        """
        logger.info(f"Synchronizing major node {major_id}")
        
        try:
            # Get major from SQL database
            major = await self.sql_repository.get_by_id(major_id)
            if not major:
                logger.error(f"Major {major_id} not found in SQL database")
                return False
            
            # Convert to Neo4j format
            neo4j_data = self._convert_to_node(major)
            
            # Create or update node in Neo4j
            result = await self.graph_repository.create_or_update(neo4j_data)
            
            logger.info(f"Successfully synchronized major node {major_id}")
            return result
            
        except Exception as e:
            logger.error(f"Error syncing major node {major_id}: {e}")
            return False
    
    async def sync_all_nodes(self, limit: Optional[int] = None) -> Tuple[int, int]:
        """
        Synchronize all major nodes, without their relationships (except INSTANCE_OF).
        
        Args:
            limit: Optional limit on number of majors to sync
            
        Returns:
            Tuple of (success_count, failed_count)
        """
        logger.info(f"Synchronizing all major nodes (limit={limit})")
        
        try:
            # Get all majors from SQL database
            majors, _ = await self.sql_repository.get_all(limit=limit)
            
            success_count = 0
            failed_count = 0
            
            for major in majors:
                try:
                    # Sync only the major node - handle both ORM objects and dictionaries
                    major_id = major.major_id if hasattr(major, 'major_id') else major.get("major_id")
                    if not major_id:
                        logger.error(f"Missing major_id in major object: {major}")
                        failed_count += 1
                        continue
                        
                    if await self.sync_node_by_id(major_id):
                        success_count += 1
                    else:
                        failed_count += 1
                except Exception as e:
                    # Get major_id safely for logging
                    major_id = getattr(major, 'major_id', None) if hasattr(major, 'major_id') else major.get("major_id", "unknown")
                    logger.error(f"Error syncing major node {major_id}: {e}")
                    failed_count += 1
            
            logger.info(f"Completed synchronizing major nodes: {success_count} successful, {failed_count} failed")
            return (success_count, failed_count)
            
        except Exception as e:
            logger.error(f"Error during major nodes synchronization: {e}")
            return (0, 0)
    
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
            
    async def sync_relationship_by_id(self, major_id: str) -> Dict[str, int]:
        """
        Synchronize relationships for a specific major.
        
        Args:
            major_id: ID of the major to synchronize relationships for
            
        Returns:
            Dictionary with counts of successfully synced relationships by type
        """
        logger.info(f"Synchronizing relationships for major {major_id}")
        
        # Check if major node exists before syncing relationships
        major_node = await self.graph_repository.get_by_id(major_id)
        if not major_node:
            logger.warning(f"Major node {major_id} not found in Neo4j, skipping relationship sync")
            return {
                "error": "Major node not found in Neo4j",
                "schools": 0,
                "degrees": 0
            }
        
        relationship_counts = {
            "schools": 0,
            "degrees": 0
        }
        
        try:
            # Import text for SQL queries
            from sqlalchemy import text
            
            # Instead of trying to access ORM relationships directly, use SQL queries to get related data
            # 1. Get school-major relationships from the database
            query = text("""
            SELECT sm.school_id, sm.start_year 
            FROM school_major sm 
            WHERE sm.major_id = :major_id
            """)
            result = await self.db_session.execute(query, {"major_id": major_id})
            school_majors = result.fetchall()
            
            # Sync school relationships
            for school_major in school_majors:
                school_id = school_major[0]
                start_year = school_major[1]
                if school_id:
                    success = await self.graph_repository.add_offered_by_relationship(
                        major_id, 
                        school_id,
                        start_year
                    )
                    if success:
                        relationship_counts["schools"] += 1
            
            # 2. Get degree-major relationships from the database
            query = text("""
            SELECT d.degree_id
            FROM degree d
            WHERE d.major_id = :major_id
            """)
            result = await self.db_session.execute(query, {"major_id": major_id})
            degrees = result.fetchall()
            
            # Sync degree relationships
            for degree in degrees:
                degree_id = degree[0]
                if degree_id:
                    success = await self.graph_repository.add_has_major_relationship(
                        degree_id, 
                        major_id
                    )
                    if success:
                        relationship_counts["degrees"] += 1
            
            logger.info(f"Major relationship synchronization completed for {major_id}: {relationship_counts}")
            return relationship_counts
            
        except Exception as e:
            logger.error(f"Error synchronizing relationships for major {major_id}: {e}")
            return relationship_counts
    
    async def sync_all_relationships(self, limit: Optional[int] = None) -> Dict[str, int]:
        """
        Synchronize relationships for all majors.
        
        Args:
            limit: Optional maximum number of majors to process
            
        Returns:
            Dictionary with counts of synced relationships by type
        """
        logger.info(f"Synchronizing relationships for all majors (limit={limit})")
        
        try:
            # Import text for SQL queries
            from sqlalchemy import text
            
            # Get all majors' IDs from SQL database - using a more direct approach
            # to avoid any lazy loading issues
            sql_query = "SELECT major_id FROM major"
            if limit:
                sql_query += f" LIMIT {limit}"
            
            query = text(sql_query)
            result = await self.db_session.execute(query)
            major_ids = [row[0] for row in result.fetchall()]
            
            total_majors = len(major_ids)
            success_count = 0
            failure_count = 0
            
            # Aggregated counts for all relationship types
            relationship_counts = {
                "schools": 0,
                "degrees": 0
            }
            
            # For each major, sync relationships
            for major_id in major_ids:
                try:
                    # Verify major exists in Neo4j
                    major_node = await self.graph_repository.get_by_id(major_id)
                    if not major_node:
                        logger.warning(f"Major {major_id} not found in Neo4j, skipping relationship sync")
                        failure_count += 1
                        continue
                    
                    # Sync relationships for this major
                    results = await self.sync_relationship_by_id(major_id)
                    
                    # Update aggregated counts
                    for key, value in results.items():
                        if key in relationship_counts:
                            relationship_counts[key] += value
                    
                    success_count += 1
                    
                except Exception as e:
                    logger.error(f"Error synchronizing relationships for major {major_id}: {e}")
                    failure_count += 1
            
            # Prepare final result
            result = {
                "total_majors": total_majors,
                "success": success_count,
                "failed": failure_count,
                "relationships": relationship_counts
            }
            
            logger.info(f"Completed synchronizing relationships for all majors: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error during major relationships synchronization: {e}")
            return {
                "total_majors": 0,
                "success": 0,
                "failed": 0,
                "error": str(e),
                "relationships": {}
            } 