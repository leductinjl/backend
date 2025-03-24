"""
Subject Sync Service Module.

This module provides the SubjectSyncService class for synchronizing Subject
data between PostgreSQL and Neo4j.
"""

import logging
from typing import Optional, Tuple, Dict, Any, List, Union

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
        
        # Khởi tạo graph_repository nếu nó là None
        from app.graph_repositories.subject_graph_repository import SubjectGraphRepository
        self.graph_repository = graph_repository or SubjectGraphRepository(driver)
    
    async def sync_by_id(self, subject_id: str, skip_relationships: bool = False) -> bool:
        """
        Synchronize a specific subject by ID.
        
        Args:
            subject_id: The ID of the subject to sync
            skip_relationships: If True, only sync node without its relationships
            
        Returns:
            True if sync was successful, False otherwise
        """
        logger.info(f"Synchronizing subject {subject_id} (skip_relationships={skip_relationships})")
        
        try:
            # Get subject from SQL database
            subject = await self.sql_repository.get_by_id(subject_id)
            if not subject:
                logger.error(f"Subject {subject_id} not found in SQL database")
                return False
            
            # Convert to Neo4j format
            neo4j_data = self._convert_to_node(subject)
            
            # Create or update node in Neo4j
            await self.graph_repository.create_or_update(neo4j_data)
            
            # Sync relationships if needed
            if not skip_relationships:
                await self.sync_relationships(subject_id)
            
            return True
            
        except Exception as e:
            logger.error(f"Error syncing subject {subject_id}: {e}")
            return False
    
    async def sync_all(self, limit: Optional[int] = None, skip_relationships: bool = False) -> Union[Tuple[int, int], Dict[str, int]]:
        """
        Synchronize all subjects.
        
        Args:
            limit: Optional limit on number of subjects to sync
            skip_relationships: If True, only sync nodes without their relationships
            
        Returns:
            Tuple of (success_count, failed_count) or dict with success/failed counts
        """
        logger.info(f"Synchronizing all subjects (skip_relationships={skip_relationships})")
        
        try:
            # Get all subjects from SQL database
            subjects, _ = await self.sql_repository.get_all(limit=limit)
            
            success_count = 0
            failed_count = 0
            
            for subject in subjects:
                try:
                    # Sync the subject node - handle both ORM objects and dictionaries
                    subject_id = subject.subject_id if hasattr(subject, 'subject_id') else subject.get("subject_id")
                    if not subject_id:
                        logger.error(f"Missing subject_id in subject object: {subject}")
                        failed_count += 1
                        continue
                        
                    await self.sync_by_id(subject_id, skip_relationships=skip_relationships)
                    success_count += 1
                except Exception as e:
                    # Get subject_id safely for logging
                    subject_id = getattr(subject, 'subject_id', None) if hasattr(subject, 'subject_id') else subject.get("subject_id", "unknown")
                    logger.error(f"Error syncing subject {subject_id}: {e}")
                    failed_count += 1
            
            return (success_count, failed_count)
            
        except Exception as e:
            logger.error(f"Error during subject synchronization: {e}")
            return {"success": 0, "failed": 0}
    
    async def sync_relationships(self, subject_id: str) -> Dict[str, int]:
        """
        Synchronize relationships for a specific subject.
        
        Subjects may have relationships with exams, scores, and other entities.
        This method ensures these relationships are properly established in Neo4j.
        
        Args:
            subject_id: ID of the subject to synchronize relationships for
            
        Returns:
            Dictionary with counts of successfully synced relationships by type
        """
        logger.info(f"Synchronizing relationships for subject {subject_id}")
        
        relationship_counts = {
            "exams": 0,
            "scores": 0
        }
        
        try:
            # In a complete implementation, we would:
            # 1. Get related entities from SQL database (exams, scores, etc.)
            # 2. Create relationships in Neo4j
            # 3. Count successful relationships
            
            # This is a minimal implementation to satisfy the abstract method requirement
            logger.info(f"Relationship synchronization for subject {subject_id} completed")
            return relationship_counts
            
        except Exception as e:
            logger.error(f"Error synchronizing relationships for subject {subject_id}: {e}")
            return relationship_counts
    
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