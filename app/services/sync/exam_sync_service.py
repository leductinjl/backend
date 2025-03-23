"""
Exam Sync Service Module.

This module provides the ExamSyncService class for synchronizing Exam
data between PostgreSQL and Neo4j.
"""

import logging
from typing import Optional, Tuple, List, Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession
from neo4j import AsyncDriver

from app.domain.models.exam import Exam
from app.domain.graph_models.exam_node import ExamNode
from app.repositories.exam_repository import ExamRepository
from app.graph_repositories.exam_graph_repository import ExamGraphRepository
from app.services.sync.base_sync_service import BaseSyncService

logger = logging.getLogger(__name__)

class ExamSyncService(BaseSyncService):
    """
    Service for synchronizing Exam data between PostgreSQL and Neo4j.
    
    This service implements the BaseSyncService abstract class and provides
    methods for synchronizing individual exams by ID and synchronizing
    all exams in the database.
    """
    
    def __init__(
        self,
        session: AsyncSession,
        driver: AsyncDriver,
        exam_repository: Optional[ExamRepository] = None,
        exam_graph_repository: Optional[ExamGraphRepository] = None
    ):
        """
        Initialize the ExamSyncService.
        
        Args:
            session: SQLAlchemy async session
            driver: Neo4j async driver
            exam_repository: Optional ExamRepository instance
            exam_graph_repository: Optional ExamGraphRepository instance
        """
        self.session = session
        self.driver = driver
        self.exam_repository = exam_repository or ExamRepository(session)
        self.exam_graph_repository = exam_graph_repository or ExamGraphRepository(driver)
    
    async def sync_by_id(self, exam_id: str) -> bool:
        """
        Synchronize a single exam by ID.
        
        Args:
            exam_id: ID of the exam to synchronize
        
        Returns:
            True if synchronization was successful, False otherwise
        """
        try:
            # Get exam from SQL database
            exam = await self.exam_repository.get_by_id(exam_id)
            if not exam:
                logger.warning(f"Exam with ID {exam_id} not found in SQL database")
                return False
            
            # Convert to Neo4j node and save
            exam_node = self._convert_to_node(exam)
            result = await self.exam_graph_repository.create_or_update(exam_node)
            
            if result:
                # Synchronize key relationships
                await self._sync_relationships(exam)
                logger.info(f"Successfully synchronized exam {exam_id}")
            return True
            else:
                logger.error(f"Failed to synchronize exam {exam_id}")
                return False
            
        except Exception as e:
            logger.error(f"Error synchronizing exam {exam_id}: {str(e)}")
            return False
    
    async def _sync_relationships(self, exam: Dict[str, Any]) -> None:
        """
        Synchronize exam relationships with other nodes.
        
        Args:
            exam: The exam data dictionary
        """
        exam_id = exam.get("exam_id")
        
        # Sync ORGANIZED_BY relationship with management unit
        if "organizing_unit_id" in exam and exam["organizing_unit_id"]:
            await self.exam_graph_repository.add_organized_by_relationship(
                exam_id, 
                exam["organizing_unit_id"]
            )
        
        # If there are locations, sync HELD_AT relationships
        if "exams" in exam:  # This would contain location mappings if get_by_id returns that info
            for location_mapping in exam.get("exams", []):
                if "location_id" in location_mapping:
                    await self.exam_graph_repository.add_held_at_relationship(
                        exam_id, 
                        location_mapping["location_id"]
                    )
    
    async def sync_all(self, limit: Optional[int] = None, offset: int = 0) -> Tuple[int, int]:
        """
        Synchronize all exams from PostgreSQL to Neo4j.
        
        Args:
            limit: Optional maximum number of exams to synchronize
            offset: Optional offset for pagination
        
        Returns:
            Tuple containing counts of (successful, failed) synchronizations
        """
        success_count = 0
        failure_count = 0
        
        try:
            # Get all exams from SQL database
            exams, total = await self.exam_repository.get_all(skip=offset, limit=limit or 100)
            
            logger.info(f"Found {total} exams to synchronize")
            
            # Synchronize each exam
            for exam in exams:
                exam_id = exam.get("exam_id")
                if await self.sync_by_id(exam_id):
                    success_count += 1
                else:
                    failure_count += 1
                    
            logger.info(f"Exam synchronization complete. Success: {success_count}, Failed: {failure_count}")
            
        except Exception as e:
            logger.error(f"Error during exam synchronization: {str(e)}")
        
        return success_count, failure_count
    
    def _convert_to_node(self, exam: Dict[str, Any]) -> ExamNode:
        """
        Convert a SQL Exam model to an ExamNode.
        
        Args:
            exam: SQL Exam dictionary
        
        Returns:
            ExamNode instance ready for Neo4j
        """
        try:
            # Create the exam node
            exam_node = ExamNode(
                exam_id=exam["exam_id"],
                exam_name=exam["exam_name"],
                exam_type=exam["type_id"],
                start_date=exam["start_date"],
                end_date=exam["end_date"],
                scope=exam["scope"]
            )
            
            return exam_node
            
        except Exception as e:
            logger.error(f"Error converting exam to node: {str(e)}")
            # Return a basic node with just the ID as fallback
            return ExamNode(
                exam_id=exam["exam_id"],
                exam_name=exam.get("exam_name", f"Exam {exam['exam_id']}")
            ) 