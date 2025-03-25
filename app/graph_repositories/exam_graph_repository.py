"""
Exam graph repository module.

This module defines the ExamGraphRepository class for interacting with Exam nodes in Neo4j.
"""

from app.domain.graph_models.exam_node import ExamNode, INSTANCE_OF_REL
from app.infrastructure.ontology.ontology import RELATIONSHIPS
import logging
import json

logger = logging.getLogger(__name__)

# Import specific relationships
FOLLOWS_SCHEDULE_REL = RELATIONSHIPS["FOLLOWS_SCHEDULE"]["type"]
ORGANIZED_BY_REL = RELATIONSHIPS["ORGANIZED_BY"]["type"]

class ExamGraphRepository:
    """
    Repository for managing Exam nodes in Neo4j.
    """
    
    def __init__(self, neo4j_connection):
        """Initialize with Neo4j connection."""
        self.neo4j = neo4j_connection
    
    async def create_or_update(self, exam):
        """
        Create or update an Exam node in Neo4j.
        
        Args:
            exam: The exam object containing exam data
            
        Returns:
            The created or updated ExamNode
        """
        try:
            # Create or update exam node
            query = ExamNode.create_query()
            params = exam.to_dict() if hasattr(exam, 'to_dict') else exam
            
            result = await self.neo4j.execute_query(query, params)
            if result and len(result) > 0:
                # Create INSTANCE_OF relationship only
                if hasattr(exam, 'create_instance_of_relationship_query'):
                    instance_of_query = exam.create_instance_of_relationship_query()
                    await self.neo4j.execute_query(instance_of_query, params)
                else:
                    # Fallback to repository method for backward compatibility
                    await self._create_instance_of_relationship(params["exam_id"])
                
                logger.info(f"Successfully created/updated exam {params['exam_id']} in Neo4j")
                return True
            return False
        except Exception as e:
            # Log the error
            logger.error(f"Error creating/updating exam in Neo4j: {e}", exc_info=True)
            return False
    
    async def _create_instance_of_relationship(self, exam_id):
        """
        Create INSTANCE_OF relationship between the exam and Exam class node.
        
        Args:
            exam_id: ID of the exam node
        """
        try:
            query = f"""
            MATCH (instance:Exam:OntologyInstance {{exam_id: $exam_id}})
            MATCH (class:OntologyClass {{id: 'exam-class'}})
            MERGE (instance)-[r:{INSTANCE_OF_REL}]->(class)
            RETURN r
            """
            params = {
                "exam_id": exam_id
            }
            await self.neo4j.execute_query(query, params)
            logger.info(f"Created INSTANCE_OF relationship for exam {exam_id}")
            return True
        except Exception as e:
            logger.error(f"Error creating INSTANCE_OF relationship for exam {exam_id}: {e}")
            return False
    
    async def get_by_id(self, exam_id):
        """
        Get an exam by ID.
        
        Args:
            exam_id: The ID of the exam to retrieve
            
        Returns:
            ExamNode or None if not found
        """
        query = """
        MATCH (e:Exam {exam_id: $exam_id})
        RETURN e
        """
        params = {"exam_id": exam_id}
        
        try:
            result = await self.neo4j.execute_query(query, params)
            if result and len(result) > 0 and result[0] and result[0][0]:
                # Lấy dữ liệu từ node Neo4j và chuyển thành dict Python
                exam_data = dict(result[0][0].items())
                return ExamNode(
                    exam_id=exam_data.get("exam_id"),
                    exam_name=exam_data.get("exam_name"),
                    exam_type=exam_data.get("exam_type"),
                    start_date=exam_data.get("start_date"),
                    end_date=exam_data.get("end_date"),
                    scope=exam_data.get("scope")
                )
            return None
        except Exception as e:
            logger.error(f"Error retrieving exam by ID: {e}")
            return None
    
    async def delete(self, exam_id):
        """
        Delete an exam from Neo4j.
        
        Args:
            exam_id: ID of the exam to delete
            
        Returns:
            True if successful, False otherwise
        """
        query = """
        MATCH (e:Exam {exam_id: $exam_id})
        DETACH DELETE e
        """
        params = {"exam_id": exam_id}
        
        try:
            await self.neo4j.execute_query(query, params)
            return True
        except Exception as e:
            print(f"Error deleting exam from Neo4j: {e}")
            return False
    
    async def add_includes_subject_relationship(self, exam_id, subject_id, relationship_data=None):
        """
        Create a relationship between an exam and a subject.
        
        Args:
            exam_id: ID of the exam
            subject_id: ID of the subject
            relationship_data: Additional data for the relationship
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Sử dụng query tùy chỉnh thay vì query mặc định từ RELATIONSHIPS
            query = """
            MATCH (e:Exam {exam_id: $exam_id})
            MATCH (s:Subject {subject_id: $subject_id})
            MERGE (e)-[r:INCLUDES_SUBJECT]->(s)
            SET r.exam_date = $exam_date,
                r.duration_minutes = $duration_minutes,
                r.weight = $weight,
                r.passing_score = $passing_score,
                r.max_score = $max_score,
                r.is_required = $is_required,
                r.additional_info = $additional_info,
                r.updated_at = datetime()
            RETURN r
            """
            
            # Đảm bảo relationship_data không là None
            if relationship_data is None:
                relationship_data = {}
            
            # Chuyển đổi các đối tượng phức tạp thành chuỗi nếu cần
            additional_info = relationship_data.get("additional_info", "")
            if isinstance(additional_info, dict):
                additional_info = json.dumps(additional_info)
                
            params = {
                "exam_id": exam_id,
                "subject_id": subject_id,
                "exam_date": relationship_data.get("exam_date"),
                "duration_minutes": relationship_data.get("duration_minutes"),
                "weight": relationship_data.get("weight", 1.0),
                "passing_score": relationship_data.get("passing_score", 0),
                "max_score": relationship_data.get("max_score", 10),
                "is_required": relationship_data.get("is_required", True),
                "additional_info": additional_info
                # Bỏ thuộc tính subject_metadata vì nó là đối tượng phức tạp
            }
            
            await self.neo4j.execute_query(query, params)
            logger.info(f"Added INCLUDES_SUBJECT relationship between exam {exam_id} and subject {subject_id}")
            return True
        except Exception as e:
            logger.error(f"Error adding INCLUDES_SUBJECT relationship: {e}")
            return False
    
    async def add_held_at_relationship(self, exam_id, location_id, relationship_data=None):
        """
        Create a relationship between an exam and a location.
        
        Args:
            exam_id: ID of the exam
            location_id: ID of the location
            relationship_data: Additional data for the relationship
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Sử dụng query tùy chỉnh thay vì query mặc định từ RELATIONSHIPS
            query = """
            MATCH (e:Exam {exam_id: $exam_id})
            MATCH (l:ExamLocation {location_id: $location_id})
            MERGE (e)-[r:HELD_AT]->(l)
            SET r.is_primary = $is_primary,
                r.is_active = $is_active,
                r.mapping_metadata_str = $mapping_metadata_str,
                r.updated_at = datetime()
            RETURN r
            """
            
            # Đảm bảo relationship_data không là None
            if relationship_data is None:
                relationship_data = {}
            
            # Chuyển đổi mapping_metadata từ đối tượng phức tạp thành chuỗi JSON
            mapping_metadata = relationship_data.get("mapping_metadata", {})
            mapping_metadata_str = ""
            if isinstance(mapping_metadata, dict) and mapping_metadata:
                mapping_metadata_str = json.dumps(mapping_metadata)
                
            params = {
                "exam_id": exam_id,
                "location_id": location_id,
                "is_primary": relationship_data.get("is_primary", True),
                "is_active": relationship_data.get("is_active", True),
                "mapping_metadata_str": mapping_metadata_str
            }
            
            await self.neo4j.execute_query(query, params)
            logger.info(f"Added HELD_AT relationship between exam {exam_id} and location {location_id}")
            return True
        except Exception as e:
            logger.error(f"Error adding HELD_AT relationship: {e}")
            return False
    
    async def add_follows_schedule_relationship(self, exam_id, schedule_id):
        """
        Create a relationship between an exam and an exam schedule.
        
        Args:
            exam_id: ID of the exam
            schedule_id: ID of the exam schedule
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Sử dụng query tùy chỉnh thay vì query mặc định từ RELATIONSHIPS
            query = """
            MATCH (e:Exam {exam_id: $exam_id})
            MATCH (s:ExamSchedule {schedule_id: $schedule_id})
            MERGE (e)-[r:FOLLOWS_SCHEDULE]->(s)
            SET r.updated_at = datetime()
            RETURN r
            """
            
            params = {
                "exam_id": exam_id,
                "schedule_id": schedule_id
            }
            
            await self.neo4j.execute_query(query, params)
            logger.info(f"Added FOLLOWS_SCHEDULE relationship between exam {exam_id} and schedule {schedule_id}")
            return True
        except Exception as e:
            logger.error(f"Error adding FOLLOWS_SCHEDULE relationship: {e}")
            return False
    
    async def add_organized_by_relationship(self, exam_id, unit_id, relationship_data=None):
        """
        Create a relationship between an exam and a management unit.
        
        Args:
            exam_id: ID of the exam
            unit_id: ID of the management unit
            relationship_data: Additional data for the relationship
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Use a custom query that handles null values
            query = """
            MATCH (e:Exam {exam_id: $exam_id})
            MATCH (m:ManagementUnit {unit_id: $unit_id})
            MERGE (e)-[r:ORGANIZED_BY]->(m)
            """
            
            # Set default values if not provided
            relationship_data = relationship_data or {}
            
            # Thiết lập các thuộc tính cơ bản
            params = {
                "exam_id": exam_id,
                "unit_id": unit_id,
                "is_primary": relationship_data.get("is_primary", True),
                "role": relationship_data.get("role", "Primary"),
                "status": relationship_data.get("status", "Active")
            }
            
            # Tạo phần SET động dựa trên những thuộc tính có giá trị
            set_clause = """
            SET r.is_primary = $is_primary,
                r.role = $role,
                r.status = $status,
                r.updated_at = datetime()
            """
            
            # Thêm organization_date vào SET clause chỉ khi nó không null
            organization_date = relationship_data.get("organization_date")
            if organization_date is not None:
                set_clause += ", r.organization_date = $organization_date"
                params["organization_date"] = organization_date
            
            # Hoàn thiện truy vấn
            query += set_clause + " RETURN r"
            
            await self.neo4j.execute_query(query, params)
            logger.info(f"Added ORGANIZED_BY relationship between exam {exam_id} and unit {unit_id}")
            return True
        except Exception as e:
            logger.error(f"Error adding ORGANIZED_BY relationship: {e}")
            return False 