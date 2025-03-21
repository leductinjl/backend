"""
Major Graph Repository module.

This module provides methods for interacting with Major nodes in Neo4j.
"""

from app.domain.graph_models.major_node import MajorNode
from app.infrastructure.ontology.ontology import RELATIONSHIPS

class MajorGraphRepository:
    """
    Repository for managing Major nodes in Neo4j knowledge graph.
    
    This class provides methods to create, update, and query Major nodes
    and their relationships with other entities in the knowledge graph.
    """
    
    def __init__(self, neo4j_connection):
        """Initialize with Neo4j connection."""
        self.neo4j = neo4j_connection
    
    async def create_or_update(self, major):
        """
        Create or update a Major node in Neo4j.
        
        Args:
            major: MajorNode object or dictionary with major data
            
        Returns:
            bool: True if operation successful, False otherwise
        """
        try:
            # Ensure we have a dictionary
            params = major.to_dict() if hasattr(major, 'to_dict') else major
            
            # Execute Cypher query to create/update major
            query = MajorNode.create_query()
            result = await self.neo4j.execute_query(query, params)
            
            if result and len(result) > 0:
                return True
            return False
        except Exception as e:
            print(f"Error creating/updating major in Neo4j: {e}")
            return False
    
    async def get_by_id(self, major_id):
        """
        Get a major by ID.
        
        Args:
            major_id: The ID of the major to retrieve
            
        Returns:
            MajorNode or None if not found
        """
        query = """
        MATCH (m:Major {major_id: $major_id})
        RETURN m
        """
        params = {"major_id": major_id}
        
        result = await self.neo4j.execute_query(query, params)
        if result and len(result) > 0:
            return MajorNode.from_record({"m": result[0][0]})
        return None
    
    async def delete(self, major_id):
        """
        Delete a major from Neo4j.
        
        Args:
            major_id: ID of the major to delete
            
        Returns:
            bool: True if successful, False otherwise
        """
        query = """
        MATCH (m:Major {major_id: $major_id})
        DETACH DELETE m
        """
        params = {"major_id": major_id}
        
        try:
            await self.neo4j.execute_query(query, params)
            return True
        except Exception as e:
            print(f"Error deleting major from Neo4j: {e}")
            return False
    
    async def get_schools_offering_major(self, major_id):
        """
        Get all schools that offer this major.
        
        Args:
            major_id: ID of the major
            
        Returns:
            List of schools with relationship details
        """
        query = """
        MATCH (s:School)-[r:OFFERS_MAJOR]->(m:Major {major_id: $major_id})
        RETURN s, r.start_year as start_year
        """
        params = {"major_id": major_id}
        
        try:
            result = await self.neo4j.execute_query(query, params)
            schools = []
            
            for record in result:
                school = record[0]
                start_year = record[1]
                
                schools.append({
                    "school_id": school["school_id"],
                    "school_name": school["school_name"],
                    "city": school.get("city"),
                    "country": school.get("country"),
                    "start_year": start_year
                })
            
            return schools
        except Exception as e:
            print(f"Error getting schools for major: {e}")
            return []
    
    async def get_candidates_studying_major(self, major_id):
        """
        Get all candidates who study this major.
        
        Args:
            major_id: ID of the major
            
        Returns:
            List of candidates with their education details
        """
        query = """
        MATCH (c:Candidate)-[:STUDIES_MAJOR]->(m:Major {major_id: $major_id})
        RETURN c
        """
        params = {"major_id": major_id}
        
        try:
            result = await self.neo4j.execute_query(query, params)
            candidates = []
            
            for record in result:
                candidate = record[0]
                
                candidates.append({
                    "candidate_id": candidate["candidate_id"],
                    "full_name": candidate["full_name"],
                    "email": candidate.get("email")
                })
            
            return candidates
        except Exception as e:
            print(f"Error getting candidates for major: {e}")
            return []
    
    async def get_all_majors(self, limit=100):
        """
        Get all majors in the graph.
        
        Args:
            limit: Maximum number of majors to return
            
        Returns:
            List of majors
        """
        query = """
        MATCH (m:Major)
        RETURN m
        LIMIT $limit
        """
        params = {"limit": limit}
        
        try:
            result = await self.neo4j.execute_query(query, params)
            majors = []
            
            for record in result:
                node = record[0]
                major = MajorNode.from_record({"m": node})
                majors.append(major.to_dict())
            
            return majors
        except Exception as e:
            print(f"Error getting all majors: {e}")
            return []
    
    async def find_related_majors(self, major_id, relationship_threshold=2):
        """
        Find majors that are related to the given major.
        Majors are considered related if they are studied by the same candidates
        or offered by the same schools.
        
        Args:
            major_id: ID of the major
            relationship_threshold: Minimum number of shared connections to consider related
            
        Returns:
            List of related majors with a score indicating strength of relationship
        """
        query = """
        // Find majors that are offered by the same schools
        MATCH (m1:Major {major_id: $major_id})
        MATCH (m1)<-[:OFFERS_MAJOR]-(s:School)-[:OFFERS_MAJOR]->(m2:Major)
        WHERE m1 <> m2
        
        WITH m2, count(distinct s) as shared_schools
        
        // Find majors that are studied by the same candidates
        OPTIONAL MATCH (m1:Major {major_id: $major_id})
        OPTIONAL MATCH (m1)<-[:STUDIES_MAJOR]-(c:Candidate)-[:STUDIES_MAJOR]->(m2:Major)
        WHERE m1 <> m2
        
        WITH m2, shared_schools, count(distinct c) as shared_candidates
        
        // Calculate relationship score
        WITH m2, shared_schools, shared_candidates, 
             (shared_schools + shared_candidates) as relationship_score
        
        WHERE relationship_score >= $threshold
        
        RETURN m2, shared_schools, shared_candidates, relationship_score
        ORDER BY relationship_score DESC
        """
        params = {
            "major_id": major_id,
            "threshold": relationship_threshold
        }
        
        try:
            result = await self.neo4j.execute_query(query, params)
            related_majors = []
            
            for record in result:
                major = record[0]
                shared_schools = record[1]
                shared_candidates = record[2]
                relationship_score = record[3]
                
                related_majors.append({
                    "major_id": major["major_id"],
                    "major_name": major["major_name"],
                    "description": major.get("description"),
                    "shared_schools": shared_schools,
                    "shared_candidates": shared_candidates,
                    "relationship_score": relationship_score
                })
            
            return related_majors
        except Exception as e:
            print(f"Error finding related majors: {e}")
            return [] 