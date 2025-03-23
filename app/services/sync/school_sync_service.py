"""
School Sync Service Module.

This module provides the SchoolSyncService class for synchronizing School
data between PostgreSQL and Neo4j.
"""

import logging
from typing import Optional, Tuple, List, Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession
from neo4j import AsyncDriver

from app.domain.models.school import School
from app.domain.graph_models.school_node import SchoolNode
from app.repositories.school_repository import SchoolRepository
from app.graph_repositories.school_graph_repository import SchoolGraphRepository
from app.services.sync.base_sync_service import BaseSyncService

logger = logging.getLogger(__name__)

class SchoolSyncService(BaseSyncService):
    """
    Service for synchronizing School data between PostgreSQL and Neo4j.
    
    This service implements the BaseSyncService abstract class and provides
    methods for synchronizing individual schools by ID and synchronizing
    all schools in the database.
    """
    
    def __init__(
        self,
        session: AsyncSession,
        driver: AsyncDriver,
        school_repository: Optional[SchoolRepository] = None,
        school_graph_repository: Optional[SchoolGraphRepository] = None
    ):
        """
        Initialize the SchoolSyncService.
        
        Args:
            session: SQLAlchemy async session
            driver: Neo4j async driver
            school_repository: Optional SchoolRepository instance
            school_graph_repository: Optional SchoolGraphRepository instance
        """
        self.db_session = session
        self.neo4j_driver = driver
        self.sql_repository = school_repository or SchoolRepository(session)
        self.graph_repository = school_graph_repository or SchoolGraphRepository(driver)
    
    async def sync_by_id(self, school_id: str) -> bool:
        """
        Synchronize a single school by ID.
        
        Args:
            school_id: ID of the school to synchronize
            
        Returns:
            True if synchronization was successful, False otherwise
        """
        try:
            # Get school from SQL database
            school = await self.sql_repository.get_by_id(school_id)
            if not school:
                logger.warning(f"School with ID {school_id} not found in SQL database")
                return False
            
            # Convert to Neo4j node and save
            school_node = self._convert_to_node(school)
            result = await self.graph_repository.create_or_update(school_node)
            
            if result:
                logger.info(f"Successfully synchronized school {school_id}")
                return True
            else:
                logger.error(f"Failed to synchronize school {school_id}")
                return False
            
        except Exception as e:
            logger.error(f"Error synchronizing school {school_id}: {str(e)}")
            return False
    
    async def sync_all(self, limit: Optional[int] = None, offset: int = 0) -> Tuple[int, int]:
        """
        Synchronize all schools from PostgreSQL to Neo4j.
        
        Args:
            limit: Optional maximum number of schools to synchronize
            offset: Optional offset for pagination
            
        Returns:
            Tuple containing counts of (successful, failed) synchronizations
        """
        success_count = 0
        failure_count = 0
        
        try:
            # Get all schools from SQL database
            schools, total = await self.sql_repository.get_all(skip=offset, limit=limit or 100)
            
            logger.info(f"Found {total} schools to synchronize")
            
            # Synchronize each school
            for school in schools:
                if await self.sync_by_id(school.school_id):
                    success_count += 1
                else:
                    failure_count += 1
                    
            logger.info(f"School synchronization complete. Success: {success_count}, Failed: {failure_count}")
            
        except Exception as e:
            logger.error(f"Error during school synchronization: {str(e)}")
        
        return success_count, failure_count
    
    def _convert_to_node(self, school: School) -> SchoolNode:
        """
        Convert a SQL School model to a SchoolNode.
        
        Args:
            school: SQL School model instance
            
        Returns:
            SchoolNode instance ready for Neo4j
        """
        try:
            # Create the school node
            school_node = SchoolNode.from_sql_model(school)
            return school_node
            
        except Exception as e:
            logger.error(f"Error converting school to node: {str(e)}")
            # Return a basic node with just the ID as fallback
            return SchoolNode(
                school_id=school.school_id,
                school_name=school.school_name
            )
    
    async def sync_school_majors(self, school_id: str) -> bool:
        """
        Synchronize the relationships between a school and its majors.
        
        Args:
            school_id: ID of the school
            
        Returns:
            True if synchronization was successful, False otherwise
        """
        try:
            # Get school from SQL database
            school = await self.sql_repository.get_by_id(school_id)
            if not school:
                logger.warning(f"School with ID {school_id} not found in SQL database")
                return False
                
            # Process majors if school has the school_majors relationship
            if hasattr(school, 'school_majors') and school.school_majors:
                for school_major in school.school_majors:
                    # Add relationship between school and major
                    success = await self.graph_repository.add_offers_major_relationship(
                        school_id, 
                        school_major.major_id,
                        school_major.start_year
                    )
                    if not success:
                        logger.warning(f"Failed to create relationship between school {school_id} and major {school_major.major_id}")
                
            return True
            
        except Exception as e:
            logger.error(f"Error synchronizing school-major relationships for school {school_id}: {str(e)}")
            return False 