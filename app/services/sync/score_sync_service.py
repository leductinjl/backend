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
        sql_repository: Optional[ExamScoreRepository] = None,
        graph_repository: Optional[ScoreGraphRepository] = None
    ):
        """
        Initialize the ScoreSyncService.
        
        Args:
            session: SQLAlchemy async session
            driver: Neo4j async driver
            sql_repository: Optional ExamScoreRepository instance
            graph_repository: Optional ScoreGraphRepository instance
        """
        super().__init__(session, driver, sql_repository, graph_repository)
        self.db_session = session
        self.neo4j_driver = driver
        self.sql_repository = sql_repository or ExamScoreRepository(session)
        self.graph_repository = graph_repository or ScoreGraphRepository(driver)
    
    async def sync_node_by_id(self, score_id: str) -> bool:
        """
        Synchronize a specific score node by ID, only creating the node and INSTANCE_OF relationship.
        
        Args:
            score_id: The ID of the score to sync (exam_score_id in database)
            
        Returns:
            True if sync was successful, False otherwise
        """
        logger.info(f"Synchronizing score node {score_id}")
        
        try:
            # Get score from SQL database using exam_score_id
            score = await self.sql_repository.get_by_id(score_id)
            if not score:
                logger.error(f"Score {score_id} not found in SQL database")
                return False
            
            # Convert to Neo4j format
            neo4j_data = self._convert_to_node(score)
            
            # Create or update node in Neo4j
            result = await self.graph_repository.create_or_update(neo4j_data)
            
            logger.info(f"Successfully synchronized score node {score_id}")
            return result
            
        except Exception as e:
            logger.error(f"Error syncing score node {score_id}: {e}")
            return False
    
    async def sync_all_nodes(self, limit: Optional[int] = None) -> Tuple[int, int]:
        """
        Synchronize all score nodes, without their relationships (except INSTANCE_OF).
        
        Args:
            limit: Optional limit on number of scores to sync
            
        Returns:
            Tuple of (success_count, failed_count)
        """
        logger.info(f"Synchronizing all score nodes (limit={limit})")
        
        try:
            # Get all scores from SQL database
            scores, _ = await self.sql_repository.get_all(limit=limit)
            
            success_count = 0
            failed_count = 0
            
            for score in scores:
                try:
                    # Sync only the score node - handle both ORM objects and dictionaries
                    score_id = score.score_id if hasattr(score, 'score_id') else score.get("score_id")
                    # Check for exam_score_id if score_id is not found
                    if not score_id:
                        score_id = score.exam_score_id if hasattr(score, 'exam_score_id') else score.get("exam_score_id")
                    
                    if not score_id:
                        logger.error(f"Missing score_id/exam_score_id in score object: {score}")
                        failed_count += 1
                        continue
                        
                    if await self.sync_node_by_id(score_id):
                        success_count += 1
                    else:
                        failed_count += 1
                except Exception as e:
                    # Get score_id safely for logging
                    score_id = getattr(score, 'score_id', None) if hasattr(score, 'score_id') else score.get("score_id", None)
                    if not score_id:
                        score_id = getattr(score, 'exam_score_id', None) if hasattr(score, 'exam_score_id') else score.get("exam_score_id", "unknown")
                    logger.error(f"Error syncing score node {score_id}: {e}")
                    failed_count += 1
            
            logger.info(f"Completed synchronizing score nodes: {success_count} successful, {failed_count} failed")
            return (success_count, failed_count)
            
        except Exception as e:
            logger.error(f"Error during score nodes synchronization: {e}")
            return (0, 0)
    
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
            
            # Create the score node with basic node properties only
            score_node = ScoreNode(
                score_id=score_data["exam_score_id"],
                score_value=score_value,
                status=score_data.get("status"),
                graded_by=score_data.get("graded_by"),
                graded_at=score_data.get("graded_at"),
                score_history=score_data.get("score_histories"),
                name=name
            )
            
            return score_node
            
        except Exception as e:
            logger.error(f"Error converting score to node: {str(e)}")
            # Return a basic node with just the ID as fallback
            return ScoreNode(
                score_id=score_data["exam_score_id"]
            )
    
    async def sync_relationship_by_id(self, score_id: str) -> Dict[str, int]:
        """
        Synchronize relationships for a specific score.
        
        Args:
            score_id: ID of the score to synchronize relationships for
            
        Returns:
            Dictionary with counts of successfully synced relationships by type
        """
        logger.info(f"Synchronizing relationships for score {score_id}")
        
        # Check if score node exists before syncing relationships
        score_node = await self.graph_repository.get_by_id(score_id)
        if not score_node:
            logger.warning(f"Score node {score_id} not found in Neo4j, skipping relationship sync")
            return {
                "error": "Score node not found in Neo4j",
                "candidate": 0,
                "exam": 0,
                "subject": 0,
                "reviews": 0
            }
        
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
            
            logger.info(f"Score relationship synchronization completed for {score_id}: {relationship_counts}")
            return relationship_counts
            
        except Exception as e:
            logger.error(f"Error synchronizing relationships for score {score_id}: {e}")
            return relationship_counts
            
    async def sync_all_relationships(self, limit: Optional[int] = None) -> Dict[str, int]:
        """
        Synchronize relationships for all scores.
        
        Args:
            limit: Optional maximum number of scores to process
            
        Returns:
            Dictionary with counts of synced relationships by type
        """
        logger.info(f"Synchronizing relationships for all scores (limit={limit})")
        
        try:
            # Get all scores from SQL database
            scores, total_count = await self.sql_repository.get_all(limit=limit)
            
            total_scores = len(scores)
            success_count = 0
            failure_count = 0
            
            # Aggregated counts for all relationship types
            relationship_counts = {
                "candidate": 0,
                "exam": 0,
                "subject": 0,
                "reviews": 0
            }
            
            # For each score, sync relationships
            for score in scores:
                try:
                    # Get score_id safely - handle both ORM objects and dictionaries
                    score_id = score.score_id if hasattr(score, 'score_id') else score.get("score_id")
                    if not score_id:
                        logger.error(f"Missing score_id in score object: {score}")
                        failure_count += 1
                        continue
                    
                    # Verify score exists in Neo4j
                    score_node = await self.graph_repository.get_by_id(score_id)
                    if not score_node:
                        logger.warning(f"Score {score_id} not found in Neo4j, skipping relationship sync")
                        failure_count += 1
                        continue
                    
                    # Sync relationships for this score
                    results = await self.sync_relationship_by_id(score_id)
                    
                    # Update aggregated counts
                    for key, value in results.items():
                        if key in relationship_counts:
                            relationship_counts[key] += value
                    
                    success_count += 1
                    
                except Exception as e:
                    # Get score_id safely for logging
                    score_id = getattr(score, 'score_id', None) if hasattr(score, 'score_id') else score.get("score_id", "unknown")
                    logger.error(f"Error synchronizing relationships for score {score_id}: {e}")
                    failure_count += 1
            
            # Prepare final result
            result = {
                "total_scores": total_scores,
                "success": success_count,
                "failed": failure_count,
                "relationships": relationship_counts
            }
            
            logger.info(f"Completed synchronizing relationships for all scores: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error during score relationships synchronization: {e}")
            return {
                "total_scores": 0,
                "success": 0,
                "failed": 0,
                "error": str(e),
                "relationships": {}
            } 