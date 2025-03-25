"""
Score Review Sync Service Module.

This module provides the ScoreReviewSyncService class for synchronizing Score Review
data between PostgreSQL and Neo4j.
"""

import logging
from typing import Optional, Tuple, Dict, Any, Union

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
        sql_repository: Optional[ScoreReviewRepository] = None,
        graph_repository: Optional[ScoreReviewGraphRepository] = None
    ):
        """
        Initialize the ScoreReviewSyncService.
        
        Args:
            session: SQLAlchemy async session
            driver: Neo4j async driver
            sql_repository: Optional ScoreReviewRepository instance
            graph_repository: Optional ScoreReviewGraphRepository instance
        """
        super().__init__(session, driver, sql_repository, graph_repository)
        self.db_session = session
        self.neo4j_driver = driver
        self.sql_repository = sql_repository or ScoreReviewRepository(session)
        self.graph_repository = graph_repository or ScoreReviewGraphRepository(driver)
    
    async def sync_node_by_id(self, review_id: str) -> bool:
        """
        Synchronize a specific score review node by ID, only creating the node and INSTANCE_OF relationship.
        
        Args:
            review_id: The ID of the score review to sync (score_review_id in database)
            
        Returns:
            True if sync was successful, False otherwise
        """
        logger.info(f"Synchronizing score review node {review_id}")
        
        try:
            # Get score review from SQL database using score_review_id
            review = await self.sql_repository.get_by_id(review_id)
            if not review:
                logger.error(f"Score review {review_id} not found in SQL database")
                return False
            
            # Convert to Neo4j format
            neo4j_data = self._convert_to_node(review)
            
            # Create or update node in Neo4j
            result = await self.graph_repository.create_or_update(neo4j_data)
            
            logger.info(f"Successfully synchronized score review node {review_id}")
            return result
            
        except Exception as e:
            logger.error(f"Error syncing score review node {review_id}: {e}")
            return False
    
    async def sync_all_nodes(self, limit: Optional[int] = None) -> Tuple[int, int]:
        """
        Synchronize all score review nodes, without their relationships (except INSTANCE_OF).
        
        Args:
            limit: Optional limit on number of score reviews to sync
            
        Returns:
            Tuple of (success_count, failed_count)
        """
        logger.info(f"Synchronizing all score review nodes (limit={limit})")
        
        try:
            # Get all score reviews from SQL database
            reviews, _ = await self.sql_repository.get_all(limit=limit)
            
            success_count = 0
            failed_count = 0
            
            for review in reviews:
                try:
                    # Sync only the score review node - handle both ORM objects and dictionaries
                    review_id = review.review_id if hasattr(review, 'review_id') else review.get("review_id")
                    # Check for score_review_id if review_id is not found
                    if not review_id:
                        review_id = review.score_review_id if hasattr(review, 'score_review_id') else review.get("score_review_id")
                    
                    if not review_id:
                        logger.error(f"Missing review_id/score_review_id in review object: {review}")
                        failed_count += 1
                        continue
                        
                    if await self.sync_node_by_id(review_id):
                        success_count += 1
                    else:
                        failed_count += 1
                except Exception as e:
                    # Get review_id safely for logging
                    review_id = getattr(review, 'review_id', None) if hasattr(review, 'review_id') else review.get("review_id", None)
                    if not review_id:
                        review_id = getattr(review, 'score_review_id', None) if hasattr(review, 'score_review_id') else review.get("score_review_id", "unknown")
                    logger.error(f"Error syncing score review node {review_id}: {e}")
                    failed_count += 1
            
            logger.info(f"Completed synchronizing score review nodes: {success_count} successful, {failed_count} failed")
            return (success_count, failed_count)
            
        except Exception as e:
            logger.error(f"Error during score review nodes synchronization: {e}")
            return (0, 0)
    
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
            
            # Create the node with only basic node properties
            score_review_node = ScoreReviewNode(
                review_id=review_id,
                review_name=review_name,
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

    async def sync_relationship_by_id(self, review_id: str) -> Dict[str, int]:
        """
        Synchronize relationships for a specific score review.
        
        Args:
            review_id: ID of the score review to synchronize relationships for
            
        Returns:
            Dictionary with counts of successfully synced relationships by type
        """
        logger.info(f"Synchronizing relationships for score review {review_id}")
        
        # Check if score review node exists before syncing relationships
        review_node = await self.graph_repository.get_by_id(review_id)
        if not review_node:
            logger.warning(f"Score review node {review_id} not found in Neo4j, skipping relationship sync")
            return {
                "error": "Score review node not found in Neo4j",
                "score": 0,
                "candidate": 0,
                "subject": 0,
                "exam": 0
            }
        
        relationship_counts = {
            "score": 0,
            "candidate": 0,
            "subject": 0,
            "exam": 0
        }
        
        try:
            # Get score review from SQL database with full details
            review = await self.sql_repository.get_by_id(review_id)
            if not review:
                logger.error(f"Score review {review_id} not found in SQL database")
                return relationship_counts
            
            # Sync FOR_SCORE relationship (review-score)
            if review.get("score_id"):
                score_id = review["score_id"]
                success = await self.graph_repository.add_for_score_relationship(review_id, score_id)
                if success:
                    relationship_counts["score"] += 1
            
            # Sync REQUESTED_BY relationship (review-candidate)
            if review.get("candidate_id"):
                candidate_id = review["candidate_id"]
                success = await self.graph_repository.add_requested_by_relationship(review_id, candidate_id)
                if success:
                    relationship_counts["candidate"] += 1
            
            # Sync FOR_SUBJECT relationship if we have subject data
            if review.get("subject_id"):
                subject_id = review["subject_id"]
                success = await self.graph_repository.add_for_subject_relationship(review_id, subject_id)
                if success:
                    relationship_counts["subject"] += 1
            
            logger.info(f"Score review relationship synchronization completed for {review_id}: {relationship_counts}")
            return relationship_counts
            
        except Exception as e:
            logger.error(f"Error synchronizing relationships for score review {review_id}: {e}")
            return relationship_counts
            
    async def sync_all_relationships(self, limit: Optional[int] = None) -> Dict[str, int]:
        """
        Synchronize relationships for all score reviews.
        
        Args:
            limit: Optional maximum number of score reviews to process
            
        Returns:
            Dictionary with counts of synced relationships by type
        """
        logger.info(f"Synchronizing relationships for all score reviews (limit={limit})")
        
        try:
            # Get all score reviews from SQL database
            reviews, total_count = await self.sql_repository.get_all(limit=limit)
            
            total_reviews = len(reviews)
            success_count = 0
            failure_count = 0
            
            # Aggregated counts for all relationship types
            relationship_counts = {
                "score": 0,
                "candidate": 0,
                "subject": 0,
                "exam": 0
            }
            
            # For each score review, sync relationships
            for review in reviews:
                try:
                    # Get review_id safely - handle both ORM objects and dictionaries
                    review_id = review.review_id if hasattr(review, 'review_id') else review.get("review_id")
                    if not review_id:
                        logger.error(f"Missing review_id in review object: {review}")
                        failure_count += 1
                        continue
                    
                    # Verify score review exists in Neo4j
                    review_node = await self.graph_repository.get_by_id(review_id)
                    if not review_node:
                        logger.warning(f"Score review {review_id} not found in Neo4j, skipping relationship sync")
                        failure_count += 1
                        continue
                    
                    # Sync relationships for this score review
                    results = await self.sync_relationship_by_id(review_id)
                    
                    # Update aggregated counts
                    for key, value in results.items():
                        if key in relationship_counts:
                            relationship_counts[key] += value
                    
                    success_count += 1
                    
                except Exception as e:
                    # Get review_id safely for logging
                    review_id = getattr(review, 'review_id', None) if hasattr(review, 'review_id') else review.get("review_id", "unknown")
                    logger.error(f"Error synchronizing relationships for score review {review_id}: {e}")
                    failure_count += 1
            
            # Prepare final result
            result = {
                "total_reviews": total_reviews,
                "success": success_count,
                "failed": failure_count,
                "relationships": relationship_counts
            }
            
            logger.info(f"Completed synchronizing relationships for all score reviews: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error during score review relationships synchronization: {e}")
            return {
                "total_reviews": 0,
                "success": 0,
                "failed": 0,
                "error": str(e),
                "relationships": {}
            } 