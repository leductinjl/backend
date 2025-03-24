"""
Score Sync Service Module.

This module provides the ScoreSyncService class for synchronizing Score
data between PostgreSQL and Neo4j.
"""

import logging
from typing import Optional, Tuple, Dict, Any, Union

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
    
    async def sync_by_id(self, score_id: str, skip_relationships: bool = False) -> bool:
        """
        Synchronize a specific score by ID.
        
        Args:
            score_id: The ID of the score to sync
            skip_relationships: If True, only sync node without its relationships
            
        Returns:
            True if sync was successful, False otherwise
        """
        logger.info(f"Synchronizing score {score_id} (skip_relationships={skip_relationships})")
        
        try:
            # Get score from SQL database
            score = await self.sql_repository.get_by_id(score_id)
            if not score:
                logger.error(f"Score {score_id} not found in SQL database")
                return False
            
            # Convert to Neo4j format
            neo4j_data = self._convert_to_node(score)
            
            # Create or update node in Neo4j
            await self.graph_repository.create_or_update(neo4j_data)
            
            # Sync relationships if needed
            if not skip_relationships:
                await self.sync_relationships(score_id)
            
            return True
            
        except Exception as e:
            logger.error(f"Error syncing score {score_id}: {e}")
            return False
    
    async def sync_all(self, limit: Optional[int] = None, skip_relationships: bool = False) -> Union[Tuple[int, int], Dict[str, int]]:
        """
        Synchronize all scores.
        
        Args:
            limit: Optional limit on number of scores to sync
            skip_relationships: If True, only sync nodes without their relationships
            
        Returns:
            Tuple of (success_count, failed_count) or dict with success/failed counts
        """
        logger.info(f"Synchronizing all scores (skip_relationships={skip_relationships})")
        
        try:
            # Get all scores from SQL database
            scores, _ = await self.sql_repository.get_all(limit=limit)
            
            success_count = 0
            failed_count = 0
            
            for score in scores:
                try:
                    # Sync the score node - handle both ORM objects and dictionaries
                    score_id = score.score_id if hasattr(score, 'score_id') else score.get("score_id")
                    if not score_id:
                        logger.error(f"Missing score_id in score object: {score}")
                        failed_count += 1
                        continue
                        
                    await self.sync_by_id(score_id, skip_relationships=skip_relationships)
                    success_count += 1
                except Exception as e:
                    # Get score_id safely for logging
                    score_id = getattr(score, 'score_id', None) if hasattr(score, 'score_id') else score.get("score_id", "unknown")
                    logger.error(f"Error syncing score {score_id}: {e}")
                    failed_count += 1
            
            return (success_count, failed_count)
            
        except Exception as e:
            logger.error(f"Error during score synchronization: {e}")
            return {"success": 0, "failed": 0}
    
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
            score_value = score_data.get("score")
            subject_name = score_data.get("subject_name")
            exam_name = score_data.get("exam_name")
            
            # Create a meaningful name for the score
            name = None
            if score_value is not None and subject_name:
                name = f"{subject_name}: {score_value}"
            elif score_value is not None and exam_name:
                name = f"{exam_name}: {score_value}"
            else:
                name = f"Score {score_data['exam_score_id']}"
            
            # Create the score node with all available data
            score_node = ScoreNode(
                score_id=score_data["exam_score_id"],
                candidate_id=score_data.get("candidate_id"),
                subject_id=score_data.get("subject_id"),
                exam_id=score_data.get("exam_id"),
                score_value=score_value,
                status=score_data.get("status"),
                graded_by=score_data.get("graded_by"),
                graded_at=score_data.get("graded_at"),
                score_history=score_data.get("score_histories"),
                # Additional properties for relationships
                exam_name=exam_name,
                subject_name=subject_name,
                registration_status=score_data.get("registration_status", "REGISTERED"),
                registration_date=score_data.get("registration_date", ""),
                is_required=score_data.get("is_required", False),
                exam_date=score_data.get("exam_date", ""),
                name=name
            )
            
            return score_node
            
        except Exception as e:
            logger.error(f"Error converting score to node: {str(e)}")
            # Return a basic node with just the ID as fallback
            return ScoreNode(
                score_id=score_data["exam_score_id"]
            )
    
    async def sync_relationships(self, score_id: str) -> Dict[str, int]:
        """
        Synchronize relationships for a specific score.
        
        Args:
            score_id: ID of the score to synchronize relationships for
            
        Returns:
            Dictionary with counts of successfully synced relationships by type
        """
        logger.info(f"Synchronizing relationships for score {score_id}")
        
        relationship_counts = {
            "candidate": 0,
            "exam": 0,
            "subject": 0,
            "reviews": 0
        }
        
        try:
            # Get score from SQL database with full details
            score = await self.sql_repository.get_by_id(score_id)
            if not score:
                logger.error(f"Score {score_id} not found in SQL database")
                return relationship_counts
            
            # Sync ACHIEVED_BY relationship (score-candidate)
            if score.get("candidate_id"):
                candidate_id = score["candidate_id"]
                success = await self.graph_repository.add_achieved_by_relationship(score_id, candidate_id)
                if success:
                    relationship_counts["candidate"] += 1
            
            # Sync FOR_EXAM relationship (score-exam)
            if score.get("exam_id"):
                exam_id = score["exam_id"]
                success = await self.graph_repository.add_for_exam_relationship(score_id, exam_id)
                if success:
                    relationship_counts["exam"] += 1
            
            # Sync FOR_SUBJECT relationship (score-subject)
            if score.get("subject_id"):
                subject_id = score["subject_id"]
                success = await self.graph_repository.add_for_subject_relationship(score_id, subject_id)
                if success:
                    relationship_counts["subject"] += 1
            
            logger.info(f"Score relationship synchronization completed for {score_id}")
            return relationship_counts
            
        except Exception as e:
            logger.error(f"Error synchronizing relationships for score {score_id}: {e}")
            return relationship_counts 