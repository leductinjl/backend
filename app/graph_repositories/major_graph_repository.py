"""
Major Graph Repository module.

This module provides methods for interacting with Major nodes in Neo4j.
"""

import logging
from typing import List, Dict, Any, Optional

from app.domain.graph_models.major_node import (
    MajorNode, INSTANCE_OF_REL, OFFERS_MAJOR_REL, STUDIES_MAJOR_REL
)
from app.infrastructure.ontology.ontology import RELATIONSHIPS

class MajorGraphRepository:
    """
    Repository for managing Major nodes in Neo4j knowledge graph.
    
    This class provides methods to create, update, and query Major nodes
    and their relationships with other entities in the knowledge graph.
    """
    
    def __init__(self, neo4j_service):
        """
        Initialize with Neo4j connection.
        
        Args:
            neo4j_service: Service for connecting to Neo4j
        """
        self.neo4j = neo4j_service
        self.logger = logging.getLogger(__name__)
    
    async def create_or_update(self, major: MajorNode) -> Dict[str, Any]:
        """
        Create or update a Major node in Neo4j.
        
        Args:
            major: MajorNode object with major data
            
        Returns:
            Dictionary representing the created or updated node
        """
        try:
            # Create or update the Major node
            result = await self.neo4j.execute_query(
                major.create_query(), 
                major.to_dict()
            )
            
            # Create INSTANCE_OF relationship if the method exists
            if hasattr(major, 'create_instance_of_relationship_query'):
                instance_query = major.create_instance_of_relationship_query()
                if instance_query:
                    await self.neo4j.execute_query(instance_query, major.to_dict())
            
            if result and len(result) > 0:
                self.logger.info(f"Major node created/updated: {major.major_id}")
                # Return the original major data rather than trying to parse the record
                return major.to_dict()
            else:
                self.logger.error(f"Failed to create/update Major node: {major.major_id}")
                return None
        except Exception as e:
            self.logger.error(f"Error creating/updating major in Neo4j: {str(e)}")
            raise
    
    async def get_by_id(self, major_id: str) -> Optional[MajorNode]:
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
        
        try:
            result = await self.neo4j.execute_query(query, params)
            if result and len(result) > 0 and result[0][0] is not None:
                node_data = dict(result[0][0])
                # Create MajorNode directly from the node properties
                return MajorNode(
                    major_id=node_data.get('major_id'),
                    major_name=node_data.get('major_name', f"Major {major_id}"),
                    major_code=node_data.get('major_code'),
                    description=node_data.get('description')
                )
            return None
        except Exception as e:
            self.logger.error(f"Error retrieving major by ID {major_id}: {str(e)}")
            return None  # Return None instead of raising to avoid cascading errors
    
    async def delete(self, major_id: str) -> bool:
        """
        Delete a major from Neo4j.
        
        Args:
            major_id: ID of the major to delete
            
        Returns:
            True if successful, False otherwise
        """
        query = """
        MATCH (m:Major {major_id: $major_id})
        DETACH DELETE m
        """
        params = {"major_id": major_id}
        
        try:
            await self.neo4j.execute_query(query, params)
            self.logger.info(f"Major node deleted: {major_id}")
            return True
        except Exception as e:
            self.logger.error(f"Error deleting major from Neo4j: {str(e)}")
            return False
    
    async def link_major_to_school(self, major_id: str, school_id: str, link_data: Dict[str, Any] = None) -> bool:
        """
        Create a relationship between a Major and a School.
        
        Args:
            major_id: ID of the major
            school_id: ID of the school
            link_data: Additional data for the relationship
            
        Returns:
            True if successful, False otherwise
        """
        if link_data is None:
            link_data = {}
        
        # Use the ontology-defined relationship with properties
        params = {
            "major_id": major_id,
            "school_id": school_id,
            "start_year": link_data.get("start_year"),
            "is_active": link_data.get("is_active", True),
            "additional_info": link_data.get("additional_info", "")
        }
        
        query = f"""
        MATCH (m:Major {{major_id: $major_id}})
        MATCH (s:School {{school_id: $school_id}})
        MERGE (s)-[r:{OFFERS_MAJOR_REL}]->(m)
        ON CREATE SET
            r.start_year = $start_year,
            r.is_active = $is_active,
            r.additional_info = $additional_info,
            r.created_at = datetime()
        ON MATCH SET
            r.start_year = $start_year,
            r.is_active = $is_active,
            r.additional_info = $additional_info,
            r.updated_at = datetime()
        RETURN r
        """
        
        try:
            result = await self.neo4j.execute_query(query, params)
            if result and len(result) > 0:
                self.logger.info(f"Major {major_id} linked to School {school_id}")
                return True
            else:
                self.logger.error(f"Failed to link Major {major_id} to School {school_id}")
                return False
        except Exception as e:
            self.logger.error(f"Error linking major to school: {str(e)}")
            return False
    
    async def link_candidate_to_major(self, candidate_id: str, major_id: str, link_data: Dict[str, Any] = None) -> bool:
        """
        Create a relationship between a Candidate and a Major.
        
        Args:
            candidate_id: ID of the candidate
            major_id: ID of the major
            link_data: Additional data for the relationship
            
        Returns:
            True if successful, False otherwise
        """
        if link_data is None:
            link_data = {}
        
        # Use the ontology-defined relationship with properties
        params = {
            "candidate_id": candidate_id,
            "major_id": major_id,
            "start_year": link_data.get("start_year"),
            "end_year": link_data.get("end_year"),
            "education_level": link_data.get("education_level", "Bachelor"),
            "academic_performance": link_data.get("academic_performance", "Good"),
            "school_id": link_data.get("school_id"),
            "school_name": link_data.get("school_name"),
            "additional_info": link_data.get("additional_info", "")
        }
        
        query = f"""
        MATCH (c:Candidate {{candidate_id: $candidate_id}})
        MATCH (m:Major {{major_id: $major_id}})
        MERGE (c)-[r:{STUDIES_MAJOR_REL}]->(m)
        ON CREATE SET
            r.start_year = $start_year,
            r.end_year = $end_year,
            r.education_level = $education_level,
            r.academic_performance = $academic_performance,
            r.school_id = $school_id,
            r.school_name = $school_name,
            r.additional_info = $additional_info,
            r.created_at = datetime()
        ON MATCH SET
            r.start_year = $start_year,
            r.end_year = $end_year,
            r.education_level = $education_level,
            r.academic_performance = $academic_performance,
            r.school_id = $school_id,
            r.school_name = $school_name,
            r.additional_info = $additional_info,
            r.updated_at = datetime()
        RETURN r
        """
        
        try:
            result = await self.neo4j.execute_query(query, params)
            if result:
                self.logger.info(f"Candidate {candidate_id} linked to Major {major_id}")
                return True
            else:
                self.logger.error(f"Failed to link Candidate {candidate_id} to Major {major_id}")
                return False
        except Exception as e:
            self.logger.error(f"Error linking candidate to major: {str(e)}")
            return False
    
    async def get_schools_offering_major(self, major_id: str) -> List[Dict[str, Any]]:
        """
        Get all schools that offer this major.
        
        Args:
            major_id: ID of the major
            
        Returns:
            List of schools with relationship details
        """
        query = f"""
        MATCH (s:School)-[r:{OFFERS_MAJOR_REL}]->(m:Major {{major_id: $major_id}})
        RETURN s, r
        """
        params = {"major_id": major_id}
        
        try:
            result = await self.neo4j.execute_query(query, params)
            schools = []
            
            for record in result:
                school = record['s']
                relationship = record['r']
                
                schools.append({
                    "school_id": school["school_id"],
                    "school_name": school["school_name"],
                    "address": school.get("address"),
                    "start_year": relationship.get("start_year"),
                    "is_active": relationship.get("is_active"),
                    "additional_info": relationship.get("additional_info")
                })
            
            return schools
        except Exception as e:
            self.logger.error(f"Error getting schools for major: {str(e)}")
            return []
    
    async def get_candidates_studying_major(self, major_id: str) -> List[Dict[str, Any]]:
        """
        Get all candidates who study this major.
        
        Args:
            major_id: ID of the major
            
        Returns:
            List of candidates with their education details
        """
        query = f"""
        MATCH (c:Candidate)-[r:{STUDIES_MAJOR_REL}]->(m:Major {{major_id: $major_id}})
        RETURN c, r
        """
        params = {"major_id": major_id}
        
        try:
            result = await self.neo4j.execute_query(query, params)
            candidates = []
            
            for record in result:
                candidate = record['c']
                relationship = record['r']
                
                candidates.append({
                    "candidate_id": candidate["candidate_id"],
                    "full_name": candidate.get("full_name"),
                    "email": candidate.get("email"),
                    "start_year": relationship.get("start_year"),
                    "end_year": relationship.get("end_year"),
                    "education_level": relationship.get("education_level"),
                    "academic_performance": relationship.get("academic_performance"),
                    "school_id": relationship.get("school_id"),
                    "school_name": relationship.get("school_name")
                })
            
            return candidates
        except Exception as e:
            self.logger.error(f"Error getting candidates for major: {str(e)}")
            return []
    
    async def get_all_majors(self, limit: int = 100) -> List[Dict[str, Any]]:
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
                node = record['m']
                major = MajorNode.from_record({"m": node})
                majors.append(major.to_dict())
            
            return majors
        except Exception as e:
            self.logger.error(f"Error getting all majors: {str(e)}")
            return []
    
    async def find_related_majors(self, major_id: str, relationship_threshold: int = 2) -> List[Dict[str, Any]]:
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
        query = f"""
        // Find majors that are offered by the same schools
        MATCH (m1:Major {{major_id: $major_id}})
        MATCH (m1)<-[:{OFFERS_MAJOR_REL}]-(s:School)-[:{OFFERS_MAJOR_REL}]->(m2:Major)
        WHERE m1 <> m2
        
        WITH m2, count(distinct s) as shared_schools
        
        // Find majors that are studied by the same candidates
        OPTIONAL MATCH (m1:Major {{major_id: $major_id}})
        OPTIONAL MATCH (m1)<-[:{STUDIES_MAJOR_REL}]-(c:Candidate)-[:{STUDIES_MAJOR_REL}]->(m2:Major)
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
                major = record['m2']
                shared_schools = record['shared_schools']
                shared_candidates = record['shared_candidates']
                relationship_score = record['relationship_score']
                
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
            self.logger.error(f"Error finding related majors: {str(e)}")
            return []
    
    async def add_offered_by_relationship(self, major_id: str, school_id: str, start_year: Optional[int] = None) -> bool:
        """
        Create OFFERS_MAJOR relationship between a School and a Major.
        
        Args:
            major_id: ID of the major
            school_id: ID of the school offering the major
            start_year: The year the school started offering this major
            
        Returns:
            True if successful, False otherwise
        """
        # Reuse existing link method
        return await self.link_major_to_school(
            major_id=major_id,
            school_id=school_id,
            link_data={"start_year": start_year} if start_year else {}
        )
    
    async def add_has_major_relationship(self, degree_id: str, major_id: str) -> bool:
        """
        Create a relationship between a Degree and a Major.
        
        Args:
            degree_id: ID of the degree
            major_id: ID of the major
            
        Returns:
            True if successful, False otherwise
        """
        # Define the relationship type from the ontology constants
        HAS_MAJOR_REL = RELATIONSHIPS.get("HAS_MAJOR", {}).get("type", "HAS_MAJOR")
        
        query = f"""
        MATCH (d:Degree {{degree_id: $degree_id}})
        MATCH (m:Major {{major_id: $major_id}})
        MERGE (d)-[r:{HAS_MAJOR_REL}]->(m)
        ON CREATE SET r.created_at = datetime()
        ON MATCH SET r.updated_at = datetime()
        RETURN r
        """
        params = {"degree_id": degree_id, "major_id": major_id}
        
        try:
            result = await self.neo4j.execute_query(query, params)
            if result and len(result) > 0:
                self.logger.info(f"Created relationship between degree {degree_id} and major {major_id}")
                return True
            else:
                self.logger.warning(f"Failed to create relationship between degree {degree_id} and major {major_id}")
                return False
        except Exception as e:
            self.logger.error(f"Error creating degree-major relationship: {str(e)}")
            return False 