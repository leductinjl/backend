"""
Degree Graph Repository module.

This module provides methods for interacting with Degree nodes in Neo4j.
"""

from app.domain.graph_models.degree_node import DegreeNode
from app.infrastructure.ontology.ontology import RELATIONSHIPS

class DegreeGraphRepository:
    """
    Repository for managing Degree nodes in Neo4j knowledge graph.
    
    This class provides methods to create, update, and query Degree nodes
    and their relationships with other entities in the knowledge graph.
    """
    
    def __init__(self, neo4j_connection):
        """Initialize with Neo4j connection."""
        self.neo4j = neo4j_connection
    
    async def create_or_update(self, degree):
        """
        Create or update a Degree node in Neo4j.
        
        Args:
            degree: DegreeNode object or dictionary with degree data
            
        Returns:
            bool: True if operation successful, False otherwise
        """
        try:
            # Ensure we have a dictionary
            params = degree.to_dict() if hasattr(degree, 'to_dict') else degree
            
            # Execute Cypher query to create/update degree
            query = DegreeNode.create_query()
            result = await self.neo4j.execute_query(query, params)
            
            # Create relationships if possible
            if result and len(result) > 0:
                if hasattr(degree, 'create_relationships_query'):
                    rel_query = degree.create_relationships_query()
                    await self.neo4j.execute_query(rel_query, params)
                return True
            return False
        except Exception as e:
            print(f"Error creating/updating degree in Neo4j: {e}")
            return False
    
    async def get_by_id(self, degree_id):
        """
        Get a degree by ID.
        
        Args:
            degree_id: The ID of the degree to retrieve
            
        Returns:
            DegreeNode or None if not found
        """
        query = """
        MATCH (d:Degree {degree_id: $degree_id})
        RETURN d
        """
        params = {"degree_id": degree_id}
        
        result = await self.neo4j.execute_query(query, params)
        if result and len(result) > 0:
            return DegreeNode.from_record({"d": result[0][0]})
        return None
    
    async def delete(self, degree_id):
        """
        Delete a degree from Neo4j.
        
        Args:
            degree_id: ID of the degree to delete
            
        Returns:
            bool: True if successful, False otherwise
        """
        query = """
        MATCH (d:Degree {degree_id: $degree_id})
        DETACH DELETE d
        """
        params = {"degree_id": degree_id}
        
        try:
            await self.neo4j.execute_query(query, params)
            return True
        except Exception as e:
            print(f"Error deleting degree from Neo4j: {e}")
            return False
    
    async def get_by_candidate(self, candidate_id):
        """
        Get all degrees held by a candidate.
        
        Args:
            candidate_id: ID of the candidate
            
        Returns:
            List of degrees
        """
        query = """
        MATCH (c:Candidate {candidate_id: $candidate_id})-[:HOLDS_DEGREE]->(d:Degree)
        RETURN d
        """
        params = {"candidate_id": candidate_id}
        
        try:
            result = await self.neo4j.execute_query(query, params)
            degrees = []
            
            for record in result:
                degree = DegreeNode.from_record({"d": record[0]})
                degrees.append(degree.to_dict())
            
            return degrees
        except Exception as e:
            print(f"Error getting degrees for candidate: {e}")
            return []
    
    async def get_by_major(self, major_id):
        """
        Get all degrees in a specific major.
        
        Args:
            major_id: ID of the major
            
        Returns:
            List of degrees
        """
        query = """
        MATCH (d:Degree)-[:IN_MAJOR]->(m:Major {major_id: $major_id})
        RETURN d
        """
        params = {"major_id": major_id}
        
        try:
            result = await self.neo4j.execute_query(query, params)
            degrees = []
            
            for record in result:
                degree = DegreeNode.from_record({"d": record[0]})
                degrees.append(degree.to_dict())
            
            return degrees
        except Exception as e:
            print(f"Error getting degrees for major: {e}")
            return []
    
    async def get_by_school(self, school_id):
        """
        Get all degrees issued by a specific school.
        
        Args:
            school_id: ID of the school
            
        Returns:
            List of degrees
        """
        query = """
        MATCH (d:Degree)-[:ISSUED_BY]->(s:School {school_id: $school_id})
        RETURN d
        """
        params = {"school_id": school_id}
        
        try:
            result = await self.neo4j.execute_query(query, params)
            degrees = []
            
            for record in result:
                degree = DegreeNode.from_record({"d": record[0]})
                degrees.append(degree.to_dict())
            
            return degrees
        except Exception as e:
            print(f"Error getting degrees for school: {e}")
            return []
    
    async def get_by_degree_type(self, degree_type):
        """
        Get all degrees of a specific type.
        
        Args:
            degree_type: Type of degrees to retrieve
            
        Returns:
            List of degrees
        """
        query = """
        MATCH (d:Degree)
        WHERE d.degree_type = $degree_type
        RETURN d
        """
        params = {"degree_type": degree_type}
        
        try:
            result = await self.neo4j.execute_query(query, params)
            degrees = []
            
            for record in result:
                degree = DegreeNode.from_record({"d": record[0]})
                degrees.append(degree.to_dict())
            
            return degrees
        except Exception as e:
            print(f"Error getting degrees by type: {e}")
            return []
    
    async def get_all_degrees(self, limit=100):
        """
        Get all degrees in the knowledge graph.
        
        Args:
            limit: Maximum number of degrees to return
            
        Returns:
            List of degrees
        """
        query = """
        MATCH (d:Degree)
        RETURN d
        LIMIT $limit
        """
        params = {"limit": limit}
        
        try:
            result = await self.neo4j.execute_query(query, params)
            degrees = []
            
            for record in result:
                degree = DegreeNode.from_record({"d": record[0]})
                degrees.append(degree.to_dict())
            
            return degrees
        except Exception as e:
            print(f"Error getting all degrees: {e}")
            return [] 