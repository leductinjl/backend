"""
Exam Sync Service Module.

This module provides the ExamSyncService class for synchronizing Exam
data between PostgreSQL and Neo4j.
"""

import logging
from typing import Optional, Tuple, List, Dict, Any, Union

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
    
    async def sync_by_id(self, exam_id: str, skip_relationships: bool = False) -> bool:
        """
        Synchronize a specific exam by ID.
        
        Args:
            exam_id: The ID of the exam to sync
            skip_relationships: If True, only sync node without its relationships
            
        Returns:
            True if sync was successful, False otherwise
        """
        logger.info(f"Synchronizing exam {exam_id} (skip_relationships={skip_relationships})")
        
        try:
            # Get exam from SQL database
            exam = await self.exam_repository.get_by_id(exam_id)
            if not exam:
                logger.error(f"Exam {exam_id} not found in SQL database")
                return False
            
            # Convert to Neo4j format
            neo4j_data = self._convert_to_node(exam)
            
            # Create or update node in Neo4j
            await self.exam_graph_repository.create_or_update(neo4j_data)
            
            # Sync relationships if needed
            if not skip_relationships:
                await self.sync_relationships(exam_id)
            
            return True
            
        except Exception as e:
            logger.error(f"Error syncing exam {exam_id}: {e}")
            return False
    
    async def sync_relationships(self, exam_id: str) -> Dict[str, int]:
        """
        Synchronize relationships for a specific exam.
        
        Args:
            exam_id: ID of the exam to synchronize relationships for
            
        Returns:
            Dictionary with counts of successfully synced relationships by type
        """
        logger.info(f"Synchronizing relationships for exam {exam_id}")
        
        relationship_counts = {
            "management_units": 0,
            "locations": 0,
            "schedules": 0,
            "subjects": 0
        }
        
        try:
            # Get exam from SQL database with details
            exam = await self.exam_repository.get_by_id(exam_id)
            if not exam:
                logger.error(f"Exam {exam_id} not found in SQL database")
                return relationship_counts
            
            # Sync internal relationships
            await self._sync_relationships(exam)
            
            # Count relationships
            if "organizing_unit_id" in exam and exam["organizing_unit_id"]:
                relationship_counts["management_units"] += 1
            
            if "exams" in exam:
                relationship_counts["locations"] = len(exam.get("exams", []))
            
            logger.info(f"Exam relationship synchronization completed for {exam_id}")
            return relationship_counts
            
        except Exception as e:
            logger.error(f"Error synchronizing relationships for exam {exam_id}: {e}")
            return relationship_counts
    
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
    
    async def sync_all(self, limit: Optional[int] = None, skip_relationships: bool = False) -> Union[Tuple[int, int], Dict[str, int]]:
        """
        Synchronize all exams.
        
        Args:
            limit: Optional limit on number of exams to sync
            skip_relationships: If True, only sync nodes without their relationships
            
        Returns:
            Tuple of (success_count, failed_count) or dict with success/failed counts
        """
        logger.info(f"Synchronizing all exams (skip_relationships={skip_relationships})")
        
        try:
            # Get all exams from SQL database
            exams, _ = await self.exam_repository.get_all(limit=limit)
            
            success_count = 0
            failed_count = 0
            
            for exam in exams:
                try:
                    # Sync the exam node
                    exam_id = exam.exam_id if hasattr(exam, 'exam_id') else exam.get("exam_id")
                    if not exam_id:
                        logger.error(f"Missing exam_id in exam object: {exam}")
                        failed_count += 1
                        continue
                        
                    await self.sync_by_id(exam_id, skip_relationships=skip_relationships)
                    success_count += 1
                except Exception as e:
                    # Get exam_id safely for logging
                    exam_id = getattr(exam, 'exam_id', None) if hasattr(exam, 'exam_id') else exam.get("exam_id", "unknown")
                    logger.error(f"Error syncing exam {exam_id}: {e}")
                    failed_count += 1
            
            return (success_count, failed_count)
            
        except Exception as e:
            logger.error(f"Error during exam synchronization: {e}")
            return {"success": 0, "failed": 0}
    
    def _convert_to_node(self, exam: Dict[str, Any]) -> ExamNode:
        """
        Convert a SQL Exam model or dictionary to an ExamNode.
        
        Args:
            exam: SQL Exam dictionary or ORM object
        
        Returns:
            ExamNode instance ready for Neo4j
        """
        try:
            # Extract fields safely supporting both dict and ORM objects
            if isinstance(exam, dict):
                exam_id = exam.get("exam_id")
                exam_name = exam.get("exam_name", f"Exam {exam_id}")
                exam_type = exam.get("type_id")
                start_date = exam.get("start_date")
                end_date = exam.get("end_date")
                scope = exam.get("scope")
            else:
                # It's an ORM object
                exam_id = exam.exam_id
                exam_name = getattr(exam, "exam_name", f"Exam {exam_id}")
                exam_type = getattr(exam, "type_id", None)
                start_date = getattr(exam, "start_date", None)
                end_date = getattr(exam, "end_date", None)
                scope = getattr(exam, "scope", None)
            
            # Create the exam node
            exam_node = ExamNode(
                exam_id=exam_id,
                exam_name=exam_name,
                exam_type=exam_type,
                start_date=start_date,
                end_date=end_date,
                scope=scope
            )
            
            return exam_node
            
        except Exception as e:
            logger.error(f"Error converting exam to node: {str(e)}")
            # Get exam_id safely for error recovery
            exam_id = exam.get("exam_id") if isinstance(exam, dict) else getattr(exam, "exam_id", "unknown")
            exam_name = f"Exam {exam_id}"
            if isinstance(exam, dict) and "exam_name" in exam:
                exam_name = exam["exam_name"]
            elif hasattr(exam, "exam_name"):
                exam_name = exam.exam_name
                
            # Return a basic node with just the ID as fallback
            return ExamNode(
                exam_id=exam_id,
                exam_name=exam_name
            ) 