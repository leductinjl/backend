"""
Score synchronization service module.

This module provides services for synchronizing score-related data between
PostgreSQL and Neo4j databases, including scores, score histories, and score reviews.
"""

import logging
import json
import traceback
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.sync.base_sync_service import BaseSyncService
from app.domain.graph_models.score_node import ScoreNode
from app.domain.graph_models.score_history_node import ScoreHistoryNode
from app.domain.graph_models.score_review_node import ScoreReviewNode
from app.graph_repositories.score_graph_repository import ScoreGraphRepository
from app.graph_repositories.score_history_graph_repository import ScoreHistoryGraphRepository
from app.graph_repositories.score_review_graph_repository import ScoreReviewGraphRepository
from app.repositories.repository_factory import RepositoryFactory

logger = logging.getLogger(__name__)

class ScoreSyncService(BaseSyncService):
    """
    Service for synchronizing score-related data between PostgreSQL and Neo4j.
    
    This service handles synchronization of scores, score histories, and score reviews.
    """
    
    def __init__(self, neo4j_connection, db_session: AsyncSession):
        """Initialize with Neo4j connection and SQLAlchemy session."""
        super().__init__(neo4j_connection, db_session)
        
        # Initialize score-related repositories
        self.score_graph_repo = ScoreGraphRepository(neo4j_connection)
        self.score_history_graph_repository = ScoreHistoryGraphRepository(neo4j_connection)
        self.score_review_graph_repository = ScoreReviewGraphRepository(neo4j_connection)
    
    async def sync_score(self, score_model):
        """
        Synchronize a score from PostgreSQL to Neo4j.
        
        Args:
            score_model: A Score SQLAlchemy model or dictionary
        
        Returns:
            bool: True if successful, False otherwise
        """
        score_id = None
        try:
            # Handle both dictionary and SQLAlchemy model
            if isinstance(score_model, dict):
                score_id = score_model.get("exam_score_id") or score_model.get("score_id")
                score_dict = score_model
            else:
                score_id = getattr(score_model, "exam_score_id", getattr(score_model, "score_id", None))
                score_dict = {
                    "score_id": score_id,
                    "candidate_exam_id": getattr(score_model, "candidate_exam_id", None),
                    "subject_id": getattr(score_model, "subject_id", None),
                    "score_value": getattr(score_model, "score_value", None),
                    "scoring_date": getattr(score_model, "scoring_date", None),
                    "max_score": getattr(score_model, "max_score", None),
                    "min_score": getattr(score_model, "min_score", None),
                    "passing_score": getattr(score_model, "passing_score", None),
                    "status": getattr(score_model, "status", None),
                    "scored_by": getattr(score_model, "scored_by", None)
                }
            
            await self._log_sync_start("score", score_id)
            
            # Create Neo4j node
            score_node = ScoreNode.from_dict(score_dict)
            
            # Create or update node in Neo4j
            query = score_node.create_query()
            logger.info(f"Executing Neo4j query for score {score_id}")
            await self._execute_neo4j_query(query, score_node.to_dict())
            
            # Create relationships if applicable
            if hasattr(score_node, "create_relationships_query") and callable(getattr(score_node, "create_relationships_query")):
                rel_query = score_node.create_relationships_query()
                if rel_query:
                    logger.info(f"Creating relationships for score {score_id}")
                    await self._execute_neo4j_query(rel_query, score_node.to_dict())
            
            await self._log_sync_success("score", score_id)
            return True
        except Exception as e:
            await self._log_sync_error("score", str(e), score_id)
            logger.error(traceback.format_exc())
            return False
    
    async def sync_subject_score(self, score_model):
        """
        Synchronize a subject score relationship from PostgreSQL to Neo4j.
        
        Args:
            score_model: A Score SQLAlchemy model or dictionary
        
        Returns:
            bool: True if successful, False otherwise
        """
        score_id = None
        try:
            # Handle both dictionary and SQLAlchemy model
            if isinstance(score_model, dict):
                score_id = score_model.get("exam_score_id") or score_model.get("score_id")
                subject_id = score_model.get("subject_id")
            else:
                score_id = getattr(score_model, "exam_score_id", getattr(score_model, "score_id", None))
                subject_id = score_model.subject_id
            
            if not subject_id:
                logger.warning(f"No subject ID found for score {score_id}, skipping relationship creation")
                return False
            
            await self._log_sync_start("subject-score relationship", score_id)
            
            # Create relationship between subject and score
            relationship_query = """
            MATCH (s:Subject {subject_id: $subject_id})
            MATCH (sc:Score {score_id: $score_id})
            MERGE (sc)-[r:BELONGS_TO_SUBJECT]->(s)
            RETURN r
            """
            
            params = {
                "subject_id": subject_id,
                "score_id": score_id
            }
            
            logger.info(f"Creating relationship between score {score_id} and subject {subject_id}")
            await self._execute_neo4j_query(relationship_query, params)
            
            await self._log_sync_success("subject-score relationship", score_id)
            return True
        except Exception as e:
            await self._log_sync_error("subject-score relationship", str(e), score_id)
            logger.error(traceback.format_exc())
            return False
    
    async def sync_score_history(self, history_model):
        """
        Synchronize a score history from PostgreSQL to Neo4j.
        
        Args:
            history_model: A ScoreHistory SQLAlchemy model or dictionary
        
        Returns:
            bool: True if successful, False otherwise
        """
        history_id = None
        try:
            # Handle both dictionary and SQLAlchemy model
            if isinstance(history_model, dict):
                history_id = history_model.get("history_id")
                history_dict = history_model
            else:
                history_id = history_model.history_id
                history_dict = {
                    "history_id": history_model.history_id,
                    "score_id": history_model.score_id,
                    "previous_score": history_model.previous_score,
                    "new_score": history_model.new_score,
                    "change_reason": history_model.change_reason,
                    "changed_by": history_model.changed_by,
                    "change_date": history_model.change_date,
                }
            
            await self._log_sync_start("score history", history_id)
            
            # Create Neo4j node
            history_node = ScoreHistoryNode.from_dict(history_dict)
            
            # Create or update node in Neo4j
            query = history_node.create_query()
            logger.info(f"Executing Neo4j query for score history {history_id}")
            await self._execute_neo4j_query(query, history_node.to_dict())
            
            # Create relationships if applicable
            if hasattr(history_node, "create_relationships_query") and callable(getattr(history_node, "create_relationships_query")):
                rel_query = history_node.create_relationships_query()
                if rel_query:
                    logger.info(f"Creating relationships for score history {history_id}")
                    await self._execute_neo4j_query(rel_query, history_node.to_dict())
            
            await self._log_sync_success("score history", history_id)
            return True
        except Exception as e:
            await self._log_sync_error("score history", str(e), history_id)
            logger.error(traceback.format_exc())
            return False
    
    async def sync_score_review(self, review_model):
        """
        Synchronize a score review from PostgreSQL to Neo4j.
        
        Args:
            review_model: A ScoreReview SQLAlchemy model or dictionary
        
        Returns:
            bool: True if successful, False otherwise
        """
        review_id = None
        try:
            # Handle both dictionary and SQLAlchemy model
            if isinstance(review_model, dict):
                review_id = review_model.get("review_id")
                review_dict = review_model
            else:
                review_id = review_model.review_id
                review_dict = {
                    "review_id": review_model.review_id,
                    "score_id": review_model.score_id,
                    "candidate_id": review_model.candidate_id,
                    "request_date": review_model.request_date,
                    "review_status": review_model.review_status,
                    "reviewer_comments": review_model.reviewer_comments,
                    "resolution_date": review_model.resolution_date,
                    "original_score": review_model.original_score,
                    "adjusted_score": review_model.adjusted_score,
                }
            
            await self._log_sync_start("score review", review_id)
            
            # Create Neo4j node
            review_node = ScoreReviewNode.from_dict(review_dict)
            
            # Create or update node in Neo4j
            query = review_node.create_query()
            logger.info(f"Executing Neo4j query for score review {review_id}")
            await self._execute_neo4j_query(query, review_node.to_dict())
            
            # Create relationships if applicable
            if hasattr(review_node, "create_relationships_query") and callable(getattr(review_node, "create_relationships_query")):
                rel_query = review_node.create_relationships_query()
                if rel_query:
                    logger.info(f"Creating relationships for score review {review_id}")
                    await self._execute_neo4j_query(rel_query, review_node.to_dict())
            
            await self._log_sync_success("score review", review_id)
            return True
        except Exception as e:
            await self._log_sync_error("score review", str(e), review_id)
            logger.error(traceback.format_exc())
            return False
    
    async def bulk_sync_scores(self):
        """
        Synchronize all scores from PostgreSQL to Neo4j.
        
        Returns:
            int: Number of successfully synchronized scores
        """
        await self._log_sync_start("score")
        try:
            # Get repository factory
            repo_factory = RepositoryFactory(self.db)
            score_repo = repo_factory.get_exam_score_repository()
            
            # Get all scores
            scores = await score_repo.get_all()
            logger.info(f"Found {len(scores)} scores to sync")
            
            # Sync each score
            success_count = 0
            for score in scores:
                if await self.sync_score(score):
                    success_count += 1
                    
                    # Also sync subject-score relationship if subject_id exists
                    if hasattr(score, "subject_id") and score.subject_id:
                        await self.sync_subject_score(score)
            
            await self._log_sync_success("score", count=success_count)
            return success_count
        except Exception as e:
            await self._log_sync_error("score", str(e))
            logger.error(traceback.format_exc())
            return 0
    
    async def bulk_sync_score_histories(self):
        """
        Synchronize all score histories from PostgreSQL to Neo4j.
        
        Returns:
            int: Number of successfully synchronized score histories
        """
        await self._log_sync_start("score history")
        try:
            # Get repository factory
            repo_factory = RepositoryFactory(self.db)
            history_repo = repo_factory.get_score_history_repository()
            
            # Get all score histories
            histories = await history_repo.get_all()
            logger.info(f"Found {len(histories)} score histories to sync")
            
            # Sync each score history
            success_count = 0
            for history in histories:
                if await self.sync_score_history(history):
                    success_count += 1
            
            await self._log_sync_success("score history", count=success_count)
            return success_count
        except Exception as e:
            await self._log_sync_error("score history", str(e))
            logger.error(traceback.format_exc())
            return 0
    
    async def bulk_sync_score_reviews(self):
        """
        Synchronize all score reviews from PostgreSQL to Neo4j.
        
        Returns:
            int: Number of successfully synchronized score reviews
        """
        await self._log_sync_start("score review")
        try:
            # Get repository factory
            repo_factory = RepositoryFactory(self.db)
            review_repo = repo_factory.get_score_review_repository()
            
            # Get all score reviews
            reviews = await review_repo.get_all()
            logger.info(f"Found {len(reviews)} score reviews to sync")
            
            # Sync each score review
            success_count = 0
            for review in reviews:
                if await self.sync_score_review(review):
                    success_count += 1
            
            await self._log_sync_success("score review", count=success_count)
            return success_count
        except Exception as e:
            await self._log_sync_error("score review", str(e))
            logger.error(traceback.format_exc())
            return 0 