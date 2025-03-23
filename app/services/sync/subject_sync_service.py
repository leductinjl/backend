"""
Subject Sync Service Module.

This module provides the SubjectSyncService class for synchronizing Subject
data between PostgreSQL and Neo4j.
"""

import logging
from typing import Optional, Tuple, Dict, Any, List

from sqlalchemy.ext.asyncio import AsyncSession
from neo4j import AsyncDriver

from app.domain.models.subject import Subject
from app.domain.graph_models.subject_node import SubjectNode
from app.repositories.subject_repository import SubjectRepository
from app.services.sync.base_sync_service import BaseSyncService

logger = logging.getLogger(__name__)

class SubjectSyncService(BaseSyncService):
    """
    Service for synchronizing Subject data between PostgreSQL and Neo4j.
    
    This service implements the BaseSyncService abstract class and provides
    methods for synchronizing individual subjects by ID and synchronizing
    all subjects in the database.
    """
    
    def __init__(
        self,
        session: AsyncSession,
        driver: AsyncDriver,
        subject_repository: Optional[SubjectRepository] = None,
        graph_repository: Optional[Any] = None
    ):
        """
        Initialize the SubjectSyncService.
        
        Args:
            session: SQLAlchemy async session
            driver: Neo4j async driver
            subject_repository: Optional SubjectRepository instance
            graph_repository: Optional graph repository instance for subjects
        """
        super().__init__(session, driver)
        self.db_session = session
        self.neo4j_driver = driver
        self.sql_repository = subject_repository or SubjectRepository(session)
        self.graph_repository = graph_repository
    
    async def sync_by_id(self, subject_id: str) -> bool:
        """
        Synchronize a single subject by ID.
        
        Args:
            subject_id: ID of the subject to synchronize
            
        Returns:
            True if synchronization was successful, False otherwise
        """
        try:
            # Get subject from SQL database
            subject = await self.sql_repository.get_by_id(subject_id)
            if not subject:
                logger.warning(f"Subject with ID {subject_id} not found in SQL database")
                return False
            
            # Convert to Neo4j node
            subject_node = self._convert_to_node(subject)
            
            # Create or update in Neo4j
            query = SubjectNode.create_query()
            await self.execute_neo4j_query(query, subject_node.to_dict())
            
            # Create INSTANCE_OF relationship
            instance_query = subject_node.create_instance_of_relationship_query()
            await self.execute_neo4j_query(instance_query, subject_node.to_dict())
            
            logger.info(f"Successfully synchronized subject {subject_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error synchronizing subject {subject_id}: {str(e)}")
            return False
    
    async def sync_all(self, limit: Optional[int] = None, offset: int = 0) -> Tuple[int, int]:
        """
        Synchronize all subjects from PostgreSQL to Neo4j.
        
        Args:
            limit: Optional maximum number of subjects to synchronize
            offset: Optional offset for pagination
            
        Returns:
            Tuple containing counts of (successful, failed) synchronizations
        """
        success_count = 0
        failure_count = 0
        
        try:
            # Get all subjects from SQL database with pagination
            subjects, total = await self.sql_repository.get_all(skip=offset, limit=limit or 100)
            
            logger.info(f"Found {total} subjects to synchronize")
            
            # Synchronize each subject
            for subject in subjects:
                if await self.sync_by_id(subject.subject_id):
                    success_count += 1
                else:
                    failure_count += 1
                    
            logger.info(f"Subject synchronization complete. Success: {success_count}, Failed: {failure_count}")
            
        except Exception as e:
            logger.error(f"Error during subject synchronization: {str(e)}")
        
        return success_count, failure_count
    
    def _convert_to_node(self, subject: Subject) -> SubjectNode:
        """
        Convert SQL subject model to a SubjectNode.
        
        Args:
            subject: Subject SQLAlchemy model instance
            
        Returns:
            SubjectNode instance ready for Neo4j
        """
        try:
            # Convert the Subject model to SubjectNode
            return SubjectNode.from_sql_model(subject)
            
        except Exception as e:
            logger.error(f"Error converting subject to node: {str(e)}")
            # Return a basic node with just the ID and name as fallback
            return SubjectNode(
                subject_id=subject.subject_id,
                subject_name=subject.subject_name
            ) 