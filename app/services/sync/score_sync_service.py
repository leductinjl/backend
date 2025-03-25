"""
Score Sync Service Module.

This module provides the ScoreSyncService class for synchronizing Score
data between PostgreSQL and Neo4j.
"""

import logging
from typing import Optional, Tuple, Dict, Any, Union

from sqlalchemy.ext.asyncio import AsyncSession
from neo4j import AsyncDriver
from sqlalchemy import text

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
            # Get score from SQL database using direct SQL query
            sql_query = """
                SELECT 
                    es.exam_score_id, 
                    es.score, 
                    es.status, 
                    es.graded_by, 
                    es.graded_at,
                    es.score_metadata,
                    sub.subject_name,
                    ex.exam_name
                FROM 
                    exam_score es
                JOIN 
                    exam_subject esub ON es.exam_subject_id = esub.exam_subject_id
                JOIN 
                    exam ex ON esub.exam_id = ex.exam_id
                JOIN 
                    subject sub ON esub.subject_id = sub.subject_id
                WHERE 
                    es.exam_score_id = :score_id
            """
            
            result = await self.db_session.execute(text(sql_query), {"score_id": score_id})
            row = result.first()
            
            if not row:
                logger.error(f"Score {score_id} not found in SQL database")
                return False
                
            # Create a dictionary with the score data
            score_data = {
                "exam_score_id": row[0],
                "score": row[1],
                "status": row[2],
                "graded_by": row[3],
                "graded_at": row[4],
                "score_histories": row[5],
                "subject_name": row[6],
                "exam_name": row[7]
            }
            
            # Convert to Neo4j format
            neo4j_data = self._convert_to_node(score_data)
            
            # Create or update node in Neo4j
            result = await self.graph_repository.create_or_update(neo4j_data)
            
            logger.info(f"Successfully synchronized score node {score_id}")
            return result
            
        except Exception as e:
            logger.error(f"Error syncing score node {score_id}: {e}", exc_info=True)
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
            # Use direct SQL to get all scores with the necessary data in one query
            sql_query = """
                SELECT 
                    es.exam_score_id, 
                    es.score, 
                    es.status, 
                    es.graded_by, 
                    es.graded_at,
                    es.score_metadata,
                    sub.subject_name,
                    ex.exam_name,
                    ce.candidate_id,
                    sub.subject_id,
                    ex.exam_id
                FROM 
                    exam_score es
                JOIN 
                    exam_subject esub ON es.exam_subject_id = esub.exam_subject_id
                JOIN 
                    exam ex ON esub.exam_id = ex.exam_id
                JOIN 
                    subject sub ON esub.subject_id = sub.subject_id
                JOIN 
                    candidate_exam_subject ces ON es.candidate_exam_subject_id = ces.candidate_exam_subject_id
                JOIN 
                    candidate_exam ce ON ces.candidate_exam_id = ce.candidate_exam_id
            """
            
            if limit:
                sql_query += f" LIMIT {limit}"
                
            result = await self.db_session.execute(text(sql_query))
            scores = []
            
            for row in result.fetchall():
                # Convert empty dictionary to None for score_metadata
                score_metadata = row[5]
                if isinstance(score_metadata, dict) and not score_metadata:
                    score_metadata = None
                
                scores.append({
                    "exam_score_id": row[0],
                    "score": float(row[1]) if row[1] is not None else None,  # Convert Decimal to float
                    "status": row[2],
                    "graded_by": row[3],
                    "graded_at": row[4],
                    "score_histories": score_metadata,  # Use processed score_metadata
                    "subject_name": row[6],
                    "exam_name": row[7],
                    "candidate_id": row[8],
                    "subject_id": row[9],
                    "exam_id": row[10]
                })
            
            success_count = 0
            failed_count = 0
            
            for score in scores:
                try:
                    score_id = score["exam_score_id"]
                    if not score_id:
                        logger.error(f"Missing exam_score_id in score object: {score}")
                        failed_count += 1
                        continue
                        
                    # Create a more comprehensive ScoreNode with relationship info
                    score_node = ScoreNode(
                        score_id=score_id,
                        score_value=score.get("score"),
                        status=score.get("status"),
                        graded_by=score.get("graded_by"),
                        graded_at=score.get("graded_at"),
                        score_history=score.get("score_histories"),
                        name=f"{score.get('subject_name', '')} {score.get('score', '')}",
                        candidate_id=score.get("candidate_id"),
                        subject_id=score.get("subject_id"),
                        exam_id=score.get("exam_id"),
                        subject_name=score.get("subject_name"),
                        exam_name=score.get("exam_name")
                    )
                    
                    # Create or update node in Neo4j directly
                    # Include all needed properties in a single operation
                    query = """
                    MERGE (s:Score:OntologyInstance {score_id: $score_id})
                    ON CREATE SET
                        s.exam_score_id = $score_id,
                        s.name = $name,
                        s.score_value = $score_value,
                        s.status = $status,
                        s.graded_by = $graded_by,
                        s.graded_at = $graded_at,
                        s.score_history = $score_history,
                        s.created_at = datetime(),
                        s.candidate_id = $candidate_id,
                        s.subject_id = $subject_id,
                        s.exam_id = $exam_id,
                        s.subject_name = $subject_name,
                        s.exam_name = $exam_name
                    ON MATCH SET
                        s.exam_score_id = $score_id,
                        s.name = $name,
                        s.score_value = $score_value,
                        s.status = $status,
                        s.graded_by = $graded_by,
                        s.graded_at = $graded_at,
                        s.score_history = $score_history,
                        s.updated_at = datetime(),
                        s.candidate_id = $candidate_id,
                        s.subject_id = $subject_id,
                        s.exam_id = $exam_id,
                        s.subject_name = $subject_name,
                        s.exam_name = $exam_name
                    RETURN s
                    """
                    
                    params = score_node.to_dict()
                    # Ensure score_id is set as exam_score_id as well
                    params["exam_score_id"] = score_id
                    
                    # Convert empty dictionary to None for score_history
                    if isinstance(params.get("score_history"), dict) and not params["score_history"]:
                        params["score_history"] = None
                    
                    result = await self.neo4j_driver.execute_query(query, params)
                    if result and len(result) > 0:
                        # Create INSTANCE_OF relationship using the method from ScoreNode
                        instance_query = score_node.create_instance_of_relationship_query()
                        instance_params = {"score_id": score_id}
                        instance_result = await self.neo4j_driver.execute_query(instance_query, instance_params)
                        
                        if instance_result:
                            logger.debug(f"Created INSTANCE_OF relationship for score {score_id}")
                        else:
                            logger.warning(f"Failed to create INSTANCE_OF relationship for score {score_id}")
                        
                        success_count += 1
                        logger.debug(f"Successfully synchronized score node {score_id}")
                    else:
                        failed_count += 1
                        logger.warning(f"Failed to synchronize score node {score_id}")
                    
                except Exception as e:
                    score_id = score.get("exam_score_id", "unknown")
                    logger.error(f"Error syncing score node {score_id}: {e}", exc_info=True)
                    failed_count += 1
            
            logger.info(f"Completed synchronizing score nodes: {success_count} successful, {failed_count} failed")
            return (success_count, failed_count)
            
        except Exception as e:
            logger.error(f"Error during score nodes synchronization: {e}", exc_info=True)
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
            score_id = score_data.get("exam_score_id")
            # Convert Decimal to float for Neo4j compatibility
            score_value = float(score_data.get("score")) if score_data.get("score") is not None else None
            subject_name = score_data.get("subject_name")
            exam_name = score_data.get("exam_name")
            
            # Create a meaningful name for the score
            name = None
            if score_value is not None and subject_name:
                name = f"{subject_name}: {score_value}"
            elif score_value is not None and exam_name:
                name = f"{exam_name}: {score_value}"
            else:
                name = f"Score {score_id}"
            
            # Create the score node with basic node properties only
            score_node = ScoreNode(
                score_id=score_id,
                score_value=score_value,
                status=score_data.get("status"),
                graded_by=score_data.get("graded_by"),
                graded_at=score_data.get("graded_at"),
                score_history=score_data.get("score_histories") or score_data.get("score_metadata"),
                name=name
            )
            
            return score_node
            
        except Exception as e:
            logger.error(f"Error converting score to node: {str(e)}", exc_info=True)
            # Return a basic node with just the ID as fallback
            score_id = score_data.get("exam_score_id")
            if not score_id:
                raise ValueError(f"No exam_score_id found in score data: {score_data}")
                
            return ScoreNode(
                score_id=score_id
            )
    
    async def sync_relationship_by_id(self, score_id: str) -> Dict[str, int]:
        """
        Synchronize relationships for a specific score.
        
        Args:
            score_id: ID of the score to synchronize relationships for (exam_score_id in the database)
            
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
            # Use direct SQL query to get all related IDs in one query
            sql_query = """
                SELECT 
                    ce.candidate_id, 
                    esub.subject_id,
                    ex.exam_id
                FROM 
                    exam_score es
                JOIN 
                    candidate_exam_subject ces ON es.candidate_exam_subject_id = ces.candidate_exam_subject_id
                JOIN 
                    candidate_exam ce ON ces.candidate_exam_id = ce.candidate_exam_id
                JOIN 
                    exam_subject esub ON es.exam_subject_id = esub.exam_subject_id
                JOIN 
                    exam ex ON esub.exam_id = ex.exam_id
                WHERE 
                    es.exam_score_id = :score_id
            """
            
            result = await self.db_session.execute(text(sql_query), {"score_id": score_id})
            row = result.first()
            
            if not row:
                logger.error(f"Score {score_id} or its relationships not found in SQL database")
                return relationship_counts
                
            candidate_id, subject_id, exam_id = row
            
            # Sync ACHIEVED_BY relationship (score-candidate)
            if candidate_id:
                success = await self.graph_repository.add_achieved_by_relationship(score_id, candidate_id)
                if success:
                    relationship_counts["candidate"] += 1
                    logger.info(f"Added RECEIVES_SCORE relationship between candidate {candidate_id} and score {score_id}")
            
            # Sync FOR_EXAM relationship (score-exam)
            if exam_id:
                success = await self.graph_repository.add_for_exam_relationship(score_id, exam_id)
                if success:
                    relationship_counts["exam"] += 1
                    logger.info(f"Added IN_EXAM relationship between score {score_id} and exam {exam_id}")
            
            # Sync FOR_SUBJECT relationship (score-subject)
            if subject_id:
                success = await self.graph_repository.add_for_subject_relationship(score_id, subject_id)
                if success:
                    relationship_counts["subject"] += 1
                    logger.info(f"Added FOR_SUBJECT relationship between score {score_id} and subject {subject_id}")
            
            # Sync HAS_REVIEW relationships (score-review)
            review_query = """
                SELECT score_review_id 
                FROM score_review 
                WHERE score_id = :score_id
            """
            review_result = await self.db_session.execute(text(review_query), {"score_id": score_id})
            reviews = review_result.fetchall()
            
            for review_row in reviews:
                review_id = review_row[0]
                if review_id:
                    success = await self.graph_repository.add_has_review_relationship(score_id, review_id)
                    if success:
                        relationship_counts["reviews"] += 1
                        logger.info(f"Added HAS_REVIEW relationship between score {score_id} and review {review_id}")
            
            logger.info(f"Score relationship synchronization completed for {score_id}: {relationship_counts}")
            return relationship_counts
            
        except Exception as e:
            logger.error(f"Error synchronizing relationships for score {score_id}: {e}", exc_info=True)
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
            # Use direct SQL query to get all required IDs in one query
            
            # Get all score data with related entity IDs in a single query
            sql_query = """
                SELECT 
                    es.exam_score_id, 
                    ce.candidate_id, 
                    es.exam_subject_id,
                    sub.subject_id,
                    ex.exam_id
                FROM 
                    exam_score es
                JOIN 
                    candidate_exam_subject ces ON es.candidate_exam_subject_id = ces.candidate_exam_subject_id
                JOIN 
                    candidate_exam ce ON ces.candidate_exam_id = ce.candidate_exam_id
                JOIN 
                    exam_subject esub ON es.exam_subject_id = esub.exam_subject_id
                JOIN 
                    exam ex ON esub.exam_id = ex.exam_id
                JOIN 
                    subject sub ON esub.subject_id = sub.subject_id
            """
            if limit:
                sql_query += f" LIMIT {limit}"
            
            query = text(sql_query)
            result = await self.db_session.execute(query)
            
            # Extract score data from result
            score_data = []
            for row in result.fetchall():
                score_data.append({
                    "score_id": row[0],  # exam_score_id
                    "candidate_id": row[1],
                    "exam_subject_id": row[2],
                    "subject_id": row[3],
                    "exam_id": row[4]
                })
            
            total_scores = len(score_data)
            success_count = 0
            failure_count = 0
            
            # Aggregated counts for all relationship types
            relationship_counts = {
                "candidate": 0,
                "exam": 0,
                "subject": 0,
                "reviews": 0
            }
            
            # For each score, sync relationships directly
            for score in score_data:
                try:
                    score_id = score["score_id"]
                    
                    # Verify score exists in Neo4j
                    score_node = await self.graph_repository.get_by_id(score_id)
                    if not score_node:
                        logger.warning(f"Score {score_id} not found in Neo4j, skipping relationship sync")
                        failure_count += 1
                        continue
                    
                    # Track relationships for this score
                    score_relationships = {
                        "candidate": 0,
                        "exam": 0,
                        "subject": 0,
                        "reviews": 0
                    }
                    
                    # Sync ACHIEVED_BY relationship (score-candidate)
                    if score["candidate_id"]:
                        success = await self.graph_repository.add_achieved_by_relationship(score_id, score["candidate_id"])
                        if success:
                            score_relationships["candidate"] += 1
                            relationship_counts["candidate"] += 1
                            logger.debug(f"Added RECEIVES_SCORE relationship for candidate {score['candidate_id']}")
                    
                    # Sync FOR_EXAM relationship (score-exam)
                    if score["exam_id"]:
                        success = await self.graph_repository.add_for_exam_relationship(score_id, score["exam_id"])
                        if success:
                            score_relationships["exam"] += 1
                            relationship_counts["exam"] += 1
                            logger.debug(f"Added IN_EXAM relationship for exam {score['exam_id']}")
                    
                    # Sync FOR_SUBJECT relationship (score-subject)
                    if score["subject_id"]:
                        success = await self.graph_repository.add_for_subject_relationship(score_id, score["subject_id"])
                        if success:
                            score_relationships["subject"] += 1
                            relationship_counts["subject"] += 1
                            logger.debug(f"Added FOR_SUBJECT relationship for subject {score['subject_id']}")
                    
                    # Sync HAS_REVIEW relationships (score-review)
                    review_query = """
                        SELECT score_review_id 
                        FROM score_review 
                        WHERE score_id = :score_id
                    """
                    review_result = await self.db_session.execute(text(review_query), {"score_id": score_id})
                    reviews = review_result.fetchall()
                    
                    for review_row in reviews:
                        review_id = review_row[0]
                        if review_id:
                            success = await self.graph_repository.add_has_review_relationship(score_id, review_id)
                            if success:
                                score_relationships["reviews"] += 1
                                relationship_counts["reviews"] += 1
                                logger.debug(f"Added HAS_REVIEW relationship for review {review_id}")
                    
                    logger.info(f"Score {score_id} relationships: {score_relationships}")
                    success_count += 1
                    
                except Exception as e:
                    logger.error(f"Error synchronizing relationships for score {score.get('score_id', 'unknown')}: {e}")
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
            logger.error(f"Error during score relationships synchronization: {e}", exc_info=True)
            return {
                "total_scores": 0,
                "success": 0,
                "failed": 0,
                "error": str(e),
                "relationships": {}
            } 