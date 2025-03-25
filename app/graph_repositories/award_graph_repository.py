"""
Award Graph Repository module.

This module provides methods for interacting with Award nodes in Neo4j.
"""

from app.domain.graph_models.award_node import AwardNode
from app.infrastructure.ontology.ontology import RELATIONSHIPS
import logging

logger = logging.getLogger(__name__)

# Import specific relationships
EARNS_AWARD_REL = RELATIONSHIPS["EARNS_AWARD"]["type"]
AWARD_FOR_EXAM_REL = RELATIONSHIPS["AWARD_FOR_EXAM"]["type"]
INSTANCE_OF_REL = RELATIONSHIPS["INSTANCE_OF"]["type"]

class AwardGraphRepository:
    """
    Repository for managing Award nodes in Neo4j knowledge graph.
    
    This class provides methods to create, update, and query Award nodes
    and their relationships with other entities in the knowledge graph.
    """
    
    def __init__(self, neo4j_connection):
        """Initialize with Neo4j connection."""
        self.neo4j = neo4j_connection
    
    async def create_or_update(self, award):
        """
        Create or update an Award node in Neo4j.
        
        Args:
            award: AwardNode object or dictionary with award data
            
        Returns:
            bool: True if operation successful, False otherwise
        """
        try:
            # Ensure we have a dictionary
            params = award.to_dict() if hasattr(award, 'to_dict') else award
            
            # Execute Cypher query to create/update award
            query = AwardNode.create_query()
            result = await self.neo4j.execute_query(query, params)
            
            # Create INSTANCE_OF relationship only
            if result and len(result) > 0:
                # Create INSTANCE_OF relationship with Award class
                await self._create_instance_of_relationship(params.get('award_id'))
                return True
            return False
        except Exception as e:
            logger.error(f"Error creating/updating award in Neo4j: {e}")
            return False
    
    async def _create_instance_of_relationship(self, award_id):
        """
        Tạo mối quan hệ INSTANCE_OF giữa node instance và class node tương ứng.
        
        Args:
            award_id: ID của node instance
        """
        try:
            query = AwardNode.create_instance_of_relationship_query()
            await self.neo4j.execute_query(query, {"award_id": award_id})
            logger.info(f"Created INSTANCE_OF relationship for award {award_id}")
        except Exception as e:
            logger.error(f"Error creating INSTANCE_OF relationship for award {award_id}: {e}")
            raise
    
    async def get_by_id(self, award_id):
        """
        Get an award by ID.
        
        Args:
            award_id: The ID of the award to retrieve
            
        Returns:
            AwardNode or None if not found
        """
        query = """
        MATCH (a:Award {award_id: $award_id})
        RETURN a
        """
        params = {"award_id": award_id}
        
        result = await self.neo4j.execute_query(query, params)
        if result and len(result) > 0:
            return AwardNode.from_record({"a": result[0][0]})
        return None
    
    async def delete(self, award_id):
        """
        Delete an award from Neo4j.
        
        Args:
            award_id: ID of the award to delete
            
        Returns:
            bool: True if successful, False otherwise
        """
        query = """
        MATCH (a:Award {award_id: $award_id})
        DETACH DELETE a
        """
        params = {"award_id": award_id}
        
        try:
            await self.neo4j.execute_query(query, params)
            return True
        except Exception as e:
            logger.error(f"Error deleting award from Neo4j: {e}")
            return False
    
    async def get_by_candidate(self, candidate_id):
        """
        Get all awards received by a candidate.
        
        Args:
            candidate_id: ID of the candidate
            
        Returns:
            List of awards
        """
        query = f"""
        MATCH (c:Candidate {{candidate_id: $candidate_id}})-[:{EARNS_AWARD_REL}]->(a:Award)
        RETURN a
        """
        params = {"candidate_id": candidate_id}
        
        try:
            result = await self.neo4j.execute_query(query, params)
            awards = []
            
            for record in result:
                award = AwardNode.from_record({"a": record[0]})
                awards.append(award.to_dict())
            
            return awards
        except Exception as e:
            logger.error(f"Error getting awards for candidate: {e}")
            return []
    
    async def get_by_exam(self, exam_id):
        """
        Get all awards given in a specific exam.
        
        Args:
            exam_id: ID of the exam
            
        Returns:
            List of awards
        """
        query = f"""
        MATCH (a:Award)-[:{AWARD_FOR_EXAM_REL}]->(e:Exam {{exam_id: $exam_id}})
        RETURN a
        """
        params = {"exam_id": exam_id}
        
        try:
            result = await self.neo4j.execute_query(query, params)
            awards = []
            
            for record in result:
                award = AwardNode.from_record({"a": record[0]})
                awards.append(award.to_dict())
            
            return awards
        except Exception as e:
            logger.error(f"Error getting awards for exam: {e}")
            return []
    
    async def get_by_award_type(self, award_type):
        """
        Get all awards of a specific type.
        
        Args:
            award_type: Type of the award
            
        Returns:
            List of awards
        """
        query = """
        MATCH (a:Award {award_type: $award_type})
        RETURN a
        """
        params = {"award_type": award_type}
        
        try:
            result = await self.neo4j.execute_query(query, params)
            awards = []
            
            for record in result:
                award = AwardNode.from_record({"a": record[0]})
                awards.append(award.to_dict())
            
            return awards
        except Exception as e:
            logger.error(f"Error getting awards by type: {e}")
            return []
    
    async def get_by_organization(self, organization):
        """
        Get all awards issued by a specific organization.
        
        Args:
            organization: Name of the issuing organization
            
        Returns:
            List of awards
        """
        query = """
        MATCH (a:Award)
        WHERE a.issuing_organization = $organization
        RETURN a
        """
        params = {"organization": organization}
        
        try:
            result = await self.neo4j.execute_query(query, params)
            awards = []
            
            for record in result:
                award = AwardNode.from_record({"a": record[0]})
                awards.append(award.to_dict())
            
            return awards
        except Exception as e:
            logger.error(f"Error getting awards by organization: {e}")
            return []
    
    async def get_all_awards(self, limit=100):
        """
        Get all awards in the knowledge graph.
        
        Args:
            limit: Maximum number of awards to return
            
        Returns:
            List of awards
        """
        query = """
        MATCH (a:Award)
        RETURN a
        LIMIT $limit
        """
        params = {"limit": limit}
        
        try:
            result = await self.neo4j.execute_query(query, params)
            awards = []
            
            for record in result:
                award = AwardNode.from_record({"a": record[0]})
                awards.append(award.to_dict())
            
            return awards
        except Exception as e:
            logger.error(f"Error getting all awards: {e}")
            return []
    
    async def add_awarded_to_relationship(self, award_id, candidate_id):
        """
        Create a relationship between a candidate and an award.
        
        Args:
            award_id: ID of the award
            candidate_id: ID of the candidate who received the award
            
        Returns:
            True if successful, False otherwise
        """
        try:
            query = f"""
            MATCH (c:Candidate {{candidate_id: $candidate_id}})
            MATCH (a:Award {{award_id: $award_id}})
            MERGE (c)-[r:{EARNS_AWARD_REL}]->(a)
            SET r.updated_at = datetime()
            RETURN r
            """
            
            params = {
                "award_id": award_id,
                "candidate_id": candidate_id
            }
            
            await self.neo4j.execute_query(query, params)
            logger.info(f"Added EARNS_AWARD relationship between candidate {candidate_id} and award {award_id}")
            return True
        except Exception as e:
            logger.error(f"Error adding EARNS_AWARD relationship: {e}")
            return False
    
    async def add_award_for_exam_relationship(self, award_id, exam_id):
        """
        Create a relationship between an award and an exam.
        
        Args:
            award_id: ID of the award
            exam_id: ID of the exam the award was given for
            
        Returns:
            True if successful, False otherwise
        """
        try:
            query = f"""
            MATCH (a:Award {{award_id: $award_id}})
            MATCH (e:Exam {{exam_id: $exam_id}})
            MERGE (a)-[r:{AWARD_FOR_EXAM_REL}]->(e)
            SET r.updated_at = datetime()
            RETURN r
            """
            
            params = {
                "award_id": award_id,
                "exam_id": exam_id
            }
            
            await self.neo4j.execute_query(query, params)
            logger.info(f"Added AWARD_FOR_EXAM relationship between award {award_id} and exam {exam_id}")
            return True
        except Exception as e:
            logger.error(f"Error adding AWARD_FOR_EXAM relationship: {e}")
            return False 