"""
Score Graph Repository module.

This module provides methods for interacting with Score nodes in Neo4j.
"""

import logging
from typing import Dict, List, Optional, Union

from app.domain.graph_models.score_node import (
    ScoreNode, INSTANCE_OF_REL, RECEIVES_SCORE_REL, FOR_SUBJECT_REL, IN_EXAM_REL
)
from app.infrastructure.ontology.ontology import RELATIONSHIPS

logger = logging.getLogger(__name__)

class ScoreGraphRepository:
    """
    Repository for managing Score nodes in Neo4j knowledge graph.
    
    This class provides methods to create, update, and query Score nodes
    and their relationships with other entities in the knowledge graph.
    """
    
    def __init__(self, neo4j_connection):
        """Initialize with Neo4j connection."""
        self.neo4j = neo4j_connection
    
    async def create_or_update(self, score):
        """
        Create or update a Score node in Neo4j.
        
        Args:
            score: ScoreNode object or dictionary with score data
            
        Returns:
            bool: True if operation successful, False otherwise
        """
        try:
            # Convert to ScoreNode if it's a dictionary
            if isinstance(score, dict):
                score = ScoreNode(
                    score_id=score.get("score_id"),
                    candidate_id=score.get("candidate_id"),
                    subject_id=score.get("subject_id"),
                    exam_id=score.get("exam_id"),
                    score_value=score.get("score_value"),
                    status=score.get("status"),
                    graded_by=score.get("graded_by"),
                    graded_at=score.get("graded_at"),
                    score_history=score.get("score_history"),
                    exam_name=score.get("exam_name"),
                    subject_name=score.get("subject_name"),
                    registration_status=score.get("registration_status"),
                    registration_date=score.get("registration_date"),
                    is_required=score.get("is_required"),
                    exam_date=score.get("exam_date")
                )
            
            # Get parameters for query
            params = score.to_dict()
            
            # Execute Cypher query to create/update score
            query = ScoreNode.create_query()
            result = await self.neo4j.execute_query(query, params)
            
            if result and len(result) > 0:
                # Create relationships with other nodes
                rel_query = ScoreNode.create_relationships_query()
                await self.neo4j.execute_query(rel_query, params)
                
                # Create INSTANCE_OF relationship if the method exists
                if hasattr(score, 'create_instance_of_relationship_query'):
                    instance_query = score.create_instance_of_relationship_query()
                    await self.neo4j.execute_query(instance_query, params)
                    logger.info(f"Created INSTANCE_OF relationship for score {score.score_id}")
                
                logger.info(f"Successfully created/updated score {score.score_id} in Neo4j")
                return True
            else:
                logger.error(f"Failed to create/update score in Neo4j")
                return False
        except Exception as e:
            logger.error(f"Error creating/updating score in Neo4j: {e}")
            return False
    
    async def get_by_id(self, score_id):
        """
        Get a score by ID.
        
        Args:
            score_id: The ID of the score to retrieve
            
        Returns:
            ScoreNode or None if not found
        """
        query = """
        MATCH (s:Score {score_id: $score_id})
        RETURN s
        """
        params = {"score_id": score_id}
        
        try:
            result = await self.neo4j.execute_query(query, params)
            if result and len(result) > 0:
                return ScoreNode.from_record({"s": result[0][0]})
            logger.info(f"No score found with ID {score_id}")
            return None
        except Exception as e:
            logger.error(f"Error retrieving score by ID {score_id}: {e}")
            return None
    
    async def delete(self, score_id):
        """
        Delete a score from Neo4j.
        
        Args:
            score_id: ID of the score to delete
            
        Returns:
            bool: True if successful, False otherwise
        """
        query = """
        MATCH (s:Score {score_id: $score_id})
        DETACH DELETE s
        """
        params = {"score_id": score_id}
        
        try:
            await self.neo4j.execute_query(query, params)
            logger.info(f"Successfully deleted score {score_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting score {score_id} from Neo4j: {e}")
            return False
    
    async def get_candidate_scores(self, candidate_id):
        """
        Get all scores for a specific candidate.
        
        Args:
            candidate_id: ID of the candidate
            
        Returns:
            List of scores with subject and exam details
        """
        query = f"""
        MATCH (c:Candidate {{candidate_id: $candidate_id}})-[:{RECEIVES_SCORE_REL}]->(s:Score)
        MATCH (s)-[:{FOR_SUBJECT_REL}]->(subj:Subject)
        MATCH (s)-[:{IN_EXAM_REL}]->(e:Exam)
        RETURN s, subj, e
        """
        params = {"candidate_id": candidate_id}
        
        try:
            result = await self.neo4j.execute_query(query, params)
            scores = []
            
            for record in result:
                score = record[0]
                subject = record[1]
                exam = record[2]
                
                scores.append({
                    "score_id": score["score_id"],
                    "score_value": score["score_value"],
                    "score_date": score.get("score_date"),
                    "status": score.get("status"),
                    "subject_id": subject["subject_id"],
                    "subject_name": subject["subject_name"],
                    "exam_id": exam["exam_id"],
                    "exam_name": exam["exam_name"]
                })
            
            logger.info(f"Retrieved {len(scores)} scores for candidate {candidate_id}")
            return scores
        except Exception as e:
            logger.error(f"Error getting scores for candidate {candidate_id}: {e}")
            return []
    
    async def get_exam_scores(self, exam_id):
        """
        Get all scores for a specific exam.
        
        Args:
            exam_id: ID of the exam
            
        Returns:
            List of scores with candidate and subject details
        """
        query = f"""
        MATCH (e:Exam {{exam_id: $exam_id}})<-[:{IN_EXAM_REL}]-(s:Score)
        MATCH (c:Candidate)-[:{RECEIVES_SCORE_REL}]->(s)
        MATCH (s)-[:{FOR_SUBJECT_REL}]->(subj:Subject)
        RETURN s, c, subj
        """
        params = {"exam_id": exam_id}
        
        try:
            result = await self.neo4j.execute_query(query, params)
            scores = []
            
            for record in result:
                score = record[0]
                candidate = record[1]
                subject = record[2]
                
                scores.append({
                    "score_id": score["score_id"],
                    "score_value": score["score_value"],
                    "score_date": score.get("score_date"),
                    "status": score.get("status"),
                    "candidate_id": candidate["candidate_id"],
                    "candidate_name": candidate["full_name"],
                    "subject_id": subject["subject_id"],
                    "subject_name": subject["subject_name"]
                })
            
            logger.info(f"Retrieved {len(scores)} scores for exam {exam_id}")
            return scores
        except Exception as e:
            logger.error(f"Error getting scores for exam {exam_id}: {e}")
            return []
    
    async def get_subject_scores(self, subject_id):
        """
        Get all scores for a specific subject.
        
        Args:
            subject_id: ID of the subject
            
        Returns:
            List of scores with candidate and exam details
        """
        query = f"""
        MATCH (subj:Subject {{subject_id: $subject_id}})<-[:{FOR_SUBJECT_REL}]-(s:Score)
        MATCH (c:Candidate)-[:{RECEIVES_SCORE_REL}]->(s)
        MATCH (s)-[:{IN_EXAM_REL}]->(e:Exam)
        RETURN s, c, e
        """
        params = {"subject_id": subject_id}
        
        try:
            result = await self.neo4j.execute_query(query, params)
            scores = []
            
            for record in result:
                score = record[0]
                candidate = record[1]
                exam = record[2]
                
                scores.append({
                    "score_id": score["score_id"],
                    "score_value": score["score_value"],
                    "score_date": score.get("score_date"),
                    "status": score.get("status"),
                    "candidate_id": candidate["candidate_id"],
                    "candidate_name": candidate["full_name"],
                    "exam_id": exam["exam_id"],
                    "exam_name": exam["exam_name"]
                })
            
            logger.info(f"Retrieved {len(scores)} scores for subject {subject_id}")
            return scores
        except Exception as e:
            logger.error(f"Error getting scores for subject {subject_id}: {e}")
            return []
    
    async def get_school_average_scores(self, school_id, exam_id=None):
        """
        Get average scores for students from a specific school.
        
        Args:
            school_id: ID of the school
            exam_id: Optional ID of a specific exam to filter by
            
        Returns:
            Dictionary with subject IDs as keys and average scores as values
        """
        query_params = f"""
        MATCH (school:School {{school_id: $school_id}})
        MATCH (school)<-[:STUDIES_AT]-(c:Candidate)
        MATCH (c)-[:{RECEIVES_SCORE_REL}]->(s:Score)
        MATCH (s)-[:{FOR_SUBJECT_REL}]->(subj:Subject)
        """
        
        if exam_id:
            query_params += f"""
            MATCH (s)-[:{IN_EXAM_REL}]->(e:Exam {{exam_id: $exam_id}})
            """
        
        query_params += """
        RETURN subj.subject_id as subject_id, subj.subject_name as subject_name, 
               AVG(s.score_value) as avg_score,
               COUNT(c) as student_count
        """
        
        params = {"school_id": school_id}
        if exam_id:
            params["exam_id"] = exam_id
        
        try:
            result = await self.neo4j.execute_query(query_params, params)
            averages = []
            
            for record in result:
                subject_id = record[0]
                subject_name = record[1]
                avg_score = record[2]
                student_count = record[3]
                
                averages.append({
                    "subject_id": subject_id,
                    "subject_name": subject_name,
                    "average_score": round(avg_score, 2),
                    "student_count": student_count
                })
            
            exam_filter = f" for exam {exam_id}" if exam_id else ""
            logger.info(f"Retrieved average scores for {len(averages)} subjects from school {school_id}{exam_filter}")
            return averages
        except Exception as e:
            logger.error(f"Error getting average scores for school {school_id}: {e}")
            return [] 