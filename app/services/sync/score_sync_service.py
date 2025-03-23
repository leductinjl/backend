"""
Score Sync Service Module.

This module provides the ScoreSyncService class for synchronizing Score
data between PostgreSQL and Neo4j.
"""

import logging
from typing import Optional, Tuple, Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession
from neo4j import AsyncDriver

from app.domain.models.exam_score import ExamScore
from app.domain.graph_models.score_node import ScoreNode
from app.repositories.exam_score_repository import ExamScoreRepository
from app.graph_repositories.score_graph_repository import ScoreGraphRepository
from app.services.sync.base_sync_service import BaseSyncService

logger = logging.getLogger(__name__)

class ScoreSyncService(BaseSyncService):
    """
    Service for synchronizing Score data between PostgreSQL and Neo4j.
    
    This service implements the BaseSyncService abstract class and provides
    methods for synchronizing individual scores by ID and synchronizing
    all scores in the database.
    """
    
    def __init__(
        self,
        session: AsyncSession,
        driver: AsyncDriver,
        score_repository: Optional[ExamScoreRepository] = None,
        score_graph_repository: Optional[ScoreGraphRepository] = None
    ):
        """
        Initialize the ScoreSyncService.
        
        Args:
            session: SQLAlchemy async session
            driver: Neo4j async driver
            score_repository: Optional ExamScoreRepository instance
            score_graph_repository: Optional ScoreGraphRepository instance
        """
        super().__init__(session, driver)
        self.db_session = session
        self.neo4j_driver = driver
        self.sql_repository = score_repository or ExamScoreRepository(session)
        self.graph_repository = score_graph_repository or ScoreGraphRepository(driver)
    
    async def sync_by_id(self, score_id: str) -> bool:
        """
        Synchronize a single score by ID.
        
        Args:
            score_id: ID of the score to synchronize
            
        Returns:
            True if synchronization was successful, False otherwise
        """
        try:
            # Get score from SQL database
            score = await self.sql_repository.get_by_id(score_id)
            if not score:
                logger.warning(f"Score with ID {score_id} not found in SQL database")
                return False
            
            # Convert to Neo4j node and save
            score_node = self._convert_to_node(score)
            result = await self.graph_repository.create_or_update(score_node)
            
            if result:
                logger.info(f"Successfully synchronized score {score_id}")
                return True
            else:
                logger.error(f"Failed to synchronize score {score_id}")
                return False
            
        except Exception as e:
            logger.error(f"Error synchronizing score {score_id}: {str(e)}")
            return False
    
    async def sync_all(self, limit: Optional[int] = None, offset: int = 0) -> Tuple[int, int]:
        """
        Synchronize all scores from PostgreSQL to Neo4j.
        
        Args:
            limit: Optional maximum number of scores to synchronize
            offset: Optional offset for pagination
            
        Returns:
            Tuple containing counts of (successful, failed) synchronizations
        """
        success_count = 0
        failure_count = 0
        
        try:
            # Get all scores from SQL database with pagination
            scores, total = await self.sql_repository.get_all(skip=offset, limit=limit or 100)
            
            logger.info(f"Found {total} scores to synchronize")
            
            # Synchronize each score
            for score in scores:
                if await self.sync_by_id(score["exam_score_id"]):
                    success_count += 1
                else:
                    failure_count += 1
                    
            logger.info(f"Score synchronization complete. Success: {success_count}, Failed: {failure_count}")
            
        except Exception as e:
            logger.error(f"Error during score synchronization: {str(e)}")
        
        return success_count, failure_count
    
    def _convert_to_node(self, score_data: Dict[str, Any]) -> ScoreNode:
        """
        Convert SQL score data to a ScoreNode.
        
        Args:
            score_data: Dictionary containing score data from SQL database
            
        Returns:
            ScoreNode instance ready for Neo4j
        """
        try:
            # Extract the required fields from the score data
            # The score data should already include related entities like candidate, exam, and subject
            score_node = ScoreNode(
                score_id=score_data["exam_score_id"],
                candidate_id=score_data.get("candidate_id"),
                subject_id=score_data.get("subject_id"),
                exam_id=score_data.get("exam_id"),
                score_value=score_data.get("score"),
                status=score_data.get("status"),
                graded_by=score_data.get("graded_by"),
                graded_at=score_data.get("graded_at"),
                score_history=score_data.get("score_histories"),
                # Additional properties for relationships
                exam_name=score_data.get("exam_name"),
                subject_name=score_data.get("subject_name"),
                registration_status=None,  # Need to be obtained from candidate_exam_subject if needed
                registration_date=None,    # Need to be obtained from candidate_exam_subject if needed
                is_required=None,          # Need to be obtained from candidate_exam_subject if needed
                exam_date=None             # Need to be obtained from candidate_exam_subject if needed
            )
            
            return score_node
            
        except Exception as e:
            logger.error(f"Error converting score to node: {str(e)}")
            # Return a basic node with just the ID as fallback
            return ScoreNode(
                score_id=score_data["exam_score_id"]
            ) 