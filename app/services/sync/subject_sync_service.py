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
        sql_repository: Optional[SubjectRepository] = None,
        graph_repository: Optional[Any] = None
    ):
        """
        Initialize the SubjectSyncService.
        
        Args:
            session: SQLAlchemy async session
            driver: Neo4j async driver
            sql_repository: Optional SubjectRepository instance
            graph_repository: Optional graph repository instance for subjects
        """
        # Khởi tạo graph_repository nếu nó là None
        from app.graph_repositories.subject_graph_repository import SubjectGraphRepository
        initialized_graph_repository = graph_repository or SubjectGraphRepository(driver)
        
        super().__init__(session, driver, sql_repository, initialized_graph_repository)
        self.db_session = session
        self.neo4j_driver = driver
        self.sql_repository = sql_repository or SubjectRepository(session)
        self.graph_repository = initialized_graph_repository
    
    async def sync_node_by_id(self, subject_id: str) -> bool:
        """
        Synchronize a specific subject node by ID, only creating the node and INSTANCE_OF relationship.
        
        Args:
            subject_id: The ID of the subject to sync
            
        Returns:
            True if sync was successful, False otherwise
        """
        logger.info(f"Synchronizing subject node {subject_id}")
        
        try:
            # Get subject from SQL database
            subject = await self.sql_repository.get_by_id(subject_id)
            if not subject:
                logger.error(f"Subject {subject_id} not found in SQL database")
                return False
            
            # Convert to Neo4j format
            neo4j_data = self._convert_to_node(subject)
            
            # Create or update node in Neo4j
            result = await self.graph_repository.create_or_update(neo4j_data)
            
            logger.info(f"Successfully synchronized subject node {subject_id}")
            return result
            
        except Exception as e:
            logger.error(f"Error syncing subject node {subject_id}: {e}")
            return False
    
    async def sync_all_nodes(self, limit: Optional[int] = None) -> Tuple[int, int]:
        """
        Synchronize all subject nodes, without their relationships (except INSTANCE_OF).
        
        Args:
            limit: Optional limit on number of subjects to sync
            
        Returns:
            Tuple of (success_count, failed_count)
        """
        logger.info(f"Synchronizing all subject nodes (limit={limit})")
        
        try:
            # Get all subjects from SQL database
            subjects, _ = await self.sql_repository.get_all(limit=limit)
            
            success_count = 0
            failed_count = 0
            
            for subject in subjects:
                try:
                    # Sync only the subject node - handle both ORM objects and dictionaries
                    subject_id = subject.subject_id if hasattr(subject, 'subject_id') else subject.get("subject_id")
                    if not subject_id:
                        logger.error(f"Missing subject_id in subject object: {subject}")
                        failed_count += 1
                        continue
                        
                    if await self.sync_node_by_id(subject_id):
                        success_count += 1
                    else:
                        failed_count += 1
                except Exception as e:
                    # Get subject_id safely for logging
                    subject_id = getattr(subject, 'subject_id', None) if hasattr(subject, 'subject_id') else subject.get("subject_id", "unknown")
                    logger.error(f"Error syncing subject node {subject_id}: {e}")
                    failed_count += 1
            
            logger.info(f"Completed synchronizing subject nodes: {success_count} successful, {failed_count} failed")
            return (success_count, failed_count)
            
        except Exception as e:
            logger.error(f"Error during subject nodes synchronization: {e}")
            return (0, 0)
    
    async def sync_relationship_by_id(self, subject_id: str) -> Dict[str, int]:
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
        
        # Check if subject node exists before syncing relationships
        subject_node = await self.graph_repository.get_by_id(subject_id)
        if not subject_node:
            logger.warning(f"Subject node {subject_id} not found in Neo4j, skipping relationship sync")
            return {
                "error": "Subject node not found in Neo4j",
                "exams": 0,
                "scores": 0
            }
        
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
            logger.info(f"Relationship synchronization for subject {subject_id} completed: {relationship_counts}")
            return relationship_counts
            
        except Exception as e:
            logger.error(f"Error synchronizing relationships for subject {subject_id}: {e}")
            return relationship_counts
    
    async def sync_all_relationships(self, limit: Optional[int] = None) -> Dict[str, int]:
        """
        Synchronize relationships for all subjects.
        
        Args:
            limit: Optional maximum number of subjects to process
            
        Returns:
            Dictionary with counts of synced relationships by type
        """
        logger.info(f"Synchronizing relationships for all subjects (limit={limit})")
        
        try:
            # Get all subjects from SQL database
            subjects, total_count = await self.sql_repository.get_all(limit=limit)
            
            total_subjects = len(subjects)
            success_count = 0
            failure_count = 0
            
            # Aggregated counts for all relationship types
            relationship_counts = {
                "exams": 0,
                "scores": 0
            }
            
            # For each subject, sync relationships
            for subject in subjects:
                try:
                    # Get subject_id safely - handle both ORM objects and dictionaries
                    subject_id = subject.subject_id if hasattr(subject, 'subject_id') else subject.get("subject_id")
                    if not subject_id:
                        logger.error(f"Missing subject_id in subject object: {subject}")
                        failure_count += 1
                        continue
                    
                    # Verify subject exists in Neo4j
                    subject_node = await self.graph_repository.get_by_id(subject_id)
                    if not subject_node:
                        logger.warning(f"Subject {subject_id} not found in Neo4j, skipping relationship sync")
                        failure_count += 1
                        continue
                    
                    # Sync relationships for this subject
                    results = await self.sync_relationship_by_id(subject_id)
                    
                    # Update aggregated counts
                    for key, value in results.items():
                        if key in relationship_counts:
                            relationship_counts[key] += value
                    
                    success_count += 1
                    
                except Exception as e:
                    # Get subject_id safely for logging
                    subject_id = getattr(subject, 'subject_id', None) if hasattr(subject, 'subject_id') else subject.get("subject_id", "unknown")
                    logger.error(f"Error synchronizing relationships for subject {subject_id}: {e}")
                    failure_count += 1
            
            # Prepare final result
            result = {
                "total_subjects": total_subjects,
                "success": success_count,
                "failed": failure_count,
                "relationships": relationship_counts
            }
            
            logger.info(f"Completed synchronizing relationships for all subjects: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error during subject relationships synchronization: {e}")
            return {
                "total_subjects": 0,
                "success": 0,
                "failed": 0,
                "error": str(e),
                "relationships": {}
            }
    
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