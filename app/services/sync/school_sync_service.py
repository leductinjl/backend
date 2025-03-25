"""
School Sync Service Module.

This module provides the SchoolSyncService class for synchronizing School
data between PostgreSQL and Neo4j.
"""

import logging
from typing import Optional, Tuple, List, Dict, Any, Union

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
        sql_repository: Optional[SchoolRepository] = None,
        graph_repository: Optional[SchoolGraphRepository] = None
    ):
        """
        Initialize the SchoolSyncService.
        
        Args:
            session: SQLAlchemy async session
            driver: Neo4j async driver
            sql_repository: Optional SchoolRepository instance
            graph_repository: Optional SchoolGraphRepository instance
        """
        super().__init__(session, driver, sql_repository, graph_repository)
        self.db_session = session
        self.neo4j_driver = driver
        self.sql_repository = sql_repository or SchoolRepository(session)
        self.graph_repository = graph_repository or SchoolGraphRepository(driver)
    
    async def sync_node_by_id(self, school_id: str) -> bool:
        """
        Synchronize a specific school node by ID, only creating the node and INSTANCE_OF relationship.
        
        Args:
            school_id: The ID of the school to sync
            
        Returns:
            True if sync was successful, False otherwise
        """
        logger.info(f"Synchronizing school node {school_id}")
        
        try:
            # Get school from SQL database
            school = await self.sql_repository.get_by_id(school_id)
            if not school:
                logger.error(f"School {school_id} not found in SQL database")
                return False
            
            # Convert to Neo4j format
            neo4j_data = self._convert_to_node(school)
            
            # Create or update node in Neo4j
            result = await self.graph_repository.create_or_update(neo4j_data)
            
            logger.info(f"Successfully synchronized school node {school_id}")
            return result
            
        except Exception as e:
            logger.error(f"Error syncing school node {school_id}: {e}")
            return False
    
    async def sync_all_nodes(self, limit: Optional[int] = None) -> Tuple[int, int]:
        """
        Synchronize all school nodes, without their relationships (except INSTANCE_OF).
        
        Args:
            limit: Optional limit on number of schools to sync
            
        Returns:
            Tuple of (success_count, failed_count)
        """
        logger.info(f"Synchronizing all school nodes (limit={limit})")
        
        try:
            # Get all schools from SQL database
            schools, _ = await self.sql_repository.get_all(limit=limit)
            
            success_count = 0
            failed_count = 0
            
            for school in schools:
                try:
                    # Sync only the school node - handle both ORM objects and dictionaries
                    school_id = school.school_id if hasattr(school, 'school_id') else school.get("school_id")
                    if not school_id:
                        logger.error(f"Missing school_id in school object: {school}")
                        failed_count += 1
                        continue
                        
                    if await self.sync_node_by_id(school_id):
                        success_count += 1
                    else:
                        failed_count += 1
                except Exception as e:
                    # Get school_id safely for logging
                    school_id = getattr(school, 'school_id', None) if hasattr(school, 'school_id') else school.get("school_id", "unknown")
                    logger.error(f"Error syncing school node {school_id}: {e}")
                    failed_count += 1
            
            logger.info(f"Completed synchronizing school nodes: {success_count} successful, {failed_count} failed")
            return (success_count, failed_count)
            
        except Exception as e:
            logger.error(f"Error during school nodes synchronization: {e}")
            return (0, 0)
    
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
    
    async def sync_relationship_by_id(self, school_id: str) -> Dict[str, int]:
        """
        Synchronize relationships for a specific school.
        
        Args:
            school_id: ID of the school to synchronize relationships for
            
        Returns:
            Dictionary with counts of successfully synced relationships by type
        """
        logger.info(f"Synchronizing relationships for school {school_id}")
        
        # Check if school node exists before syncing relationships
        school_node = await self.graph_repository.get_by_id(school_id)
        if not school_node:
            logger.warning(f"School node {school_id} not found in Neo4j, skipping relationship sync")
            return {
                "error": "School node not found in Neo4j",
                "majors": 0,
                "candidates": 0,
                "management_units": 0
            }
        
        relationship_counts = {
            "majors": 0,
            "candidates": 0,
            "management_units": 0
        }
        
        try:
            # Sync school-major relationships
            success = await self.sync_school_majors(school_id)
            
            if success:
                # Get school again to count relationships
                school = await self.sql_repository.get_by_id(school_id)
                if school and hasattr(school, 'school_majors'):
                    relationship_counts["majors"] = len(school.school_majors)
            
            logger.info(f"School relationship synchronization completed for {school_id}: {relationship_counts}")
            return relationship_counts
            
        except Exception as e:
            logger.error(f"Error synchronizing relationships for school {school_id}: {e}")
            return relationship_counts
    
    async def sync_all_relationships(self, limit: Optional[int] = None) -> Dict[str, int]:
        """
        Synchronize relationships for all schools.
        
        Args:
            limit: Optional maximum number of schools to process
            
        Returns:
            Dictionary with counts of synced relationships by type
        """
        logger.info(f"Synchronizing relationships for all schools (limit={limit})")
        
        try:
            # Get all schools from SQL database
            schools, total_count = await self.sql_repository.get_all(limit=limit)
            
            total_schools = len(schools)
            success_count = 0
            failure_count = 0
            
            # Aggregated counts for all relationship types
            relationship_counts = {
                "majors": 0,
                "candidates": 0,
                "management_units": 0
            }
            
            # For each school, sync relationships
            for school in schools:
                try:
                    # Get school_id safely - handle both ORM objects and dictionaries
                    school_id = school.school_id if hasattr(school, 'school_id') else school.get("school_id")
                    if not school_id:
                        logger.error(f"Missing school_id in school object: {school}")
                        failure_count += 1
                        continue
                    
                    # Verify school exists in Neo4j
                    school_node = await self.graph_repository.get_by_id(school_id)
                    if not school_node:
                        logger.warning(f"School {school_id} not found in Neo4j, skipping relationship sync")
                        failure_count += 1
                        continue
                    
                    # Sync relationships for this school
                    results = await self.sync_relationship_by_id(school_id)
                    
                    # Update aggregated counts
                    for key, value in results.items():
                        if key in relationship_counts:
                            relationship_counts[key] += value
                    
                    success_count += 1
                    
                except Exception as e:
                    # Get school_id safely for logging
                    school_id = getattr(school, 'school_id', None) if hasattr(school, 'school_id') else school.get("school_id", "unknown")
                    logger.error(f"Error synchronizing relationships for school {school_id}: {e}")
                    failure_count += 1
            
            # Prepare final result
            result = {
                "total_schools": total_schools,
                "success": success_count,
                "failed": failure_count,
                "relationships": relationship_counts
            }
            
            logger.info(f"Completed synchronizing relationships for all schools: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error during school relationships synchronization: {e}")
            return {
                "total_schools": 0,
                "success": 0,
                "failed": 0,
                "error": str(e),
                "relationships": {}
            }
    
    async def sync_school_majors(self, school_id: str) -> bool:
        """
        Synchronize the relationships between a school and its majors.
        
        Args:
            school_id: ID of the school
            
        Returns:
            True if synchronization was successful, False otherwise
        """
        try:
            # Khởi tạo SchoolMajorRepository nếu cần
            from app.repositories.school_major_repository import SchoolMajorRepository
            school_major_repository = SchoolMajorRepository(self.db_session)
            
            # Truy vấn trực tiếp từ repository thay vì sử dụng lazy-loaded relationship
            query_result = await school_major_repository.get_all(filters={"school_id": school_id})
            school_majors = query_result[0] if isinstance(query_result, tuple) and len(query_result) > 0 else []
            
            # Xử lý từng major
            for school_major in school_majors:
                # Lấy major_id từ kết quả truy vấn
                major_id = school_major.get("major_id") if isinstance(school_major, dict) else getattr(school_major, "major_id", None)
                start_year = school_major.get("start_year") if isinstance(school_major, dict) else getattr(school_major, "start_year", None)
                
                if major_id:
                    # Thêm mối quan hệ giữa school và major
                    success = await self.graph_repository.add_offers_major_relationship(
                        school_id, 
                        major_id,
                        start_year
                    )
                    if not success:
                        logger.warning(f"Failed to create relationship between school {school_id} and major {major_id}")
                
            return True
            
        except Exception as e:
            logger.error(f"Error synchronizing school-major relationships for school {school_id}: {str(e)}")
            return False 