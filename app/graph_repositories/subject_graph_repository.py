"""
Subject Graph Repository module.

This module provides methods for interacting with Subject nodes in Neo4j.
"""

import logging
from typing import Dict, List, Optional, Union

from app.domain.graph_models.subject_node import (
    SubjectNode, INSTANCE_OF_REL, FOR_SUBJECT_REL, 
    IN_EXAM_REL, INCLUDES_SUBJECT_REL
)

logger = logging.getLogger(__name__)

class SubjectGraphRepository:
    """
    Repository for managing Subject nodes in Neo4j knowledge graph.
    
    This class provides methods to create, update, and query Subject nodes
    and their relationships with other entities in the knowledge graph.
    """
    
    def __init__(self, neo4j_connection):
        """Initialize with Neo4j connection."""
        self.neo4j = neo4j_connection
    
    async def create_or_update(self, subject):
        """
        Create or update a Subject node in Neo4j.
        
        Args:
            subject: SubjectNode object or dictionary with subject data
            
        Returns:
            bool: True if operation successful, False otherwise
        """
        try:
            # Convert to SubjectNode if it's a dictionary
            if isinstance(subject, dict):
                subject = SubjectNode(
                    subject_id=subject.get("subject_id"),
                    subject_name=subject.get("subject_name"),
                    description=subject.get("description"),
                    subject_code=subject.get("subject_code")
                )
            
            # Get parameters for query
            params = subject.to_dict()
            
            # Execute Cypher query to create/update subject
            query = SubjectNode.create_query()
            result = await self.neo4j.execute_query(query, params)
            
            if result and len(result) > 0:
                # Create INSTANCE_OF relationship
                if hasattr(subject, 'create_instance_of_relationship_query'):
                    instance_query = subject.create_instance_of_relationship_query()
                    await self.neo4j.execute_query(instance_query, params)
                    logger.info(f"Created INSTANCE_OF relationship for subject {subject.subject_id}")
                
                logger.info(f"Successfully created/updated subject {subject.subject_id} in Neo4j")
                return True
            
            logger.error(f"Failed to create/update subject {subject.subject_id} in Neo4j")
            return False
        except Exception as e:
            logger.error(f"Error creating/updating subject in Neo4j: {e}", exc_info=True)
            return False
    
    async def get_by_id(self, subject_id):
        """
        Get a subject by ID.
        
        Args:
            subject_id: The ID of the subject to retrieve
            
        Returns:
            SubjectNode or None if not found
        """
        query = """
        MATCH (s:Subject {subject_id: $subject_id})
        RETURN s
        """
        params = {"subject_id": subject_id}
        
        try:
            result = await self.neo4j.execute_query(query, params)
            if result and len(result) > 0:
                logger.info(f"Successfully retrieved subject {subject_id}")
                return SubjectNode.from_record({"s": result[0][0]})
            
            logger.info(f"No subject found with ID {subject_id}")
            return None
        except Exception as e:
            logger.error(f"Error retrieving subject by ID {subject_id}: {e}")
            return None
    
    async def delete(self, subject_id):
        """
        Delete a subject from Neo4j.
        
        Args:
            subject_id: ID of the subject to delete
            
        Returns:
            bool: True if successful, False otherwise
        """
        query = """
        MATCH (s:Subject {subject_id: $subject_id})
        DETACH DELETE s
        """
        params = {"subject_id": subject_id}
        
        try:
            await self.neo4j.execute_query(query, params)
            logger.info(f"Successfully deleted subject {subject_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting subject {subject_id} from Neo4j: {e}")
            return False
    
    async def get_exams(self, subject_id):
        """
        Get all exams that include this subject.
        
        Args:
            subject_id: ID of the subject
            
        Returns:
            List of exams with their relationship details
        """
        query = f"""
        MATCH (e:Exam)-[r:{INCLUDES_SUBJECT_REL}]->(s:Subject {{subject_id: $subject_id}})
        RETURN e, r.exam_date as exam_date, r.duration_minutes as duration_minutes
        """
        params = {"subject_id": subject_id}
        
        try:
            result = await self.neo4j.execute_query(query, params)
            exams = []
            
            for record in result:
                exam = record[0]
                exam_date = record[1]
                duration_minutes = record[2]
                
                exams.append({
                    "exam_id": exam["exam_id"],
                    "exam_name": exam["exam_name"],
                    "exam_date": exam_date,
                    "duration_minutes": duration_minutes
                })
            
            logger.info(f"Retrieved {len(exams)} exams for subject {subject_id}")
            return exams
        except Exception as e:
            logger.error(f"Error getting exams for subject {subject_id}: {e}")
            return []
    
    async def get_scores(self, subject_id):
        """
        Get all scores for this subject.
        
        Args:
            subject_id: ID of the subject
            
        Returns:
            List of scores with candidate and exam details
        """
        query = f"""
        MATCH (s:Score)-[:{FOR_SUBJECT_REL}]->(subj:Subject {{subject_id: $subject_id}})
        MATCH (c:Candidate)-[:RECEIVES_SCORE]->(s)
        MATCH (s)-[:{IN_EXAM_REL}]->(e:Exam)
        RETURN c, e, s.score_value as score, s.graded_at as score_date
        """
        params = {"subject_id": subject_id}
        
        try:
            result = await self.neo4j.execute_query(query, params)
            scores = []
            
            for record in result:
                candidate = record[0]
                exam = record[1]
                score = record[2]
                score_date = record[3]
                
                scores.append({
                    "candidate_id": candidate["candidate_id"],
                    "candidate_name": candidate["full_name"],
                    "exam_id": exam["exam_id"],
                    "exam_name": exam["exam_name"],
                    "score": score,
                    "score_date": score_date
                })
            
            logger.info(f"Retrieved {len(scores)} scores for subject {subject_id}")
            return scores
        except Exception as e:
            logger.error(f"Error getting scores for subject {subject_id}: {e}")
            return []
    
    async def get_all_subjects(self):
        """
        Get all subjects.
        
        Returns:
            List of SubjectNode objects
        """
        query = """
        MATCH (s:Subject)
        RETURN s
        """
        
        try:
            result = await self.neo4j.execute_query(query)
            subjects = [SubjectNode.from_record({"s": record[0]}) for record in result]
            logger.info(f"Retrieved {len(subjects)} subjects in total")
            return subjects
        except Exception as e:
            logger.error(f"Error retrieving all subjects: {e}")
            return [] 