"""
Exam Location Graph Repository module.

This module provides methods for interacting with ExamLocation nodes in Neo4j.
"""

from app.domain.graph_models.exam_location_node import ExamLocationNode, INSTANCE_OF_REL
from app.infrastructure.ontology.ontology import RELATIONSHIPS
import logging

logger = logging.getLogger(__name__)

# Define relationship constants
HELD_AT_REL = RELATIONSHIPS["HELD_AT"]["type"]
LOCATED_IN_REL = RELATIONSHIPS["LOCATED_IN"]["type"]

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
            
            # Create INSTANCE_OF relationship only
            if result and len(result) > 0:
                # Create INSTANCE_OF relationship
                if hasattr(location, 'create_instance_of_relationship_query'):
                    instance_of_query = location.create_instance_of_relationship_query()
                    await self.neo4j.execute_query(instance_of_query, params)
                logger.info(f"Successfully created/updated exam location {params['location_id']} in Neo4j")
                return True
            return False
        except Exception as e:
            logger.error(f"Error creating/updating exam location in Neo4j: {e}", exc_info=True)
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
        
        try:
            result = await self.neo4j.execute_query(query, params)
            if result and len(result) > 0:
                # Check if the returned node has the expected property
                node = result[0][0]
                if 'location_id' not in node:
                    # Add the location_id to the node data
                    node_dict = dict(node)
                    node_dict['location_id'] = location_id
                    return ExamLocationNode.from_record({"l": node_dict})
                return ExamLocationNode.from_record({"l": node})
            return None
        except Exception as e:
            logger.error(f"Error retrieving exam location {location_id}: {e}")
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
            logger.info(f"Successfully deleted exam location {location_id} from Neo4j")
            return True
        except Exception as e:
            logger.error(f"Error deleting exam location from Neo4j: {e}")
            return False
    
    async def get_exams(self, location_id):
        """
        Get all exams held at a specific location.
        
        Args:
            location_id: ID of the location
            
        Returns:
            List of exams
        """
        query = f"""
        MATCH (e:Exam)-[:{HELD_AT_REL}]->(l:ExamLocation {{location_id: $location_id}})
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
            logger.error(f"Error getting exams for location: {e}")
            return []
    
    async def get_rooms(self, location_id):
        """
        Get all exam rooms within a specific location.
        
        Args:
            location_id: ID of the location
            
        Returns:
            List of exam rooms
        """
        query = f"""
        MATCH (r:ExamRoom)-[:{LOCATED_IN_REL}]->(l:ExamLocation {{location_id: $location_id}})
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
            logger.error(f"Error getting rooms for location: {e}")
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
            logger.error(f"Error getting all exam locations: {e}")
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
        # Instead of using the ontology query directly, we'll create a custom query
        # that doesn't require the missing parameters
        query = """
        MATCH (e:Exam {exam_id: $exam_id})
        MATCH (l:ExamLocation {location_id: $location_id})
        MERGE (e)-[r:HELD_AT]->(l)
        SET r.updated_at = datetime()
        RETURN r
        """
        
        params = {
            "exam_id": exam_id,
            "location_id": location_id
        }
        
        try:
            await self.neo4j.execute_query(query, params)
            logger.info(f"Added HELD_AT relationship between exam {exam_id} and location {location_id}")
            return True
        except Exception as e:
            logger.error(f"Error adding HELD_AT relationship: {e}")
            return False
            
    async def add_hosts_exam_relationship(self, location_id, exam_id):
        """
        Create a HOSTS_EXAM relationship between an ExamLocation and an Exam.
        This is the inverse of HELD_AT relationship.
        
        Args:
            location_id: ID of the location
            exam_id: ID of the exam
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # In Neo4j, we're using the HELD_AT relationship (from Exam to Location)
            # So we just leverage the existing method but swap the order
            return await self.add_held_at_relationship(exam_id, location_id)
        except Exception as e:
            logger.error(f"Error adding HOSTS_EXAM relationship: {e}")
            return False
    
    async def add_has_room_relationship(self, location_id, room_id):
        """
        Create a HAS_ROOM relationship between an ExamLocation and an ExamRoom.
        
        Args:
            location_id: ID of the location
            room_id: ID of the room
            
        Returns:
            bool: True if successful, False otherwise
        """
        query = """
        MATCH (l:ExamLocation {location_id: $location_id})
        MATCH (r:ExamRoom {room_id: $room_id})
        MERGE (l)-[rel:HAS_ROOM]->(r)
        SET rel.updated_at = datetime()
        RETURN rel
        """
        
        params = {
            "location_id": location_id,
            "room_id": room_id
        }
        
        try:
            await self.neo4j.execute_query(query, params)
            logger.info(f"Added HAS_ROOM relationship between location {location_id} and room {room_id}")
            return True
        except Exception as e:
            logger.error(f"Error adding HAS_ROOM relationship: {e}")
            return False 