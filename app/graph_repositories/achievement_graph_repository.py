"""
Achievement Graph Repository module.

This module provides methods for interacting with Achievement nodes in Neo4j.
"""

from app.domain.graph_models.achievement_node import AchievementNode
from app.infrastructure.ontology.ontology import RELATIONSHIPS

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
            
            # Create relationships if possible
            if result and len(result) > 0:
                if hasattr(achievement, 'create_relationships_query'):
                    rel_query = achievement.create_relationships_query()
                    await self.neo4j.execute_query(rel_query, params)
                return True
            return False
        except Exception as e:
            print(f"Error creating/updating achievement in Neo4j: {e}")
            return False
    
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
        query = """
        MATCH (c:Candidate {candidate_id: $candidate_id})-[:EARNS_ACHIEVEMENT]->(a:Achievement)
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
        query = """
        MATCH (a:Achievement)-[:ACHIEVED_IN]->(e:Exam {exam_id: $exam_id})
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