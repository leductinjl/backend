"""
Recognition Graph Repository module.

This module provides methods for interacting with Recognition nodes in Neo4j.
"""

from app.domain.graph_models.recognition_node import RecognitionNode
from app.infrastructure.ontology.ontology import RELATIONSHIPS

class RecognitionGraphRepository:
    """
    Repository for managing Recognition nodes in Neo4j knowledge graph.
    
    This class provides methods to create, update, and query Recognition nodes
    and their relationships with other entities in the knowledge graph.
    """
    
    def __init__(self, neo4j_connection):
        """Initialize with Neo4j connection."""
        self.neo4j = neo4j_connection
    
    async def create_or_update(self, recognition):
        """
        Create or update a Recognition node in Neo4j.
        
        Args:
            recognition: RecognitionNode object or dictionary with recognition data
            
        Returns:
            bool: True if operation successful, False otherwise
        """
        try:
            # Ensure we have a dictionary
            params = recognition.to_dict() if hasattr(recognition, 'to_dict') else recognition
            
            # Execute Cypher query to create/update recognition
            query = RecognitionNode.create_query()
            result = await self.neo4j.execute_query(query, params)
            
            # Create relationships if possible
            if result and len(result) > 0:
                if hasattr(recognition, 'create_relationships_query'):
                    rel_query = recognition.create_relationships_query()
                    await self.neo4j.execute_query(rel_query, params)
                return True
            return False
        except Exception as e:
            print(f"Error creating/updating recognition in Neo4j: {e}")
            return False
    
    async def get_by_id(self, recognition_id):
        """
        Get a recognition by ID.
        
        Args:
            recognition_id: The ID of the recognition to retrieve
            
        Returns:
            RecognitionNode or None if not found
        """
        query = """
        MATCH (r:Recognition {recognition_id: $recognition_id})
        RETURN r
        """
        params = {"recognition_id": recognition_id}
        
        result = await self.neo4j.execute_query(query, params)
        if result and len(result) > 0:
            return RecognitionNode.from_record({"r": result[0][0]})
        return None
    
    async def delete(self, recognition_id):
        """
        Delete a recognition from Neo4j.
        
        Args:
            recognition_id: ID of the recognition to delete
            
        Returns:
            bool: True if successful, False otherwise
        """
        query = """
        MATCH (r:Recognition {recognition_id: $recognition_id})
        DETACH DELETE r
        """
        params = {"recognition_id": recognition_id}
        
        try:
            await self.neo4j.execute_query(query, params)
            return True
        except Exception as e:
            print(f"Error deleting recognition from Neo4j: {e}")
            return False
    
    async def get_by_candidate(self, candidate_id):
        """
        Get all recognitions received by a candidate.
        
        Args:
            candidate_id: ID of the candidate
            
        Returns:
            List of recognitions
        """
        query = """
        MATCH (c:Candidate {candidate_id: $candidate_id})-[:RECEIVES_RECOGNITION]->(r:Recognition)
        RETURN r
        """
        params = {"candidate_id": candidate_id}
        
        try:
            result = await self.neo4j.execute_query(query, params)
            recognitions = []
            
            for record in result:
                recognition = RecognitionNode.from_record({"r": record[0]})
                recognitions.append(recognition.to_dict())
            
            return recognitions
        except Exception as e:
            print(f"Error getting recognitions for candidate: {e}")
            return []
    
    async def get_by_exam(self, exam_id):
        """
        Get all recognitions awarded in a specific exam.
        
        Args:
            exam_id: ID of the exam
            
        Returns:
            List of recognitions
        """
        query = """
        MATCH (r:Recognition)-[:AWARDED_IN]->(e:Exam {exam_id: $exam_id})
        RETURN r
        """
        params = {"exam_id": exam_id}
        
        try:
            result = await self.neo4j.execute_query(query, params)
            recognitions = []
            
            for record in result:
                recognition = RecognitionNode.from_record({"r": record[0]})
                recognitions.append(recognition.to_dict())
            
            return recognitions
        except Exception as e:
            print(f"Error getting recognitions for exam: {e}")
            return []
    
    async def get_by_recognition_type(self, recognition_type):
        """
        Get all recognitions of a specific type.
        
        Args:
            recognition_type: Type of recognitions to retrieve
            
        Returns:
            List of recognitions
        """
        query = """
        MATCH (r:Recognition)
        WHERE r.recognition_type = $recognition_type
        RETURN r
        """
        params = {"recognition_type": recognition_type}
        
        try:
            result = await self.neo4j.execute_query(query, params)
            recognitions = []
            
            for record in result:
                recognition = RecognitionNode.from_record({"r": record[0]})
                recognitions.append(recognition.to_dict())
            
            return recognitions
        except Exception as e:
            print(f"Error getting recognitions by type: {e}")
            return []
    
    async def get_by_organization(self, organization):
        """
        Get all recognitions issued by a specific organization.
        
        Args:
            organization: Name of the issuing organization
            
        Returns:
            List of recognitions
        """
        query = """
        MATCH (r:Recognition)
        WHERE r.issuing_organization = $organization
        RETURN r
        """
        params = {"organization": organization}
        
        try:
            result = await self.neo4j.execute_query(query, params)
            recognitions = []
            
            for record in result:
                recognition = RecognitionNode.from_record({"r": record[0]})
                recognitions.append(recognition.to_dict())
            
            return recognitions
        except Exception as e:
            print(f"Error getting recognitions by organization: {e}")
            return []
    
    async def get_all_recognitions(self, limit=100):
        """
        Get all recognitions in the knowledge graph.
        
        Args:
            limit: Maximum number of recognitions to return
            
        Returns:
            List of recognitions
        """
        query = """
        MATCH (r:Recognition)
        RETURN r
        LIMIT $limit
        """
        params = {"limit": limit}
        
        try:
            result = await self.neo4j.execute_query(query, params)
            recognitions = []
            
            for record in result:
                recognition = RecognitionNode.from_record({"r": record[0]})
                recognitions.append(recognition.to_dict())
            
            return recognitions
        except Exception as e:
            print(f"Error getting all recognitions: {e}")
            return [] 