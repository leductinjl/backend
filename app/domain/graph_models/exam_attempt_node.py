"""
Exam Attempt Node model.

This module defines the ExamAttemptNode class for representing ExamAttempt entities in the Neo4j graph.
"""

from datetime import datetime
from typing import Optional, Dict, Any

class ExamAttemptNode:
    """
    Model for ExamAttempt node in Neo4j Knowledge Graph.
    
    Đại diện cho lần thi của thí sinh trong knowledge graph.
    """
    
    def __init__(
        self, 
        attempt_id, 
        attempt_name=None,
        candidate_id=None,
        exam_id=None,
        schedule_id=None,
        room_id=None,
        status=None,
        start_time=None,
        end_time=None,
        duration=None,
        score=None,
        attempt_number=None,
        submitted=None,
        additional_info=None
    ):
        # Thuộc tính định danh - bắt buộc
        self.attempt_id = attempt_id
        self.attempt_name = attempt_name or f"Attempt {attempt_id}"
        self.name = self.attempt_name  # Thêm thuộc tính 'name' cho nhất quán với các node khác
        
        # Thuộc tính quan hệ - tùy chọn
        self.candidate_id = candidate_id
        self.exam_id = exam_id
        self.schedule_id = schedule_id
        self.room_id = room_id
        
        # Thuộc tính bổ sung - tùy chọn
        self.status = status
        self.start_time = start_time
        self.end_time = end_time
        self.duration = duration
        self.score = score
        self.attempt_number = attempt_number
        self.submitted = submitted
        self.additional_info = additional_info
        
    @staticmethod
    def create_query():
        """
        Tạo Cypher query để tạo hoặc cập nhật node ExamAttempt.
        
        Query này tuân theo định nghĩa ontology, bao gồm thiết lập nhãn Thing
        và các thuộc tính được định nghĩa trong ontology.
        """
        return """
        MERGE (a:ExamAttempt {attempt_id: $attempt_id})
        ON CREATE SET
            a:Thing, 
            a.attempt_name = $attempt_name,
            a.name = $name,
            a.status = $status,
            a.start_time = $start_time,
            a.end_time = $end_time,
            a.duration = $duration,
            a.score = $score,
            a.attempt_number = $attempt_number,
            a.submitted = $submitted,
            a.additional_info = $additional_info,
            a.created_at = datetime()
        ON MATCH SET
            a.attempt_name = $attempt_name,
            a.name = $name,
            a.status = $status,
            a.start_time = $start_time,
            a.end_time = $end_time,
            a.duration = $duration,
            a.score = $score,
            a.attempt_number = $attempt_number,
            a.submitted = $submitted,
            a.additional_info = $additional_info,
            a.updated_at = datetime()
        RETURN a
        """
    
    def create_relationships_query(self):
        """
        Tạo Cypher query để thiết lập các mối quan hệ của ExamAttempt.
        
        Returns:
            Query tạo quan hệ với các node khác
        """
        return """
        // Tạo quan hệ với Candidate nếu có
        OPTIONAL MATCH (c:Candidate {candidate_id: $candidate_id})
        WITH c
        WHERE c IS NOT NULL
        MATCH (a:ExamAttempt {attempt_id: $attempt_id})
        MERGE (c)-[:ATTEMPTED]->(a)
        
        // Tạo quan hệ với Exam nếu có
        WITH a
        OPTIONAL MATCH (e:Exam {exam_id: $exam_id})
        WITH a, e
        WHERE e IS NOT NULL
        MERGE (a)-[:FOR_EXAM]->(e)
        
        // Tạo quan hệ với ExamSchedule nếu có
        WITH a
        OPTIONAL MATCH (s:ExamSchedule {schedule_id: $schedule_id})
        WITH a, s
        WHERE s IS NOT NULL
        MERGE (a)-[:IN_SCHEDULE]->(s)
        
        // Tạo quan hệ với ExamRoom nếu có
        WITH a
        OPTIONAL MATCH (r:ExamRoom {room_id: $room_id})
        WITH a, r
        WHERE r IS NOT NULL
        MERGE (a)-[:IN_ROOM]->(r)
        """
    
    def to_dict(self):
        """
        Chuyển đổi thành dictionary để sử dụng trong Neo4j query.
        """
        result = {
            "attempt_id": self.attempt_id,
            "attempt_name": self.attempt_name,
            "name": self.name,
            "candidate_id": self.candidate_id,
            "exam_id": self.exam_id,
            "schedule_id": self.schedule_id,
            "room_id": self.room_id,
            "status": self.status,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration": self.duration,
            "score": self.score,
            "attempt_number": self.attempt_number,
            "submitted": self.submitted,
            "additional_info": self.additional_info
        }
        
        # Chuyển đổi các đối tượng datetime sang chuỗi nếu cần
        if isinstance(self.start_time, datetime):
            result["start_time"] = self.start_time.isoformat()
            
        if isinstance(self.end_time, datetime):
            result["end_time"] = self.end_time.isoformat()
            
        return result
    
    @classmethod
    def from_sql_model(cls, attempt_model):
        """
        Tạo đối tượng ExamAttemptNode từ SQLAlchemy ExamAttempt model.
        
        Args:
            attempt_model: SQLAlchemy ExamAttempt instance
            
        Returns:
            ExamAttemptNode instance
        """
        return cls(
            attempt_id=attempt_model.attempt_id,
            attempt_name=getattr(attempt_model, 'attempt_name', f"Attempt {attempt_model.attempt_id}"),
            candidate_id=getattr(attempt_model, 'candidate_id', None),
            exam_id=getattr(attempt_model, 'exam_id', None),
            schedule_id=getattr(attempt_model, 'schedule_id', None),
            room_id=getattr(attempt_model, 'room_id', None),
            status=getattr(attempt_model, 'status', None),
            start_time=getattr(attempt_model, 'start_time', None),
            end_time=getattr(attempt_model, 'end_time', None),
            duration=getattr(attempt_model, 'duration', None),
            score=getattr(attempt_model, 'score', None),
            attempt_number=getattr(attempt_model, 'attempt_number', None),
            submitted=getattr(attempt_model, 'submitted', None),
            additional_info=getattr(attempt_model, 'additional_info', None)
        )
        
    @staticmethod
    def from_record(record: Dict[str, Any]) -> 'ExamAttemptNode':
        """
        Tạo đối tượng ExamAttemptNode từ Neo4j record.
        
        Args:
            record: Neo4j record chứa node ExamAttempt
            
        Returns:
            ExamAttemptNode instance
        """
        node = record['a']  # 'a' là alias cho attempt trong cypher query
        
        # Chuyển đổi chuỗi datetime sang đối tượng datetime nếu cần
        start_time = node.get('start_time')
        if isinstance(start_time, str):
            try:
                start_time = datetime.fromisoformat(start_time)
            except ValueError:
                pass
                
        end_time = node.get('end_time')
        if isinstance(end_time, str):
            try:
                end_time = datetime.fromisoformat(end_time)
            except ValueError:
                pass
        
        return ExamAttemptNode(
            attempt_id=node['attempt_id'],
            attempt_name=node.get('attempt_name', f"Attempt {node['attempt_id']}"),
            status=node.get('status'),
            start_time=start_time,
            end_time=end_time,
            duration=node.get('duration'),
            score=node.get('score'),
            attempt_number=node.get('attempt_number'),
            submitted=node.get('submitted'),
            additional_info=node.get('additional_info')
        )
    
    def __repr__(self):
        return f"<ExamAttemptNode(attempt_id='{self.attempt_id}', attempt_name='{self.attempt_name}')>" 