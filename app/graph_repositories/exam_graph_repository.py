"""
Exam graph repository module.

This module defines the ExamGraphRepository class for interacting with Exam nodes in Neo4j.
"""

from app.domain.graph_models.exam_node import ExamNode, INSTANCE_OF_REL
from app.infrastructure.ontology.ontology import RELATIONSHIPS
import logging

logger = logging.getLogger(__name__)

# Import specific relationships
FOLLOWS_SCHEDULE_REL = RELATIONSHIPS["FOLLOWS_SCHEDULE"]["type"]
ORGANIZED_BY_REL = RELATIONSHIPS["ORGANIZED_BY"]["type"]

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
                # Create INSTANCE_OF relationship
                if hasattr(exam, 'create_instance_of_relationship_query'):
                    instance_of_query = exam.create_instance_of_relationship_query()
                    await self.neo4j.execute_query(instance_of_query, params)
                else:
                    # Fallback to repository method for backward compatibility
                    await self._create_instance_of_relationship(params["exam_id"])
                
                logger.info(f"Successfully created/updated exam {params['exam_id']} in Neo4j")
                return True
            return False
        except Exception as e:
            # Log the error
            logger.error(f"Error creating/updating exam in Neo4j: {e}", exc_info=True)
            return False
    
    async def _create_instance_of_relationship(self, exam_id):
        """
        Create INSTANCE_OF relationship between the exam and Exam class node.
        
        Args:
            exam_id: ID of the exam node
        """
        try:
            query = f"""
            MATCH (instance:Exam:OntologyInstance {{exam_id: $exam_id}})
            MATCH (class:OntologyClass {{id: 'exam-class'}})
            MERGE (instance)-[r:{INSTANCE_OF_REL}]->(class)
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
    
    async def add_follows_schedule_relationship(self, exam_id, schedule_id):
        """
        Create a relationship between an exam and an exam schedule.
        
        Args:
            exam_id: ID of the exam
            schedule_id: ID of the exam schedule
            
        Returns:
            True if successful, False otherwise
        """
        query = RELATIONSHIPS["FOLLOWS_SCHEDULE"]["create_query"]
        
        params = {
            "exam_id": exam_id,
            "schedule_id": schedule_id
        }
        
        try:
            await self.neo4j.execute_query(query, params)
            logger.info(f"Added FOLLOWS_SCHEDULE relationship between exam {exam_id} and schedule {schedule_id}")
            return True
        except Exception as e:
            logger.error(f"Error adding FOLLOWS_SCHEDULE relationship: {e}")
            return False
    
    async def add_organized_by_relationship(self, exam_id, unit_id, relationship_data=None):
        """
        Create a relationship between an exam and a management unit.
        
        Args:
            exam_id: ID of the exam
            unit_id: ID of the management unit
            relationship_data: Additional data for the relationship
            
        Returns:
            True if successful, False otherwise
        """
        query = RELATIONSHIPS["ORGANIZED_BY"]["create_query"]
        
        # Set default values if not provided
        relationship_data = relationship_data or {}
        params = {
            "exam_id": exam_id,
            "unit_id": unit_id,
            "is_primary": relationship_data.get("is_primary", True),
            "organization_date": relationship_data.get("organization_date"),
            "role": relationship_data.get("role", "Primary"),
            "status": relationship_data.get("status", "Active")
        }
        
        try:
            await self.neo4j.execute_query(query, params)
            logger.info(f"Added ORGANIZED_BY relationship between exam {exam_id} and unit {unit_id}")
            return True
        except Exception as e:
            logger.error(f"Error adding ORGANIZED_BY relationship: {e}")
            return False 