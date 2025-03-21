"""
Subject Graph Repository module.

This module provides methods for interacting with Subject nodes in Neo4j.
"""

from app.domain.graph_models.subject_node import SubjectNode
from app.infrastructure.ontology.ontology import RELATIONSHIPS
import logging

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
            # Ensure we have a dictionary
            params = subject.to_dict() if hasattr(subject, 'to_dict') else subject
            
            # Execute Cypher query to create/update subject
            query = SubjectNode.create_query()
            result = await self.neo4j.execute_query(query, params)
            
            if result and len(result) > 0:
                # Create IS_A relationship with Subject class
                await self._create_is_a_relationship(params["subject_id"])
                logger.info(f"Successfully created/updated subject {params['subject_id']} in Neo4j")
                return True
            return False
        except Exception as e:
            logger.error(f"Error creating/updating subject in Neo4j: {e}", exc_info=True)
            return False
            
    async def _create_is_a_relationship(self, subject_id):
        """
        Create INSTANCE_OF relationship between Subject node and Subject class node.
        
        Args:
            subject_id: ID of the subject node
        """
        try:
            query = """
            MATCH (instance:Subject:OntologyInstance {subject_id: $subject_id})
            MATCH (class:Subject:OntologyClass {id: 'subject-class'})
            MERGE (instance)-[r:INSTANCE_OF]->(class)
            RETURN r
            """
            params = {
                "subject_id": subject_id
            }
            await self.neo4j.execute_query(query, params)
            logger.info(f"Created INSTANCE_OF relationship for subject {subject_id}")
            return True
        except Exception as e:
            logger.error(f"Error creating INSTANCE_OF relationship for subject {subject_id}: {e}")
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
        
        result = await self.neo4j.execute_query(query, params)
        if result and len(result) > 0:
            return SubjectNode.from_record({"s": result[0][0]})
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
            return True
        except Exception as e:
            print(f"Error deleting subject from Neo4j: {e}")
            return False
    
    async def get_exams(self, subject_id):
        """
        Get all exams that include this subject.
        
        Args:
            subject_id: ID of the subject
            
        Returns:
            List of exams with their relationship details
        """
        query = """
        MATCH (e:Exam)-[r:INCLUDES_SUBJECT]->(s:Subject {subject_id: $subject_id})
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
            
            return exams
        except Exception as e:
            print(f"Error getting exams for subject: {e}")
            return []
    
    async def get_scores(self, subject_id):
        """
        Get all scores for this subject.
        
        Args:
            subject_id: ID of the subject
            
        Returns:
            List of scores with candidate and exam details
        """
        query = """
        MATCH (c:Candidate)-[r:SCORED_IN]->(s:Subject {subject_id: $subject_id})
        MATCH (e:Exam)-[:INCLUDES_SUBJECT]->(s)
        RETURN c, e, r.score as score, r.score_date as score_date
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
            
            return scores
        except Exception as e:
            print(f"Error getting scores for subject: {e}")
            return [] 