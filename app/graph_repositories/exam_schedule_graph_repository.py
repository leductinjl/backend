"""
Exam Schedule Graph Repository.

This module contains the ExamScheduleGraphRepository class for managing
ExamSchedule nodes in the Neo4j knowledge graph.
"""

import logging
from typing import List, Dict, Any, Optional
from neo4j.exceptions import Neo4jError

from app.domain.graph_models.exam_schedule_node import (
    ExamScheduleNode, INSTANCE_OF_REL, FOLLOWS_SCHEDULE_REL, 
    HAS_EXAM_SCHEDULE_REL, ASSIGNED_TO_REL, SCHEDULES_SUBJECT_REL, SCHEDULE_AT_REL
)
from app.infrastructure.ontology.ontology import RELATIONSHIPS


class ExamScheduleGraphRepository:
    """
    Repository for managing ExamSchedule nodes in the Neo4j knowledge graph.
    
    This repository provides methods for creating, retrieving, updating, and deleting
    ExamSchedule nodes, as well as managing relationships with other nodes.
    """

    def __init__(self, neo4j_service):
        """
        Initialize the repository with a Neo4j connection.
        
        Args:
            neo4j_service: Service for connecting to Neo4j
        """
        self.neo4j = neo4j_service
        self.logger = logging.getLogger(__name__)
    
    async def create_or_update(self, schedule: ExamScheduleNode) -> Dict[str, Any]:
        """
        Create or update an ExamSchedule node in the graph.
        
        Args:
            schedule: ExamScheduleNode object with schedule data
            
        Returns:
            Dictionary representing the created or updated node
        """
        try:
            # Create or update the ExamSchedule node
            result = await self.neo4j.execute_query(
                schedule.create_query(), 
                schedule.to_dict()
            )
            
            # Create INSTANCE_OF relationship if the method exists
            if hasattr(schedule, 'create_instance_of_relationship_query'):
                instance_query = schedule.create_instance_of_relationship_query()
                if instance_query:
                    await self.neo4j.execute_query(instance_query, schedule.to_dict())
            
            if result and len(result) > 0:
                # Avoid directly returning ExamScheduleNode.from_record and just return success
                self.logger.info(f"ExamSchedule node created/updated: {schedule.schedule_id}")
                return schedule.to_dict()  # Return the original dictionary that was used for creation
            
            self.logger.error(f"Failed to create/update ExamSchedule node: {schedule.schedule_id}")
            return None
        except Neo4jError as e:
            self.logger.error(f"Neo4j error creating/updating ExamSchedule: {str(e)}")
            raise
        except Exception as e:
            self.logger.error(f"Error creating/updating ExamSchedule: {str(e)}")
            raise
    
    async def get_by_id(self, schedule_id: str) -> Optional[ExamScheduleNode]:
        """
        Retrieve an ExamSchedule node by its ID.
        
        Args:
            schedule_id: The ID of the schedule to retrieve
            
        Returns:
            ExamScheduleNode if found, None otherwise
        """
        query = """
        MATCH (s:ExamSchedule {schedule_id: $schedule_id})
        RETURN s
        """
        params = {"schedule_id": schedule_id}
        
        try:
            result = await self.neo4j.execute_query(query, params)
            if result and len(result) > 0 and result[0][0]:
                # Create ExamScheduleNode directly from properties
                node_data = dict(result[0][0])
                return ExamScheduleNode(
                    schedule_id=schedule_id,
                    exam_id=node_data.get('exam_id'),
                    subject_id=node_data.get('subject_id'),
                    exam_subject_id=node_data.get('exam_subject_id'),
                    location_id=node_data.get('location_id'),
                    room_id=node_data.get('room_id'),
                    start_time=node_data.get('start_time'),
                    end_time=node_data.get('end_time'),
                    description=node_data.get('description'),
                    status=node_data.get('status'),
                    date=node_data.get('date'),
                    additional_info=node_data.get('additional_info')
                )
            else:
                return None
        except Exception as e:
            self.logger.error(f"Error retrieving ExamSchedule by ID: {str(e)}")
            raise
    
    async def get_by_exam(self, exam_id: str) -> List[ExamScheduleNode]:
        """
        Retrieve all schedules for a specific exam.
        
        Args:
            exam_id: The ID of the exam
            
        Returns:
            List of ExamScheduleNode objects for the exam
        """
        query = f"""
        MATCH (e:Exam {{exam_id: $exam_id}})-[:{FOLLOWS_SCHEDULE_REL}]->(s:ExamSchedule)
        RETURN s
        """
        params = {"exam_id": exam_id}
        
        try:
            result = await self.neo4j.execute_query(query, params)
            schedules = []
            for record in result:
                if record and len(record) > 0 and record[0]:
                    node_data = dict(record[0])
                    schedule = ExamScheduleNode(
                        schedule_id=node_data.get('schedule_id'),
                        exam_id=exam_id,
                        subject_id=node_data.get('subject_id'),
                        exam_subject_id=node_data.get('exam_subject_id'),
                        location_id=node_data.get('location_id'),
                        room_id=node_data.get('room_id'),
                        start_time=node_data.get('start_time'),
                        end_time=node_data.get('end_time'),
                        description=node_data.get('description'),
                        status=node_data.get('status'),
                        date=node_data.get('date'),
                        additional_info=node_data.get('additional_info')
                    )
                    schedules.append(schedule)
            return schedules
        except Exception as e:
            self.logger.error(f"Error retrieving schedules by exam: {str(e)}")
            raise
    
    async def get_by_location(self, location_id: str) -> List[ExamScheduleNode]:
        """
        Retrieve all schedules for a specific location.
        
        Args:
            location_id: The ID of the exam location
            
        Returns:
            List of ExamScheduleNode objects for the location
        """
        query = f"""
        MATCH (s:ExamSchedule)-[:{SCHEDULE_AT_REL}]->(l:ExamLocation {{location_id: $location_id}})
        RETURN s
        """
        params = {"location_id": location_id}
        
        try:
            result = await self.neo4j.execute_query(query, params)
            schedules = []
            for record in result:
                if record and len(record) > 0 and record[0]:
                    node_data = dict(record[0])
                    schedule = ExamScheduleNode(
                        schedule_id=node_data.get('schedule_id'),
                        exam_id=node_data.get('exam_id'),
                        subject_id=node_data.get('subject_id'),
                        exam_subject_id=node_data.get('exam_subject_id'),
                        location_id=location_id,
                        room_id=node_data.get('room_id'),
                        start_time=node_data.get('start_time'),
                        end_time=node_data.get('end_time'),
                        description=node_data.get('description'),
                        status=node_data.get('status'),
                        date=node_data.get('date'),
                        additional_info=node_data.get('additional_info')
                    )
                    # Set name from node data or create a default
                    schedule.name = node_data.get('name', f"Schedule {node_data.get('schedule_id')}")
                    schedules.append(schedule)
            return schedules
        except Exception as e:
            self.logger.error(f"Error retrieving schedules by location: {str(e)}")
            raise
    
    async def get_by_room(self, room_id: str) -> List[ExamScheduleNode]:
        """
        Retrieve all schedules for a specific room.
        
        Args:
            room_id: The ID of the exam room
            
        Returns:
            List of ExamScheduleNode objects for the room
        """
        query = f"""
        MATCH (s:ExamSchedule)-[:{ASSIGNED_TO_REL}]->(r:ExamRoom {{room_id: $room_id}})
        RETURN s
        """
        params = {"room_id": room_id}
        
        try:
            result = await self.neo4j.execute_query(query, params)
            schedules = []
            for record in result:
                if record and len(record) > 0 and record[0]:
                    node_data = dict(record[0])
                    schedule = ExamScheduleNode(
                        schedule_id=node_data.get('schedule_id'),
                        exam_id=node_data.get('exam_id'),
                        subject_id=node_data.get('subject_id'),
                        exam_subject_id=node_data.get('exam_subject_id'),
                        location_id=node_data.get('location_id'),
                        room_id=room_id,
                        start_time=node_data.get('start_time'),
                        end_time=node_data.get('end_time'),
                        description=node_data.get('description'),
                        status=node_data.get('status'),
                        date=node_data.get('date'),
                        additional_info=node_data.get('additional_info')
                    )
                    # Set name from node data or create a default
                    schedule.name = node_data.get('name', f"Schedule {node_data.get('schedule_id')}")
                    schedules.append(schedule)
            return schedules
        except Exception as e:
            self.logger.error(f"Error retrieving schedules by room: {str(e)}")
            raise
    
    async def get_by_subject(self, subject_id: str) -> List[ExamScheduleNode]:
        """
        Retrieve all schedules for a specific subject.
        
        Args:
            subject_id: The ID of the subject
            
        Returns:
            List of ExamScheduleNode objects for the subject
        """
        query = f"""
        MATCH (s:ExamSchedule)-[:{SCHEDULES_SUBJECT_REL}]->(es:ExamSubject)
        WHERE es.subject_id = $subject_id
        RETURN s
        """
        params = {"subject_id": subject_id}
        
        try:
            result = await self.neo4j.execute_query(query, params)
            return [ExamScheduleNode.from_record(record) for record in result]
        except Exception as e:
            self.logger.error(f"Error retrieving schedules by subject: {str(e)}")
            raise
    
    async def get_all_schedules(self) -> List[ExamScheduleNode]:
        """
        Retrieve all ExamSchedule nodes.
        
        Returns:
            List of all ExamScheduleNode objects
        """
        query = """
        MATCH (s:ExamSchedule)
        RETURN s
        """
        
        try:
            result = await self.neo4j.execute_query(query)
            return [ExamScheduleNode.from_record(record) for record in result]
        except Exception as e:
            self.logger.error(f"Error retrieving all schedules: {str(e)}")
            raise
    
    async def delete(self, schedule_id: str) -> bool:
        """
        Delete an ExamSchedule node from the graph.
        
        Args:
            schedule_id: The ID of the schedule to delete
            
        Returns:
            True if successful, False otherwise
        """
        query = """
        MATCH (s:ExamSchedule {schedule_id: $schedule_id})
        DETACH DELETE s
        """
        params = {"schedule_id": schedule_id}
        
        try:
            await self.neo4j.execute_query(query, params)
            self.logger.info(f"ExamSchedule node deleted: {schedule_id}")
            return True
        except Exception as e:
            self.logger.error(f"Error deleting ExamSchedule: {str(e)}")
            return False
    
    async def add_participant(self, schedule_id: str, candidate_id: str, participant_data: Dict[str, Any] = None) -> bool:
        """
        Create a relationship between a Candidate and an ExamSchedule.
        
        Args:
            schedule_id: The ID of the ExamSchedule
            candidate_id: The ID of the Candidate
            participant_data: Additional properties for the relationship
            
        Returns:
            True if successful, False otherwise
        """
        if participant_data is None:
            participant_data = {}
        
        # Merge the default properties with any provided data
        params = {
            "schedule_id": schedule_id,
            "candidate_id": candidate_id,
            "registration_date": participant_data.get("registration_date", None),
            "status": participant_data.get("status", "Registered"),
            "score": participant_data.get("score", None),
            "is_present": participant_data.get("is_present", None),
            "notes": participant_data.get("notes", ""),
            "seat_number": participant_data.get("seat_number", ""),
        }
        
        query = f"""
        MATCH (c:Candidate {{candidate_id: $candidate_id}})
        MATCH (s:ExamSchedule {{schedule_id: $schedule_id}})
        MERGE (c)-[r:{HAS_EXAM_SCHEDULE_REL}]->(s)
        ON CREATE SET
            r.registration_date = $registration_date,
            r.status = $status,
            r.score = $score,
            r.is_present = $is_present,
            r.notes = $notes,
            r.seat_number = $seat_number,
            r.created_at = datetime()
        ON MATCH SET
            r.registration_date = $registration_date,
            r.status = $status,
            r.score = $score,
            r.is_present = $is_present,
            r.notes = $notes,
            r.seat_number = $seat_number,
            r.updated_at = datetime()
        RETURN r
        """
        
        try:
            result = await self.neo4j.execute_query(query, params)
            if result:
                self.logger.info(f"Candidate {candidate_id} added to schedule {schedule_id}")
                return True
            else:
                self.logger.error(f"Failed to add candidate {candidate_id} to schedule {schedule_id}")
                return False
        except Exception as e:
            self.logger.error(f"Error adding participant: {str(e)}")
            return False
    
    async def get_participants(self, schedule_id: str) -> List[Dict[str, Any]]:
        """
        Retrieve all candidates registered for a schedule.
        
        Args:
            schedule_id: The ID of the ExamSchedule
            
        Returns:
            List of Candidates and their relationship data
        """
        query = f"""
        MATCH (c:Candidate)-[r:{HAS_EXAM_SCHEDULE_REL}]->(s:ExamSchedule {{schedule_id: $schedule_id}})
        RETURN c, r
        """
        params = {"schedule_id": schedule_id}
        
        try:
            result = await self.neo4j.execute_query(query, params)
            participants = []
            for record in result:
                candidate = record['c']
                relationship = record['r']
                
                participant_data = {
                    "candidate_id": candidate["candidate_id"],
                    "name": candidate.get("name", ""),
                    "email": candidate.get("email", ""),
                    "registration_date": relationship.get("registration_date"),
                    "status": relationship.get("status"),
                    "score": relationship.get("score"),
                    "is_present": relationship.get("is_present"),
                    "notes": relationship.get("notes"),
                    "seat_number": relationship.get("seat_number")
                }
                participants.append(participant_data)
            
            return participants
        except Exception as e:
            self.logger.error(f"Error retrieving participants: {str(e)}")
            return [] 