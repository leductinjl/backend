"""
Candidate Graph Repository module.

This module provides methods for interacting with Candidate nodes in Neo4j.
"""

from app.domain.graph_models.candidate_node import CandidateNode
from app.infrastructure.ontology.ontology import RELATIONSHIPS
import logging

logger = logging.getLogger(__name__)

# Import specific relationships
STUDIES_AT_REL = RELATIONSHIPS["STUDIES_AT"]["type"]
ATTENDS_EXAM_REL = RELATIONSHIPS["ATTENDS_EXAM"]["type"]
RECEIVES_SCORE_REL = RELATIONSHIPS["RECEIVES_SCORE"]["type"]
EARNS_CERTIFICATE_REL = RELATIONSHIPS["EARNS_CERTIFICATE"]["type"]
HOLDS_DEGREE_REL = RELATIONSHIPS["HOLDS_DEGREE"]["type"]
INSTANCE_OF_REL = RELATIONSHIPS["INSTANCE_OF"]["type"]
FOR_SUBJECT_REL = RELATIONSHIPS["FOR_SUBJECT"]["type"]
IN_EXAM_REL = RELATIONSHIPS["IN_EXAM"]["type"]
REQUESTS_REVIEW_REL = RELATIONSHIPS["REQUESTS_REVIEW"]["type"]
PROVIDES_CREDENTIAL_REL = RELATIONSHIPS["PROVIDES_CREDENTIAL"]["type"]
RECEIVES_RECOGNITION_REL = RELATIONSHIPS["RECEIVES_RECOGNITION"]["type"]
EARNS_AWARD_REL = RELATIONSHIPS["EARNS_AWARD"]["type"]
ACHIEVES_REL = RELATIONSHIPS["ACHIEVES"]["type"]
STUDIES_MAJOR_REL = RELATIONSHIPS["STUDIES_MAJOR"]["type"]
HAS_EXAM_SCHEDULE_REL = RELATIONSHIPS["HAS_EXAM_SCHEDULE"]["type"]

