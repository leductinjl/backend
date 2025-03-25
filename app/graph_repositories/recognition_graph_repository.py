"""
Recognition Graph Repository module.

This module provides methods for interacting with Recognition nodes in Neo4j.
"""

import logging
from typing import Dict, List, Optional, Union

from app.domain.graph_models.recognition_node import (
    RecognitionNode, INSTANCE_OF_REL, RECEIVES_RECOGNITION_REL, RECOGNITION_FOR_EXAM_REL
)
from app.infrastructure.ontology.ontology import RELATIONSHIPS

logger = logging.getLogger(__name__)

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
            # Convert to RecognitionNode if it's a dictionary
            if isinstance(recognition, dict):
                recognition = RecognitionNode(
                    recognition_id=recognition.get("recognition_id"),
                    recognition_name=recognition.get("recognition_name"),
                    recognition_type=recognition.get("recognition_type"),
                    recognition_date=recognition.get("recognition_date"),
                    description=recognition.get("description"),
                    candidate_id=recognition.get("candidate_id"),
                    exam_id=recognition.get("exam_id"),
                    recognition_image_url=recognition.get("recognition_image_url"),
                    additional_info=recognition.get("additional_info")
                )
            
            # Get parameters for query
            params = recognition.to_dict()
            
            # Execute Cypher query to create/update recognition
            query = RecognitionNode.create_query()
            result = await self.neo4j.execute_query(query, params)
            
            # Create relationships if result is successful
            if result and len(result) > 0:
                # Create INSTANCE_OF relationship if the method exists
                if hasattr(recognition, 'create_instance_of_relationship_query'):
                    instance_query = recognition.create_instance_of_relationship_query()
                    await self.neo4j.execute_query(instance_query, params)
                    logger.info(f"Created INSTANCE_OF relationship for recognition {recognition.recognition_id}")
                
                logger.info(f"Successfully created/updated recognition {recognition.recognition_id} in Neo4j")
                return True
            else:
                logger.error(f"Failed to create/update recognition in Neo4j")
                return False
        except Exception as e:
            logger.error(f"Error creating/updating recognition in Neo4j: {e}")
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
        
        try:
            result = await self.neo4j.execute_query(query, params)
            if result and len(result) > 0:
                return RecognitionNode.from_record({"r": result[0][0]})
            return None
        except Exception as e:
            logger.error(f"Error retrieving recognition by ID: {e}")
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
            logger.info(f"Successfully deleted recognition {recognition_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting recognition from Neo4j: {e}")
            return False
    
    async def get_by_candidate(self, candidate_id):
        """
        Get all recognitions received by a candidate.
        
        Args:
            candidate_id: ID of the candidate
            
        Returns:
            List of recognitions
        """
        query = f"""
        MATCH (c:Candidate {{candidate_id: $candidate_id}})-[:{RECEIVES_RECOGNITION_REL}]->(r:Recognition)
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
            logger.error(f"Error getting recognitions for candidate {candidate_id}: {e}")
            return []
    
    async def get_by_exam(self, exam_id):
        """
        Get all recognitions awarded in a specific exam.
        
        Args:
            exam_id: ID of the exam
            
        Returns:
            List of recognitions
        """
        query = f"""
        MATCH (r:Recognition)-[:{RECOGNITION_FOR_EXAM_REL}]->(e:Exam {{exam_id: $exam_id}})
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
            logger.error(f"Error getting recognitions for exam {exam_id}: {e}")
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
            logger.error(f"Error getting recognitions by type {recognition_type}: {e}")
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
            logger.error(f"Error getting recognitions by organization {organization}: {e}")
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
            
            logger.info(f"Retrieved {len(recognitions)} recognition nodes")
            return recognitions
        except Exception as e:
            logger.error(f"Error getting all recognitions: {e}")
            return []
    
    async def add_received_by_relationship(self, recognition_id, candidate_id):
        """
        Create a relationship between a recognition and a candidate.
        
        Args:
            recognition_id: ID of the recognition
            candidate_id: ID of the candidate who received the recognition
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            query = f"""
            MATCH (r:Recognition {{recognition_id: $recognition_id}})
            MATCH (c:Candidate {{candidate_id: $candidate_id}})
            MERGE (c)-[rel:{RECEIVES_RECOGNITION_REL}]->(r)
            SET rel.updated_at = datetime()
            RETURN rel
            """
            
            params = {
                "recognition_id": recognition_id,
                "candidate_id": candidate_id
            }
            
            await self.neo4j.execute_query(query, params)
            logger.info(f"Added RECEIVES_RECOGNITION relationship between candidate {candidate_id} and recognition {recognition_id}")
            return True
        except Exception as e:
            logger.error(f"Error adding RECEIVES_RECOGNITION relationship: {e}")
            return False
            
    async def add_for_exam_relationship(self, recognition_id, exam_id):
        """
        Create a relationship between a recognition and an exam.
        
        Args:
            recognition_id: ID of the recognition
            exam_id: ID of the exam the recognition is for
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            query = f"""
            MATCH (r:Recognition {{recognition_id: $recognition_id}})
            MATCH (e:Exam {{exam_id: $exam_id}})
            MERGE (r)-[rel:{RECOGNITION_FOR_EXAM_REL}]->(e)
            SET rel.updated_at = datetime()
            RETURN rel
            """
            
            params = {
                "recognition_id": recognition_id,
                "exam_id": exam_id
            }
            
            await self.neo4j.execute_query(query, params)
            logger.info(f"Added RECOGNITION_FOR_EXAM relationship between recognition {recognition_id} and exam {exam_id}")
            return True
        except Exception as e:
            logger.error(f"Error adding RECOGNITION_FOR_EXAM relationship: {e}")
            return False 