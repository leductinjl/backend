"""
School Graph Repository module.

This module provides methods for interacting with School nodes in Neo4j.
"""

from typing import Dict, List, Optional, Union
import logging

from app.domain.graph_models.school_node import (
    SchoolNode, INSTANCE_OF_REL, OFFERS_MAJOR_REL, STUDIES_AT_REL, ISSUED_BY_REL
)
from app.infrastructure.ontology.ontology import RELATIONSHIPS

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
            # Convert to SchoolNode if it's a dictionary
            if isinstance(school, dict):
                school = SchoolNode(
                    school_id=school.get("school_id"),
                    school_name=school.get("school_name"),
                    address=school.get("address"),
                    type=school.get("type")
                )
            
            # Get parameters for the query
            params = school.to_dict()
            
            # Execute Cypher query to create/update school
            query = SchoolNode.create_query()
            result = await self.neo4j.execute_query(query, params)
            
            if result and len(result) > 0:
                # Create INSTANCE_OF relationship
                if hasattr(school, 'create_instance_of_relationship_query'):
                    await self.neo4j.execute_query(
                        school.create_instance_of_relationship_query(),
                        params
                    )
                    logger.info(f"Created INSTANCE_OF relationship for school {school.school_id}")
                
                logger.info(f"Successfully created/updated school {params['school_id']} in Neo4j")
                return True
            
            logger.error(f"Failed to create/update school {params['school_id']} in Neo4j")
            return False
        except Exception as e:
            logger.error(f"Error creating/updating school in Neo4j: {e}", exc_info=True)
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
        
        try:
            result = await self.neo4j.execute_query(query, params)
            if result and len(result) > 0 and result[0] and result[0][0]:
                # Return a SchoolNode initialized from the record data
                school_data = dict(result[0][0].items())
                return SchoolNode(
                    school_id=school_data.get("school_id"),
                    school_name=school_data.get("school_name"),
                    address=school_data.get("address"),
                    type=school_data.get("type")
                )
            return None
        except Exception as e:
            logger.error(f"Error retrieving school by ID: {e}")
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
            logger.info(f"Successfully deleted school {school_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting school from Neo4j: {e}")
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
            "start_year": start_year,
            "is_active": True,
            "additional_info": "{}"
        }
        
        try:
            await self.neo4j.execute_query(query, params)
            logger.info(f"Added OFFERS_MAJOR relationship between School {school_id} and Major {major_id}")
            return True
        except Exception as e:
            logger.error(f"Error adding OFFERS_MAJOR relationship: {e}")
            return False
    
    async def get_majors(self, school_id):
        """
        Get all majors offered by a school.
        
        Args:
            school_id: ID of the school
            
        Returns:
            List of majors
        """
        query = f"""
        MATCH (s:School {{school_id: $school_id}})-[r:{OFFERS_MAJOR_REL}]->(m:Major)
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
            logger.error(f"Error getting majors for school {school_id}: {e}")
            return []
    
    async def get_students(self, school_id):
        """
        Get all students (candidates) who study at a school.
        
        Args:
            school_id: ID of the school
            
        Returns:
            List of candidates with their education details
        """
        query = f"""
        MATCH (c:Candidate)-[r:{STUDIES_AT_REL}]->(s:School {{school_id: $school_id}})
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
            logger.error(f"Error getting students for school {school_id}: {e}")
            return []
            
    async def get_issued_degrees(self, school_id):
        """
        Get all degrees issued by a school.
        
        Args:
            school_id: ID of the school
            
        Returns:
            List of degrees issued by the school
        """
        query = f"""
        MATCH (d:Degree)-[r:{ISSUED_BY_REL}]->(s:School {{school_id: $school_id}})
        RETURN d, r.issue_date as issue_date, r.education_level as education_level
        """
        params = {"school_id": school_id}
        
        try:
            result = await self.neo4j.execute_query(query, params)
            degrees = []
            
            for record in result:
                degree = record[0]
                issue_date = record[1]
                education_level = record[2]
                
                degrees.append({
                    "degree_id": degree["degree_id"],
                    "issue_date": issue_date,
                    "education_level": education_level,
                    "start_year": degree.get("start_year"),
                    "end_year": degree.get("end_year"),
                    "academic_performance": degree.get("academic_performance")
                })
            
            return degrees
        except Exception as e:
            logger.error(f"Error getting degrees issued by school {school_id}: {e}")
            return [] 