class CandidateGraphRepository:
    """
    Repository for managing Candidate nodes in Neo4j knowledge graph.
    
    This class provides methods to create, update, and query Candidate nodes
    and their relationships with other entities in the knowledge graph.
    """
    
    def __init__(self, neo4j_connection):
        """Initialize with Neo4j connection."""
        self.neo4j = neo4j_connection
    
    async def create_or_update(self, candidate):
        """
        Create or update a Candidate node in Neo4j.
        
        Args:
            candidate: CandidateNode object or dictionary with candidate data
            
        Returns:
            bool: True if operation successful, False otherwise
        """
        try:
            # Ensure we have a dictionary
            if hasattr(candidate, 'to_dict'):
                params = candidate.to_dict()
                logger.info(f"Converting CandidateNode to dict for {params.get('candidate_id')}")
            else:
                params = candidate
                logger.info(f"Using provided dict for candidate {params.get('candidate_id')}")
            
            # Execute Cypher query to create/update candidate
            query = CandidateNode.create_query()
            logger.info(f"Executing query for candidate {params.get('candidate_id')}")
            
            result = await self.neo4j.execute_query(query, params)
            
            if result and len(result) > 0:
                # Create INSTANCE_OF relationship with Candidate class
                await self._create_instance_of_relationship(params.get('candidate_id'))
                logger.info(f"Successfully created/updated candidate {params.get('candidate_id')} in Neo4j")
                return True
            else:
                logger.error(f"No result returned for candidate {params.get('candidate_id')}")
                return False
                
        except Exception as e:
            logger.error(f"Error creating/updating candidate in Neo4j: {e}", exc_info=True)
            return False
    
    async def _create_instance_of_relationship(self, candidate_id: str):
        """
        Tạo mối quan hệ INSTANCE_OF giữa node instance và class node tương ứng.
        
        Args:
            candidate_id: ID của node instance
        """
        try:
            query = CandidateNode.create_instance_of_relationship_query()
            await self.neo4j.execute_query(query, {"candidate_id": candidate_id})
            logger.info(f"Created INSTANCE_OF relationship for candidate {candidate_id}")
        except Exception as e:
            logger.error(f"Error creating INSTANCE_OF relationship for candidate {candidate_id}: {e}")
            raise
    
    async def get_by_id(self, candidate_id):
        """
        Get a candidate by ID.
        
        Args:
            candidate_id: The ID of the candidate to retrieve
            
        Returns:
            CandidateNode or None if not found
        """
        query = """
        MATCH (c:Candidate {candidate_id: $candidate_id})
        RETURN c
        """
        params = {"candidate_id": candidate_id}
        
        result = await self.neo4j.execute_query(query, params)
        if result and len(result) > 0:
            return CandidateNode.from_record({"c": result[0][0]})
        return None
    
    async def delete(self, candidate_id):
        """
        Delete a candidate from Neo4j.
        
        Args:
            candidate_id: ID of the candidate to delete
            
        Returns:
            bool: True if successful, False otherwise
        """
        query = """
        MATCH (c:Candidate {candidate_id: $candidate_id})
        DETACH DELETE c
        """
        params = {"candidate_id": candidate_id}
        
        try:
            await self.neo4j.execute_query(query, params)
            return True
        except Exception as e:
            print(f"Error deleting candidate from Neo4j: {e}")
            return False
    
    async def add_studies_at_relationship(self, candidate_id, school_id, relationship_data=None):
        """
        Create a relationship between a candidate and a school.
        
        Args:
            candidate_id: ID of the candidate
            school_id: ID of the school
            relationship_data: Additional data for the relationship
            
        Returns:
            bool: True if successful, False otherwise
        """
        query = RELATIONSHIPS["STUDIES_AT"]["create_query"]
        
        # Set default values if not provided
        relationship_data = relationship_data or {}
        params = {
            "candidate_id": candidate_id,
            "school_id": school_id,
            "start_year": relationship_data.get("start_year"),
            "end_year": relationship_data.get("end_year"),
            "education_level": relationship_data.get("education_level")
        }
        
        try:
            await self.neo4j.execute_query(query, params)
            return True
        except Exception as e:
            print(f"Error adding STUDIES_AT relationship: {e}")
            return False
    
    async def add_attends_exam_relationship(self, candidate_id, exam_id, relationship_data=None):
        """
        Create a relationship between a candidate and an exam.
        
        Args:
            candidate_id: ID of the candidate
            exam_id: ID of the exam
            relationship_data: Additional data for the relationship
            
        Returns:
            bool: True if successful, False otherwise
        """
        query = RELATIONSHIPS["ATTENDS_EXAM"]["create_query"]
        
        # Set default values if not provided
        relationship_data = relationship_data or {}
        params = {
            "candidate_id": candidate_id,
            "exam_id": exam_id,
            "registration_number": relationship_data.get("registration_number"),
            "registration_date": relationship_data.get("registration_date"),
            "status": relationship_data.get("status")
        }
        
        try:
            await self.neo4j.execute_query(query, params)
            return True
        except Exception as e:
            print(f"Error adding ATTENDS_EXAM relationship: {e}")
            return False
    
    async def add_earns_certificate_relationship(self, candidate_id, certificate_id):
        """
        Create a relationship between a candidate and a certificate.
        
        Args:
            candidate_id: ID of the candidate
            certificate_id: ID of the certificate
            
        Returns:
            bool: True if successful, False otherwise
        """
        query = RELATIONSHIPS["EARNS_CERTIFICATE"]["create_query"]
        
        params = {
            "candidate_id": candidate_id,
            "certificate_id": certificate_id
        }
        
        try:
            await self.neo4j.execute_query(query, params)
            return True
        except Exception as e:
            print(f"Error adding EARNS_CERTIFICATE relationship: {e}")
        return False
    
    async def add_holds_degree_relationship(self, candidate_id, degree_id):
        """
        Create a relationship between a candidate and a degree.
        
        Args:
            candidate_id: ID of the candidate
            degree_id: ID of the degree
            
        Returns:
            bool: True if successful, False otherwise
        """
        query = RELATIONSHIPS["HOLDS_DEGREE"]["create_query"]
        
        params = {
            "candidate_id": candidate_id,
            "degree_id": degree_id
        }
        
        try:
            await self.neo4j.execute_query(query, params)
            return True
        except Exception as e:
            print(f"Error adding HOLDS_DEGREE relationship: {e}")
        return False
    
    async def get_education_history(self, candidate_id):
        """
        Get a candidate's education history.
        
        Args:
            candidate_id: ID of the candidate
            
        Returns:
            List of education history records
        """
        query = f"""
        MATCH (c:Candidate {{candidate_id: $candidate_id}})-[r:{STUDIES_AT_REL}]->(s:School)
        RETURN s, r
        ORDER BY r.start_year DESC
        """
        params = {"candidate_id": candidate_id}
        
        try:
            result = await self.neo4j.execute_query(query, params)
            education_history = []
            
            for record in result:
                school = record[0]
                relationship = record[1]
                
                education_history.append({
                    "school_id": school["school_id"],
                    "school_name": school["school_name"],
                    "start_year": relationship["start_year"],
                    "end_year": relationship["end_year"],
                    "education_level": relationship["education_level"]
                })
            
            return education_history
        except Exception as e:
            print(f"Error getting education history: {e}")
        return []
    
    async def get_exam_history(self, candidate_id):
        """
        Get a candidate's exam history.
        
        Args:
            candidate_id: ID of the candidate
            
        Returns:
            List of exam history records
        """
        query = f"""
        MATCH (c:Candidate {{candidate_id: $candidate_id}})-[r:{ATTENDS_EXAM_REL}]->(e:Exam)
        OPTIONAL MATCH (c)-[rs:{RECEIVES_SCORE_REL}]->(s:Score)-[fs:{FOR_SUBJECT_REL}]->(sub:Subject)
        OPTIONAL MATCH (s)-[ie:{IN_EXAM_REL}]->(e2:Exam)
        WHERE e2.exam_id = e.exam_id
        RETURN e, r, s, sub
        ORDER BY e.start_date DESC
        """
        params = {"candidate_id": candidate_id}
        
        try:
            result = await self.neo4j.execute_query(query, params)
            exam_history = []
            
            for record in result:
                exam = record[0]
                relationship = record[1]
                score = record[2]
                subject = record[3]
                
                exam_entry = {
                    "exam_id": exam["exam_id"],
                    "exam_name": exam["exam_name"],
                    "exam_type": exam["exam_type"],
                    "start_date": exam["start_date"],
                    "end_date": exam["end_date"],
                    "registration_number": relationship["registration_number"],
                    "registration_date": relationship["registration_date"],
                    "status": relationship["status"],
                    "scores": []
                }
                
                if score and subject:
                    exam_entry["scores"].append({
                        "subject_id": subject["subject_id"],
                        "subject_name": subject["subject_name"],
                        "score_value": score["score_value"]
                    })
                
                exam_history.append(exam_entry)
            
            return exam_history
        except Exception as e:
            print(f"Error getting exam history: {e}")
        return []
    
    async def add_receives_score_relationship(self, candidate_id, score_id, relationship_data=None):
        """
        Create a relationship between a candidate and a score.
        
        Args:
            candidate_id: ID of the candidate
            score_id: ID of the score
            relationship_data: Additional data for the relationship
            
        Returns:
            bool: True if successful, False otherwise
        """
        query = RELATIONSHIPS["RECEIVES_SCORE"]["create_query"]
        
        # Set default values if not provided
        relationship_data = relationship_data or {}
        params = {
            "candidate_id": candidate_id,
            "score_id": score_id,
            "exam_id": relationship_data.get("exam_id"),
            "exam_name": relationship_data.get("exam_name"),
            "subject_id": relationship_data.get("subject_id"),
            "subject_name": relationship_data.get("subject_name"),
            "registration_status": relationship_data.get("registration_status"),
            "registration_date": relationship_data.get("registration_date"),
            "is_required": relationship_data.get("is_required", False),
            "exam_date": relationship_data.get("exam_date")
        }
        
        try:
            await self.neo4j.execute_query(query, params)
            return True
        except Exception as e:
            print(f"Error adding RECEIVES_SCORE relationship: {e}")
            return False
    
    async def add_requests_review_relationship(self, candidate_id, review_id):
        """
        Create a relationship between a candidate and a score review.
        
        Args:
            candidate_id: ID of the candidate
            review_id: ID of the score review
            
        Returns:
            bool: True if successful, False otherwise
        """
        query = RELATIONSHIPS["REQUESTS_REVIEW"]["create_query"]
        
        params = {
            "candidate_id": candidate_id,
            "review_id": review_id
        }
        
        try:
            await self.neo4j.execute_query(query, params)
            return True
        except Exception as e:
            print(f"Error adding REQUESTS_REVIEW relationship: {e}")
            return False
    
    async def add_provides_credential_relationship(self, candidate_id, credential_id):
        """
        Create a relationship between a candidate and a credential.
        
        Args:
            candidate_id: ID of the candidate
            credential_id: ID of the credential
            
        Returns:
            bool: True if successful, False otherwise
        """
        query = RELATIONSHIPS["PROVIDES_CREDENTIAL"]["create_query"]
        
        params = {
            "candidate_id": candidate_id,
            "credential_id": credential_id
        }
        
        try:
            await self.neo4j.execute_query(query, params)
            return True
        except Exception as e:
            print(f"Error adding PROVIDES_CREDENTIAL relationship: {e}")
            return False
    
    async def add_receives_recognition_relationship(self, candidate_id, recognition_id):
        """
        Create a relationship between a candidate and a recognition.
        
        Args:
            candidate_id: ID of the candidate
            recognition_id: ID of the recognition
            
        Returns:
            bool: True if successful, False otherwise
        """
        query = RELATIONSHIPS["RECEIVES_RECOGNITION"]["create_query"]
        
        params = {
            "candidate_id": candidate_id,
            "recognition_id": recognition_id
        }
        
        try:
            await self.neo4j.execute_query(query, params)
            return True
        except Exception as e:
            print(f"Error adding RECEIVES_RECOGNITION relationship: {e}")
            return False
    
    async def add_earns_award_relationship(self, candidate_id, award_id):
        """
        Create a relationship between a candidate and an award.
        
        Args:
            candidate_id: ID of the candidate
            award_id: ID of the award
            
        Returns:
            bool: True if successful, False otherwise
        """
        query = RELATIONSHIPS["EARNS_AWARD"]["create_query"]
        
        params = {
            "candidate_id": candidate_id,
            "award_id": award_id
        }
        
        try:
            await self.neo4j.execute_query(query, params)
            return True
        except Exception as e:
            print(f"Error adding EARNS_AWARD relationship: {e}")
            return False
    
    async def add_achieves_relationship(self, candidate_id, achievement_id):
        """
        Create a relationship between a candidate and an achievement.
        
        Args:
            candidate_id: ID of the candidate
            achievement_id: ID of the achievement
            
        Returns:
            bool: True if successful, False otherwise
        """
        query = RELATIONSHIPS["ACHIEVES"]["create_query"]
        
        params = {
            "candidate_id": candidate_id,
            "achievement_id": achievement_id
        }
        
        try:
            await self.neo4j.execute_query(query, params)
            return True
        except Exception as e:
            print(f"Error adding ACHIEVES relationship: {e}")
            return False
    
    async def add_studies_major_relationship(self, candidate_id, major_id, relationship_data=None):
        """
        Create a relationship between a candidate and a major.
        
        Args:
            candidate_id: ID of the candidate
            major_id: ID of the major
            relationship_data: Additional data for the relationship
            
        Returns:
            bool: True if successful, False otherwise
        """
        query = RELATIONSHIPS["STUDIES_MAJOR"]["create_query"]
        
        # Set default values if not provided
        relationship_data = relationship_data or {}
        params = {
            "candidate_id": candidate_id,
            "major_id": major_id,
            "start_year": relationship_data.get("start_year"),
            "end_year": relationship_data.get("end_year"),
            "education_level": relationship_data.get("education_level"),
            "academic_performance": relationship_data.get("academic_performance"),
            "school_id": relationship_data.get("school_id"),
            "school_name": relationship_data.get("school_name"),
            "additional_info": relationship_data.get("additional_info")
        }
        
        try:
            await self.neo4j.execute_query(query, params)
            return True
        except Exception as e:
            print(f"Error adding STUDIES_MAJOR relationship: {e}")
            return False
    
    async def add_has_exam_schedule_relationship(self, candidate_id, schedule_id, relationship_data=None):
        """
        Create a relationship between a candidate and an exam schedule.
        
        Args:
            candidate_id: ID of the candidate
            schedule_id: ID of the exam schedule
            relationship_data: Additional data for the relationship
            
        Returns:
            bool: True if successful, False otherwise
        """
        query = RELATIONSHIPS["HAS_EXAM_SCHEDULE"]["create_query"]
        
        # Set default values if not provided
        relationship_data = relationship_data or {}
        params = {
            "candidate_id": candidate_id,
            "schedule_id": schedule_id,
            "exam_id": relationship_data.get("exam_id"),
            "exam_name": relationship_data.get("exam_name"),
            "subject_id": relationship_data.get("subject_id"),
            "subject_name": relationship_data.get("subject_name"),
            "registration_status": relationship_data.get("registration_status"),
            "registration_date": relationship_data.get("registration_date"),
            "is_required": relationship_data.get("is_required", False),
            "room_id": relationship_data.get("room_id"),
            "room_name": relationship_data.get("room_name"),
            "seat_number": relationship_data.get("seat_number"),
            "assignment_date": relationship_data.get("assignment_date")
        }
        
        try:
            await self.neo4j.execute_query(query, params)
            return True
        except Exception as e:
            print(f"Error adding HAS_EXAM_SCHEDULE relationship: {e}")
            return False 