"""
Exam graph repository module.

This module defines the ExamGraphRepository class for interacting with Exam nodes in Neo4j.
"""

from app.domain.graph_models.exam_node import ExamNode
from app.infrastructure.ontology.ontology import RELATIONSHIPS
import logging

logger = logging.getLogger(__name__)

class ExamGraphRepository:
    """
    Repository for managing Exam nodes in Neo4j.
    """
    
    def __init__(self, neo4j_connection):
        """Initialize with Neo4j connection."""
        self.neo4j = neo4j_connection
    
    async def create_or_update(self, exam):
        """
        Create or update an Exam node in Neo4j.
        
        Args:
            exam: The exam object containing exam data
            
        Returns:
            The created or updated ExamNode
        """
        try:
            # Create or update exam node
            query = ExamNode.create_query()
            params = exam.to_dict() if hasattr(exam, 'to_dict') else exam
            
            result = await self.neo4j.execute_query(query, params)
            if result and len(result) > 0:
                # Create IS_A relationship with Exam class
                await self._create_is_a_relationship(params["exam_id"])
                logger.info(f"Successfully created/updated exam {params['exam_id']} in Neo4j")
                return True
            return False
        except Exception as e:
            # Log the error
            logger.error(f"Error creating/updating exam in Neo4j: {e}", exc_info=True)
            return False
    
    async def _create_is_a_relationship(self, exam_id):
        """
        Create INSTANCE_OF relationship between the exam and Exam class node.
        
        Args:
            exam_id: ID of the exam node
        """
        try:
            query = """
            MATCH (instance:Exam:OntologyInstance {exam_id: $exam_id})
            MATCH (class:Exam:OntologyClass {id: 'exam-class'})
            MERGE (instance)-[r:INSTANCE_OF]->(class)
            RETURN r
            """
            params = {
                "exam_id": exam_id
            }
            await self.neo4j.execute_query(query, params)
            logger.info(f"Created INSTANCE_OF relationship for exam {exam_id}")
            return True
        except Exception as e:
            logger.error(f"Error creating INSTANCE_OF relationship for exam {exam_id}: {e}")
            return False
    
    async def get_by_id(self, exam_id):
        """
        Get an exam by ID.
        
        Args:
            exam_id: The ID of the exam to retrieve
            
        Returns:
            ExamNode or None if not found
        """
        query = """
        MATCH (e:Exam {exam_id: $exam_id})
        RETURN e
        """
        params = {"exam_id": exam_id}
        
        result = await self.neo4j.execute_query(query, params)
        if result and len(result) > 0:
            return ExamNode.from_record({"e": result[0][0]})
        return None
    
    async def delete(self, exam_id):
        """
        Delete an exam from Neo4j.
        
        Args:
            exam_id: ID of the exam to delete
            
        Returns:
            True if successful, False otherwise
        """
        query = """
        MATCH (e:Exam {exam_id: $exam_id})
        DETACH DELETE e
        """
        params = {"exam_id": exam_id}
        
        try:
            await self.neo4j.execute_query(query, params)
            return True
        except Exception as e:
            print(f"Error deleting exam from Neo4j: {e}")
            return False
    
    async def add_includes_subject_relationship(self, exam_id, subject_id, relationship_data=None):
        """
        Create a relationship between an exam and a subject.
        
        Args:
            exam_id: ID of the exam
            subject_id: ID of the subject
            relationship_data: Additional data for the relationship
            
        Returns:
            True if successful, False otherwise
        """
        query = RELATIONSHIPS["INCLUDES_SUBJECT"]["create_query"]
        
        params = {
            "exam_id": exam_id,
            "subject_id": subject_id,
            "exam_date": relationship_data.get("exam_date") if relationship_data else None,
            "duration_minutes": relationship_data.get("duration_minutes") if relationship_data else None
        }
        
        try:
            await self.neo4j.execute_query(query, params)
            return True
        except Exception as e:
            print(f"Error adding INCLUDES_SUBJECT relationship: {e}")
            return False
    
    async def add_held_at_relationship(self, exam_id, location_id):
        """
        Create a relationship between an exam and a location.
        
        Args:
            exam_id: ID of the exam
            location_id: ID of the location
            
        Returns:
            True if successful, False otherwise
        """
        query = RELATIONSHIPS["HELD_AT"]["create_query"]
        
        params = {
            "exam_id": exam_id,
            "location_id": location_id
        }
        
        try:
            await self.neo4j.execute_query(query, params)
            return True
        except Exception as e:
            print(f"Error adding HELD_AT relationship: {e}")
            return False 