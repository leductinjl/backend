"""
Achievement Graph Repository module.

This module provides methods for interacting with Achievement nodes in Neo4j.
"""

from app.domain.graph_models.achievement_node import AchievementNode
from app.infrastructure.ontology.ontology import RELATIONSHIPS

# Import specific relationships
ACHIEVES_REL = RELATIONSHIPS["ACHIEVES"]["type"]
ACHIEVEMENT_FOR_EXAM_REL = RELATIONSHIPS["ACHIEVEMENT_FOR_EXAM"]["type"]
INSTANCE_OF_REL = RELATIONSHIPS["INSTANCE_OF"]["type"]

class AchievementGraphRepository:
    """
    Repository for managing Achievement nodes in Neo4j knowledge graph.
    
    This class provides methods to create, update, and query Achievement nodes
    and their relationships with other entities in the knowledge graph.
    """
    
    def __init__(self, neo4j_connection):
        """Initialize with Neo4j connection."""
        self.neo4j = neo4j_connection
    
    async def create_or_update(self, achievement):
        """
        Create or update an Achievement node in Neo4j.
        
        Args:
            achievement: AchievementNode object or dictionary with achievement data
            
        Returns:
            bool: True if operation successful, False otherwise
        """
        try:
            # Ensure we have a dictionary
            params = achievement.to_dict() if hasattr(achievement, 'to_dict') else achievement
            
            # Execute Cypher query to create/update achievement
            query = AchievementNode.create_query()
            result = await self.neo4j.execute_query(query, params)
            
            # Create INSTANCE_OF relationship only
            if result and len(result) > 0:
                # Create INSTANCE_OF relationship with Achievement class
                await self._create_instance_of_relationship(params.get('achievement_id'))
                return True
            return False
        except Exception as e:
            print(f"Error creating/updating achievement in Neo4j: {e}")
            return False
    
    async def _create_instance_of_relationship(self, achievement_id):
        """
        Tạo mối quan hệ INSTANCE_OF giữa node instance và class node tương ứng.
        
        Args:
            achievement_id: ID của node instance
        """
        try:
            query = AchievementNode.create_instance_of_relationship_query()
            await self.neo4j.execute_query(query, {"achievement_id": achievement_id})
            print(f"Created INSTANCE_OF relationship for achievement {achievement_id}")
        except Exception as e:
            print(f"Error creating INSTANCE_OF relationship for achievement {achievement_id}: {e}")
            raise
    
    async def get_by_id(self, achievement_id):
        """
        Get an achievement by ID.
        
        Args:
            achievement_id: The ID of the achievement to retrieve
            
        Returns:
            AchievementNode or None if not found
        """
        query = """
        MATCH (a:Achievement {achievement_id: $achievement_id})
        RETURN a
        """
        params = {"achievement_id": achievement_id}
        
        result = await self.neo4j.execute_query(query, params)
        if result and len(result) > 0:
            return AchievementNode.from_record({"a": result[0][0]})
        return None
    
    async def delete(self, achievement_id):
        """
        Delete an achievement from Neo4j.
        
        Args:
            achievement_id: ID of the achievement to delete
            
        Returns:
            bool: True if successful, False otherwise
        """
        query = """
        MATCH (a:Achievement {achievement_id: $achievement_id})
        DETACH DELETE a
        """
        params = {"achievement_id": achievement_id}
        
        try:
            await self.neo4j.execute_query(query, params)
            return True
        except Exception as e:
            print(f"Error deleting achievement from Neo4j: {e}")
            return False
    
    async def get_by_candidate(self, candidate_id):
        """
        Get all achievements earned by a candidate.
        
        Args:
            candidate_id: ID of the candidate
            
        Returns:
            List of achievements
        """
        query = f"""
        MATCH (c:Candidate {{candidate_id: $candidate_id}})-[:{ACHIEVES_REL}]->(a:Achievement)
        RETURN a
        """
        params = {"candidate_id": candidate_id}
        
        try:
            result = await self.neo4j.execute_query(query, params)
            achievements = []
            
            for record in result:
                achievement = AchievementNode.from_record({"a": record[0]})
                achievements.append(achievement.to_dict())
            
            return achievements
        except Exception as e:
            print(f"Error getting achievements for candidate: {e}")
            return []
    
    async def get_by_exam(self, exam_id):
        """
        Get all achievements awarded in a specific exam.
        
        Args:
            exam_id: ID of the exam
            
        Returns:
            List of achievements
        """
        query = f"""
        MATCH (a:Achievement)-[:{ACHIEVEMENT_FOR_EXAM_REL}]->(e:Exam {{exam_id: $exam_id}})
        RETURN a
        """
        params = {"exam_id": exam_id}
        
        try:
            result = await self.neo4j.execute_query(query, params)
            achievements = []
            
            for record in result:
                achievement = AchievementNode.from_record({"a": record[0]})
                achievements.append(achievement.to_dict())
            
            return achievements
        except Exception as e:
            print(f"Error getting achievements for exam: {e}")
            return []
    
    async def get_by_achievement_type(self, achievement_type):
        """
        Get all achievements of a specific type.
        
        Args:
            achievement_type: Type of achievements to retrieve
            
        Returns:
            List of achievements
        """
        query = """
        MATCH (a:Achievement)
        WHERE a.achievement_type = $achievement_type
        RETURN a
        """
        params = {"achievement_type": achievement_type}
        
        try:
            result = await self.neo4j.execute_query(query, params)
            achievements = []
            
            for record in result:
                achievement = AchievementNode.from_record({"a": record[0]})
                achievements.append(achievement.to_dict())
            
            return achievements
        except Exception as e:
            print(f"Error getting achievements by type: {e}")
            return []
    
    async def get_by_organization(self, organization):
        """
        Get all achievements issued by a specific organization.
        
        Args:
            organization: Name of the issuing organization
            
        Returns:
            List of achievements
        """
        query = """
        MATCH (a:Achievement)
        WHERE a.issuing_organization = $organization
        RETURN a
        """
        params = {"organization": organization}
        
        try:
            result = await self.neo4j.execute_query(query, params)
            achievements = []
            
            for record in result:
                achievement = AchievementNode.from_record({"a": record[0]})
                achievements.append(achievement.to_dict())
            
            return achievements
        except Exception as e:
            print(f"Error getting achievements by organization: {e}")
            return []
    
    async def get_all_achievements(self, limit=100):
        """
        Get all achievements in the knowledge graph.
        
        Args:
            limit: Maximum number of achievements to return
            
        Returns:
            List of achievements
        """
        query = """
        MATCH (a:Achievement)
        RETURN a
        LIMIT $limit
        """
        
        params = {"limit": limit}
        
        try:
            result = await self.neo4j.execute_query(query, params)
            achievements = []
            
            for record in result:
                achievement = AchievementNode.from_record({"a": record[0]})
                achievements.append(achievement.to_dict())
            
            return achievements
        except Exception as e:
            print(f"Error getting all achievements: {e}")
            return []

    async def add_earned_by_relationship(self, achievement_id, candidate_id):
        """
        Create a relationship between an achievement and a candidate.
        
        Args:
            achievement_id: ID of the achievement
            candidate_id: ID of the candidate
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            query = """
            MATCH (a:Achievement {achievement_id: $achievement_id})
            MATCH (c:Candidate {candidate_id: $candidate_id})
            MERGE (c)-[r:ACHIEVES]->(a)
            RETURN r
            """
            
            params = {
                "achievement_id": achievement_id,
                "candidate_id": candidate_id
            }
            
            await self.neo4j.execute_query(query, params)
            print(f"Added ACHIEVES relationship between Candidate {candidate_id} and Achievement {achievement_id}")
            return True
        except Exception as e:
            print(f"Error adding ACHIEVES relationship: {e}")
            return False

    async def add_for_exam_relationship(self, achievement_id, exam_id):
        """
        Create a relationship between an achievement and an exam.
        
        Args:
            achievement_id: ID of the achievement
            exam_id: ID of the exam
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            query = """
            MATCH (a:Achievement {achievement_id: $achievement_id})
            MATCH (e:Exam {exam_id: $exam_id})
            MERGE (a)-[r:ACHIEVEMENT_FOR_EXAM]->(e)
            RETURN r
            """
            
            params = {
                "achievement_id": achievement_id,
                "exam_id": exam_id
            }
            
            await self.neo4j.execute_query(query, params)
            print(f"Added ACHIEVEMENT_FOR_EXAM relationship between Achievement {achievement_id} and Exam {exam_id}")
            return True
        except Exception as e:
            print(f"Error adding ACHIEVEMENT_FOR_EXAM relationship: {e}")
            return False 