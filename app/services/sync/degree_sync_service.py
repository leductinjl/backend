"""
Degree Sync Service Module.

This module provides the DegreeSyncService class for synchronizing Degree
data between PostgreSQL and Neo4j.
"""

import logging
from typing import Optional, Tuple, List, Dict, Any, Union

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from neo4j import AsyncDriver

from app.domain.models.degree import Degree
from app.domain.graph_models.degree_node import DegreeNode
from app.repositories.degree_repository import DegreeRepository
from app.graph_repositories.degree_graph_repository import DegreeGraphRepository
from app.services.sync.base_sync_service import BaseSyncService

logger = logging.getLogger(__name__)

class DegreeSyncService(BaseSyncService):
    """
    Service for synchronizing Degree data between PostgreSQL and Neo4j.
    
    This service implements the BaseSyncService abstract class and provides
    methods for synchronizing individual degrees by ID and synchronizing
    all degrees in the database.
    """
    
    def __init__(
        self,
        session: AsyncSession,
        driver: AsyncDriver,
        degree_repository: Optional[DegreeRepository] = None,
        degree_graph_repository: Optional[DegreeGraphRepository] = None
    ):
        """
        Initialize the DegreeSyncService.
        
        Args:
            session: SQLAlchemy async session
            driver: Neo4j async driver
            degree_repository: Optional DegreeRepository instance
            degree_graph_repository: Optional DegreeGraphRepository instance
        """
        self.session = session
        self.driver = driver
        self.degree_repository = degree_repository or DegreeRepository(session)
        self.degree_graph_repository = degree_graph_repository or DegreeGraphRepository(driver)
    
    async def sync_by_id(self, degree_id: str, skip_relationships: bool = False) -> bool:
        """
        Synchronize a specific degree by ID.
        
        Args:
            degree_id: The ID of the degree to sync
            skip_relationships: If True, only sync node without its relationships
            
        Returns:
            True if sync was successful, False otherwise
        """
        logger.info(f"Synchronizing degree {degree_id} (skip_relationships={skip_relationships})")
        
        try:
            # Get degree from SQL database
            degree = await self.degree_repository.get_by_id(degree_id)
            if not degree:
                logger.error(f"Degree {degree_id} not found in SQL database")
                return False
            
            # Convert to Neo4j format
            neo4j_data = self._convert_to_node(degree)
            
            # Create or update node in Neo4j
            await self.degree_graph_repository.create_or_update(neo4j_data)
            
            # Sync relationships if needed
            if not skip_relationships:
                await self.sync_relationships(degree_id)
            
            return True
            
        except Exception as e:
            logger.error(f"Error syncing degree {degree_id}: {e}")
            return False
    
    async def sync_all(self, limit: Optional[int] = None, skip_relationships: bool = False) -> Union[Tuple[int, int], Dict[str, int]]:
        """
        Synchronize all degrees.
        
        Args:
            limit: Optional limit on number of degrees to sync
            skip_relationships: If True, only sync nodes without their relationships
            
        Returns:
            Tuple of (success_count, failed_count) or dict with success/failed counts
        """
        logger.info(f"Synchronizing all degrees (skip_relationships={skip_relationships})")
        
        try:
            # Get all degrees from SQL database
            degrees, _ = await self.degree_repository.get_all(limit=limit)
            
            success_count = 0
            failed_count = 0
            
            for degree in degrees:
                try:
                    # Sync the degree node - handle both ORM objects and dictionaries
                    degree_id = degree.degree_id if hasattr(degree, 'degree_id') else degree.get("degree_id")
                    if not degree_id:
                        logger.error(f"Missing degree_id in degree object: {degree}")
                        failed_count += 1
                        continue
                        
                    await self.sync_by_id(degree_id, skip_relationships=skip_relationships)
                    success_count += 1
                except Exception as e:
                    # Get degree_id safely for logging
                    degree_id = getattr(degree, 'degree_id', None) if hasattr(degree, 'degree_id') else degree.get("degree_id", "unknown")
                    logger.error(f"Error syncing degree {degree_id}: {e}")
                    failed_count += 1
            
            return (success_count, failed_count)
            
        except Exception as e:
            logger.error(f"Error during degree synchronization: {e}")
            return {"success": 0, "failed": 0}
    
    def _convert_to_node(self, degree: Degree) -> DegreeNode:
        """
        Convert a SQL Degree model to a DegreeNode.
        
        Args:
            degree: SQL Degree instance
            
        Returns:
            DegreeNode instance ready for Neo4j
        """
        try:
            # Extract candidate_id if possible
            candidate_id = None
            if hasattr(degree, 'education_history') and degree.education_history:
                if hasattr(degree.education_history, 'candidate_id'):
                    candidate_id = degree.education_history.candidate_id
            
            # Extract school_id if possible
            school_id = None
            if hasattr(degree, 'education_history') and degree.education_history:
                if hasattr(degree.education_history, 'school_id'):
                    school_id = degree.education_history.school_id
            
            # Create a degree name from major if available
            degree_name = f"Degree {degree.degree_id}"
            if hasattr(degree, 'major') and degree.major:
                if hasattr(degree.major, 'major_name'):
                    degree_name = f"{degree.major.major_name} Degree"
            
            # Create the degree node
            degree_node = DegreeNode(
                degree_id=degree.degree_id,
                degree_name=degree_name,
                candidate_id=candidate_id,
                major_id=degree.major_id,
                school_id=school_id,
                degree_type="Academic",  # Default value
                start_year=degree.start_year,
                end_year=degree.end_year,
                academic_performance=degree.academic_performance,
                additional_info=degree.additional_info,
                degree_image_url=degree.degree_image_url
            )
            
            return degree_node
            
        except Exception as e:
            logger.error(f"Error converting degree to node: {str(e)}")
            # Return a basic node with just the ID as fallback
            return DegreeNode(
                degree_id=degree.degree_id,
                degree_name=f"Degree {degree.degree_id}"
            )
            
    async def sync_relationships(self, degree_id: str) -> Dict[str, int]:
        """
        Synchronize relationships for a specific degree.
        
        Args:
            degree_id: ID of the degree to synchronize relationships for
            
        Returns:
            Dictionary with counts of successfully synced relationships by type
        """
        logger.info(f"Synchronizing relationships for degree {degree_id}")
        
        relationship_counts = {
            "candidate": 0,
            "school": 0,
            "major": 0
        }
        
        try:
            # Get degree from SQL database with full details
            degree = await self.degree_repository.get_by_id(degree_id)
            if not degree:
                logger.error(f"Degree {degree_id} not found in SQL database")
                return relationship_counts
            
            # Extract candidate_id if possible
            candidate_id = None
            if hasattr(degree, 'education_history') and degree.education_history:
                if hasattr(degree.education_history, 'candidate_id'):
                    candidate_id = degree.education_history.candidate_id
            
            # Sync EARNED_BY relationship (degree-candidate)
            if candidate_id:
                success = await self.degree_graph_repository.add_earned_by_relationship(degree_id, candidate_id)
                if success:
                    relationship_counts["candidate"] += 1
            
            # Extract school_id if possible
            school_id = None
            if hasattr(degree, 'education_history') and degree.education_history:
                if hasattr(degree.education_history, 'school_id'):
                    school_id = degree.education_history.school_id
            
            # Sync FROM_SCHOOL relationship (degree-school)
            if school_id:
                success = await self.degree_graph_repository.add_from_school_relationship(degree_id, school_id)
                if success:
                    relationship_counts["school"] += 1
            
            # Extract major_id
            major_id = degree.major_id
            
            # Sync IN_MAJOR relationship (degree-major)
            if major_id:
                success = await self.degree_graph_repository.add_in_major_relationship(degree_id, major_id)
                if success:
                    relationship_counts["major"] += 1
            
            logger.info(f"Degree relationship synchronization completed for {degree_id}")
            return relationship_counts
            
        except Exception as e:
            logger.error(f"Error synchronizing relationships for degree {degree_id}: {e}")
            return relationship_counts 