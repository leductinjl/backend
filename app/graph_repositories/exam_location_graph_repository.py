"""
Exam Location Graph Repository module.

This module provides methods for interacting with ExamLocation nodes in Neo4j.
"""

from app.domain.graph_models.exam_location_node import ExamLocationNode
from app.infrastructure.ontology.ontology import RELATIONSHIPS

class ExamLocationGraphRepository:
    """
    Repository for managing ExamLocation nodes in Neo4j knowledge graph.
    
    This class provides methods to create, update, and query ExamLocation nodes
    and their relationships with other entities in the knowledge graph.
    """
    
    def __init__(self, neo4j_connection):
        """Initialize with Neo4j connection."""
        self.neo4j = neo4j_connection
    
    async def create_or_update(self, location):
        """
        Create or update an ExamLocation node in Neo4j.
        
        Args:
            location: ExamLocationNode object or dictionary with location data
            
        Returns:
            bool: True if operation successful, False otherwise
        """
        try:
            # Ensure we have a dictionary
            params = location.to_dict() if hasattr(location, 'to_dict') else location
            
            # Execute Cypher query to create/update location
            query = ExamLocationNode.create_query()
            result = await self.neo4j.execute_query(query, params)
            
            if result and len(result) > 0:
                return True
            return False
        except Exception as e:
            print(f"Error creating/updating exam location in Neo4j: {e}")
            return False
    
    async def get_by_id(self, location_id):
        """
        Get an exam location by ID.
        
        Args:
            location_id: The ID of the exam location to retrieve
            
        Returns:
            ExamLocationNode or None if not found
        """
        query = """
        MATCH (l:ExamLocation {location_id: $location_id})
        RETURN l
        """
        params = {"location_id": location_id}
        
        result = await self.neo4j.execute_query(query, params)
        if result and len(result) > 0:
            return ExamLocationNode.from_record({"l": result[0][0]})
        return None
    
    async def delete(self, location_id):
        """
        Delete an exam location from Neo4j.
        
        Args:
            location_id: ID of the exam location to delete
            
        Returns:
            bool: True if successful, False otherwise
        """
        query = """
        MATCH (l:ExamLocation {location_id: $location_id})
        DETACH DELETE l
        """
        params = {"location_id": location_id}
        
        try:
            await self.neo4j.execute_query(query, params)
            return True
        except Exception as e:
            print(f"Error deleting exam location from Neo4j: {e}")
            return False
    
    async def get_exams(self, location_id):
        """
        Get all exams held at a specific location.
        
        Args:
            location_id: ID of the location
            
        Returns:
            List of exams
        """
        query = """
        MATCH (e:Exam)-[:HELD_AT]->(l:ExamLocation {location_id: $location_id})
        RETURN e
        """
        params = {"location_id": location_id}
        
        try:
            result = await self.neo4j.execute_query(query, params)
            exams = []
            
            for record in result:
                from app.domain.graph_models.exam_node import ExamNode
                exam = ExamNode.from_record({"e": record[0]})
                exams.append(exam.to_dict())
            
            return exams
        except Exception as e:
            print(f"Error getting exams for location: {e}")
            return []
    
    async def get_rooms(self, location_id):
        """
        Get all exam rooms within a specific location.
        
        Args:
            location_id: ID of the location
            
        Returns:
            List of exam rooms
        """
        query = """
        MATCH (r:ExamRoom)-[:LOCATED_IN]->(l:ExamLocation {location_id: $location_id})
        RETURN r
        """
        params = {"location_id": location_id}
        
        try:
            result = await self.neo4j.execute_query(query, params)
            rooms = []
            
            for record in result:
                from app.domain.graph_models.exam_room_node import ExamRoomNode
                room = ExamRoomNode.from_record({"r": record[0]})
                rooms.append(room.to_dict())
            
            return rooms
        except Exception as e:
            print(f"Error getting rooms for location: {e}")
            return []
    
    async def get_all_locations(self, limit=100):
        """
        Get all exam locations in the knowledge graph.
        
        Args:
            limit: Maximum number of locations to return
            
        Returns:
            List of exam locations
        """
        query = """
        MATCH (l:ExamLocation)
        RETURN l
        LIMIT $limit
        """
        params = {"limit": limit}
        
        try:
            result = await self.neo4j.execute_query(query, params)
            locations = []
            
            for record in result:
                location = ExamLocationNode.from_record({"l": record[0]})
                locations.append(location.to_dict())
            
            return locations
        except Exception as e:
            print(f"Error getting all exam locations: {e}")
            return []
    
    async def add_held_at_relationship(self, exam_id, location_id):
        """
        Create a HELD_AT relationship between an Exam and an ExamLocation.
        
        Args:
            exam_id: ID of the exam
            location_id: ID of the location
            
        Returns:
            bool: True if successful, False otherwise
        """
        query = RELATIONSHIPS["HELD_AT"]["create_query"]
        
        params = {
            "exam_id": exam_id,
            "location_id": location_id
        }
        
        try:
            await self.neo4j.execute_query(query, params)
            return True
        except Exception as e:
            print(f"Error adding HELD_AT relationship: {e}")
            return False 