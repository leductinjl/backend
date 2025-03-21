"""
Exam Schedule Node model.

This module defines the ExamScheduleNode class for representing ExamSchedule entities in the Neo4j graph.
"""

from datetime import datetime
from typing import Optional, Dict, Any

class ExamScheduleNode:
    """
    Model for ExamSchedule node in Neo4j Knowledge Graph.
    
    Đại diện cho lịch thi trong knowledge graph.
    """
    
    def __init__(
        self, 
        schedule_id,
        exam_subject_id=None,
        start_time=None,
        end_time=None,
        description=None,
        status=None
    ):
        # Thuộc tính định danh - bắt buộc
        self.schedule_id = schedule_id
        
        # Thuộc tính quan hệ - tùy chọn
        self.exam_subject_id = exam_subject_id
        
        # Thuộc tính bổ sung - tùy chọn
        self.start_time = start_time
        self.end_time = end_time
        self.description = description
        self.status = status
        
    @staticmethod
    def create_query():
        """
        Tạo Cypher query để tạo hoặc cập nhật node ExamSchedule.
        
        Query này tuân theo định nghĩa ontology, bao gồm thiết lập nhãn Thing
        và các thuộc tính được định nghĩa trong ontology.
        """
        return """
        MERGE (s:ExamSchedule {schedule_id: $schedule_id})
        ON CREATE SET
            s:Thing, 
            s.exam_subject_id = $exam_subject_id,
            s.start_time = $start_time,
            s.end_time = $end_time,
            s.description = $description,
            s.status = $status,
            s.created_at = datetime()
        ON MATCH SET
            s.exam_subject_id = $exam_subject_id,
            s.start_time = $start_time,
            s.end_time = $end_time,
            s.description = $description,
            s.status = $status,
            s.updated_at = datetime()
        RETURN s
        """
    
    def create_relationships_query(self):
        """
        Tạo Cypher query để thiết lập mối quan hệ giữa ExamSchedule và các node khác.
        """
        return """
        // Thiết lập quan hệ với ExamSubject (nếu có)
        MATCH (s:ExamSchedule {schedule_id: $schedule_id})
        MATCH (es:ExamSubject {exam_subject_id: $exam_subject_id})
        MERGE (s)-[:SCHEDULES]->(es)
        """
    
    def to_dict(self):
        """
        Chuyển đổi thành dictionary để sử dụng trong Neo4j query.
        """
        return {
            "schedule_id": self.schedule_id,
            "exam_subject_id": self.exam_subject_id,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "description": self.description,
            "status": self.status
        }
    
    @classmethod
    def from_sql_model(cls, schedule_model):
        """
        Tạo đối tượng ExamScheduleNode từ SQLAlchemy ExamSchedule model.
        
        Args:
            schedule_model: SQLAlchemy ExamSchedule instance hoặc dictionary
            
        Returns:
            ExamScheduleNode instance
        """
        if isinstance(schedule_model, dict):
            # Trường hợp schedule_model là dictionary
            return cls(
                schedule_id=schedule_model.get('exam_schedule_id'),
                exam_subject_id=schedule_model.get('exam_subject_id'),
                start_time=schedule_model.get('start_time'),
                end_time=schedule_model.get('end_time'),
                description=schedule_model.get('description'),
                status=schedule_model.get('status')
            )
        else:
            # Trường hợp schedule_model là SQLAlchemy model
            return cls(
                schedule_id=getattr(schedule_model, 'exam_schedule_id', None),
                exam_subject_id=getattr(schedule_model, 'exam_subject_id', None),
                start_time=getattr(schedule_model, 'start_time', None),
                end_time=getattr(schedule_model, 'end_time', None),
                description=getattr(schedule_model, 'description', None),
                status=getattr(schedule_model, 'status', None)
            )
    
    @staticmethod
    def from_record(record):
        """
        Tạo đối tượng ExamScheduleNode từ Neo4j record.
        
        Args:
            record: Neo4j record chứa node ExamSchedule
            
        Returns:
            ExamScheduleNode instance
        """
        node = record['s']  # 's' là alias cho schedule trong cypher query
        return ExamScheduleNode(
            schedule_id=node['schedule_id'],
            exam_subject_id=node.get('exam_subject_id'),
            start_time=node.get('start_time'),
            end_time=node.get('end_time'),
            description=node.get('description'),
            status=node.get('status')
        )
    
    def __repr__(self):
        return f"<ExamScheduleNode(schedule_id='{self.schedule_id}', start_time='{self.start_time}')>" 