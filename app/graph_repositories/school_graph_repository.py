"""
School Graph Repository module.

This module provides methods for interacting with School nodes in Neo4j.
"""

from app.domain.graph_models.school_node import SchoolNode
from app.infrastructure.ontology.ontology import RELATIONSHIPS
import logging

logger = logging.getLogger(__name__)

class SchoolGraphRepository:
    """
    Repository for managing School nodes in Neo4j knowledge graph.
    
    This class provides methods to create, update, and query School nodes
    and their relationships with other entities in the knowledge graph.
    """
    
    def __init__(self, neo4j_connection):
        """Initialize with Neo4j connection."""
        self.neo4j = neo4j_connection
    
    async def create_or_update(self, school):
        """
        Create or update a School node in Neo4j.
        
        Args:
            school: SchoolNode object or dictionary with school data
            
        Returns:
            bool: True if operation successful, False otherwise
        """
        try:
            # Ensure we have a dictionary
            params = school.to_dict() if hasattr(school, 'to_dict') else school
            
            # Execute Cypher query to create/update school
            query = SchoolNode.create_query()
            result = await self.neo4j.execute_query(query, params)
            
            if result and len(result) > 0:
                # Create IS_A relationship with School class
                await self._create_is_a_relationship(params["school_id"])
                logger.info(f"Successfully created/updated school {params['school_id']} in Neo4j")
                return True
            return False
        except Exception as e:
            logger.error(f"Error creating/updating school in Neo4j: {e}", exc_info=True)
            return False
    
    async def _create_is_a_relationship(self, school_id):
        """
        Create INSTANCE_OF relationship between School node and School class node.
        
        Args:
            school_id: ID of the school node
        """
        try:
            query = """
            MATCH (instance:School:OntologyInstance {school_id: $school_id})
            MATCH (class:School:OntologyClass {id: 'school-class'})
            MERGE (instance)-[r:INSTANCE_OF]->(class)
            RETURN r
            """
            params = {
                "school_id": school_id
            }
            await self.neo4j.execute_query(query, params)
            logger.info(f"Created INSTANCE_OF relationship for school {school_id}")
            return True
        except Exception as e:
            logger.error(f"Error creating INSTANCE_OF relationship for school {school_id}: {e}")
            return False
    
    async def get_by_id(self, school_id):
        """
        Get a school by ID.
        
        Args:
            school_id: The ID of the school to retrieve
            
        Returns:
            SchoolNode or None if not found
        """
        query = """
        MATCH (s:School {school_id: $school_id})
        RETURN s
        """
        params = {"school_id": school_id}
        
        result = await self.neo4j.execute_query(query, params)
        if result and len(result) > 0:
            return SchoolNode.from_record({"s": result[0][0]})
        return None
    
    async def delete(self, school_id):
        """
        Delete a school from Neo4j.
        
        Args:
            school_id: ID of the school to delete
            
        Returns:
            bool: True if successful, False otherwise
        """
        query = """
        MATCH (s:School {school_id: $school_id})
        DETACH DELETE s
        """
        params = {"school_id": school_id}
        
        try:
            await self.neo4j.execute_query(query, params)
            return True
        except Exception as e:
            print(f"Error deleting school from Neo4j: {e}")
            return False
    
    async def add_offers_major_relationship(self, school_id, major_id, start_year=None):
        """
        Create a relationship between a school and a major.
        
        Args:
            school_id: ID of the school
            major_id: ID of the major
            start_year: Year when the school started offering the major
            
        Returns:
            bool: True if successful, False otherwise
        """
        query = RELATIONSHIPS["OFFERS_MAJOR"]["create_query"]
        
        params = {
            "school_id": school_id,
            "major_id": major_id,
            "start_year": start_year
        }
        
        try:
            await self.neo4j.execute_query(query, params)
            return True
        except Exception as e:
            print(f"Error adding OFFERS_MAJOR relationship: {e}")
            return False
    
    async def get_majors(self, school_id):
        """
        Get all majors offered by a school.
        
        Args:
            school_id: ID of the school
            
        Returns:
            List of majors
        """
        query = """
        MATCH (s:School {school_id: $school_id})-[r:OFFERS_MAJOR]->(m:Major)
        RETURN m, r.start_year as start_year
        """
        params = {"school_id": school_id}
        
        try:
            result = await self.neo4j.execute_query(query, params)
            majors = []
            
            for record in result:
                major = record[0]
                start_year = record[1]
                
                majors.append({
                    "major_id": major["major_id"],
                    "major_name": major["major_name"],
                    "description": major.get("description"),
                    "start_year": start_year
                })
            
            return majors
        except Exception as e:
            print(f"Error getting majors for school: {e}")
            return []
    
    async def get_students(self, school_id):
        """
        Get all students (candidates) who study at a school.
        
        Args:
            school_id: ID of the school
            
        Returns:
            List of candidates with their education details
        """
        query = """
        MATCH (c:Candidate)-[r:STUDIES_AT]->(s:School {school_id: $school_id})
        RETURN c, r.start_year as start_year, r.end_year as end_year, 
               r.education_level as education_level
        """
        params = {"school_id": school_id}
        
        try:
            result = await self.neo4j.execute_query(query, params)
            students = []
            
            for record in result:
                candidate = record[0]
                start_year = record[1]
                end_year = record[2]
                education_level = record[3]
                
                students.append({
                    "candidate_id": candidate["candidate_id"],
                    "full_name": candidate["full_name"],
                    "start_year": start_year,
                    "end_year": end_year,
                    "education_level": education_level
                })
            
            return students
        except Exception as e:
            print(f"Error getting students for school: {e}")
            return [] 