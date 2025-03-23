"""
Degree Sync Service Module.

This module provides the DegreeSyncService class for synchronizing Degree
data between PostgreSQL and Neo4j.
"""

import logging
from typing import Optional, Tuple, List, Dict, Any

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
    
    async def sync_by_id(self, degree_id: str) -> bool:
        """
        Synchronize a single degree by ID.
        
        Args:
            degree_id: ID of the degree to synchronize
            
        Returns:
            True if synchronization was successful, False otherwise
        """
        try:
            # Get degree from SQL database with details
            degree = await self.degree_repository.get_by_id(degree_id)
            if not degree:
                logger.warning(f"Degree with ID {degree_id} not found in SQL database")
                return False
            
            # Convert to Neo4j node and save
            degree_node = self._convert_to_node(degree)
            result = await self.degree_graph_repository.create_or_update(degree_node)
            
            if result:
                logger.info(f"Successfully synchronized degree {degree_id}")
                return True
            else:
                logger.error(f"Failed to synchronize degree {degree_id}")
                return False
            
        except Exception as e:
            logger.error(f"Error synchronizing degree {degree_id}: {str(e)}")
            return False
    
    async def sync_all(self, limit: Optional[int] = None, offset: int = 0) -> Tuple[int, int]:
        """
        Synchronize all degrees from PostgreSQL to Neo4j.
        
        Args:
            limit: Optional maximum number of degrees to synchronize
            offset: Optional offset for pagination
            
        Returns:
            Tuple containing counts of (successful, failed) synchronizations
        """
        success_count = 0
        failure_count = 0
        
        try:
            # Get all degrees from SQL database with details
            degrees, total = await self.degree_repository.get_all(skip=offset, limit=limit)
            
            logger.info(f"Found {total} degrees to synchronize")
            
            # Synchronize each degree
            for degree in degrees:
                if await self.sync_by_id(degree.degree_id):
                    success_count += 1
                else:
                    failure_count += 1
                    
            logger.info(f"Degree synchronization complete. Success: {success_count}, Failed: {failure_count}")
            
        except Exception as e:
            logger.error(f"Error during degree synchronization: {str(e)}")
        
        return success_count, failure_count
    
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