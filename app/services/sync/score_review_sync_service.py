"""
Score Review Sync Service Module.

This module provides the ScoreReviewSyncService class for synchronizing Score Review
data between PostgreSQL and Neo4j.
"""

import logging
from typing import Optional, Tuple, Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession
from neo4j import AsyncDriver

from app.domain.models.score_review import ScoreReview
from app.domain.graph_models.score_review_node import ScoreReviewNode
from app.repositories.score_review_repository import ScoreReviewRepository
from app.graph_repositories.score_review_graph_repository import ScoreReviewGraphRepository
from app.services.sync.base_sync_service import BaseSyncService

logger = logging.getLogger(__name__)

class ScoreReviewSyncService(BaseSyncService):
    """
    Service for synchronizing ScoreReview data between PostgreSQL and Neo4j.
    
    This service implements the BaseSyncService abstract class and provides
    methods for synchronizing individual score reviews by ID and synchronizing
    all score reviews in the database.
    """
    
    def __init__(
        self,
        session: AsyncSession,
        driver: AsyncDriver,
        score_review_repository: Optional[ScoreReviewRepository] = None,
        score_review_graph_repository: Optional[ScoreReviewGraphRepository] = None
    ):
        """
        Initialize the ScoreReviewSyncService.
        
        Args:
            session: SQLAlchemy async session
            driver: Neo4j async driver
            score_review_repository: Optional ScoreReviewRepository instance
            score_review_graph_repository: Optional ScoreReviewGraphRepository instance
        """
        super().__init__(session, driver)
        self.db_session = session
        self.neo4j_driver = driver
        self.sql_repository = score_review_repository or ScoreReviewRepository(session)
        self.graph_repository = score_review_graph_repository or ScoreReviewGraphRepository(driver)
    
    async def sync_by_id(self, score_review_id: str) -> bool:
        """
        Synchronize a single score review by ID.
        
        Args:
            score_review_id: ID of the score review to synchronize
            
        Returns:
            True if synchronization was successful, False otherwise
        """
        try:
            # Get score review from SQL database
            score_review = await self.sql_repository.get_by_id(score_review_id)
            if not score_review:
                logger.warning(f"ScoreReview with ID {score_review_id} not found in SQL database")
                return False
            
            # Convert to Neo4j node and save
            score_review_node = self._convert_to_node(score_review)
            result = await self.graph_repository.create_or_update(score_review_node)
            
            if result:
                logger.info(f"Successfully synchronized score review {score_review_id}")
                return True
            else:
                logger.error(f"Failed to synchronize score review {score_review_id}")
                return False
            
        except Exception as e:
            logger.error(f"Error synchronizing score review {score_review_id}: {str(e)}")
            return False
    
    async def sync_all(self, limit: Optional[int] = None, offset: int = 0) -> Tuple[int, int]:
        """
        Synchronize all score reviews from PostgreSQL to Neo4j.
        
        Args:
            limit: Optional maximum number of score reviews to synchronize
            offset: Optional offset for pagination
            
        Returns:
            Tuple containing counts of (successful, failed) synchronizations
        """
        success_count = 0
        failure_count = 0
        
        try:
            # Get all score reviews from SQL database with pagination
            score_reviews, total = await self.sql_repository.get_all(skip=offset, limit=limit or 100)
            
            logger.info(f"Found {total} score reviews to synchronize")
            
            # Synchronize each score review
            for score_review in score_reviews:
                if await self.sync_by_id(score_review["score_review_id"]):
                    success_count += 1
                else:
                    failure_count += 1
                    
            logger.info(f"Score review synchronization complete. Success: {success_count}, Failed: {failure_count}")
            
        except Exception as e:
            logger.error(f"Error during score review synchronization: {str(e)}")
        
        return success_count, failure_count
    
    def _convert_to_node(self, score_review_data: Dict[str, Any]) -> ScoreReviewNode:
        """
        Convert SQL score review data to a ScoreReviewNode.
        
        Args:
            score_review_data: Dictionary containing score review data from SQL database
            
        Returns:
            ScoreReviewNode instance ready for Neo4j
        """
        try:
            # Extract the required fields from the score review data
            review_id = score_review_data["score_review_id"]
            review_name = f"Score Review {review_id}"
            
            # Get IDs for relationships
            score_id = score_review_data.get("score_id")
            
            # Get candidate, subject, and exam IDs from the related score data if available
            candidate_id = None
            subject_id = None
            exam_id = None
            
            if "exam_score" in score_review_data:
                candidate_id = score_review_data["exam_score"].get("candidate_id")
                subject_id = score_review_data["exam_score"].get("subject_id")
                exam_id = score_review_data["exam_score"].get("exam_id")
            
            if "candidate" in score_review_data:
                candidate_id = score_review_data["candidate"].get("candidate_id")
            
            if "subject" in score_review_data:
                subject_id = score_review_data["subject"].get("subject_id")
            
            if "exam" in score_review_data:
                exam_id = score_review_data["exam"].get("exam_id")
            
            # Create the node
            score_review_node = ScoreReviewNode(
                review_id=review_id,
                review_name=review_name,
                score_id=score_id,
                candidate_id=candidate_id,
                subject_id=subject_id,
                exam_id=exam_id,
                status=score_review_data.get("review_status"),
                request_date=score_review_data.get("request_date"),
                resolution_date=score_review_data.get("review_date"),
                old_score=score_review_data.get("original_score"),
                new_score=score_review_data.get("reviewed_score"),
                reviewer=None,  # No reviewer field in the model
                reason=score_review_data.get("review_result"),
                additional_info=score_review_data.get("additional_info")
            )
            
            return score_review_node
            
        except Exception as e:
            logger.error(f"Error converting score review to node: {str(e)}")
            # Return a basic node with just the ID as fallback
            return ScoreReviewNode(
                review_id=score_review_data["score_review_id"],
                review_name=f"Score Review {score_review_data['score_review_id']}"
            ) 