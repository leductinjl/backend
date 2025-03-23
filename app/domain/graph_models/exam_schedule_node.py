"""
Exam Schedule Node model.

This module defines the ExamScheduleNode class for representing ExamSchedule entities in the Neo4j graph.
"""

from datetime import datetime
from typing import Optional, Dict, Any
from app.infrastructure.ontology.ontology import RELATIONSHIPS, CLASSES

# Define relationship constants
INSTANCE_OF_REL = RELATIONSHIPS["INSTANCE_OF"]["type"]
FOLLOWS_SCHEDULE_REL = RELATIONSHIPS["FOLLOWS_SCHEDULE"]["type"]
HAS_EXAM_SCHEDULE_REL = RELATIONSHIPS["HAS_EXAM_SCHEDULE"]["type"]
ASSIGNED_TO_REL = RELATIONSHIPS["ASSIGNED_TO"]["type"]
SCHEDULES_SUBJECT_REL = RELATIONSHIPS["SCHEDULES_SUBJECT"]["type"]
SCHEDULE_AT_REL = RELATIONSHIPS["SCHEDULE_AT"]["type"]

class ExamScheduleNode:
    """
    Model for ExamSchedule node in Neo4j Knowledge Graph.
    
    Đại diện cho lịch thi trong knowledge graph.
    """
    
    def __init__(
        self, 
        schedule_id,
        exam_id=None,
        subject_id=None,
        exam_subject_id=None,
        location_id=None,
        room_id=None,
        start_time=None,
        end_time=None,
        description=None,
        status=None,
        date=None,
        additional_info=None
    ):
        # Thuộc tính định danh - bắt buộc
        self.schedule_id = schedule_id
        
        # Tên hiển thị cho node
        self.name = f"Schedule {schedule_id}"
        
        # Thuộc tính quan hệ - tùy chọn
        self.exam_id = exam_id
        self.subject_id = subject_id
        self.exam_subject_id = exam_subject_id
        self.location_id = location_id
        self.room_id = room_id
        
        # Thuộc tính bổ sung - tùy chọn
        self.start_time = start_time
        self.end_time = end_time
        self.description = description
        self.status = status
        self.date = date
        self.additional_info = additional_info
        
    @staticmethod
    def create_query():
        """
        Tạo Cypher query để tạo hoặc cập nhật node ExamSchedule.
        
        Query này tuân theo định nghĩa ontology, bao gồm thiết lập nhãn OntologyInstance
        và các thuộc tính được định nghĩa trong ontology.
        """
        return """
        MERGE (s:ExamSchedule:OntologyInstance {schedule_id: $schedule_id})
        ON CREATE SET
            s.name = $name,
            s.exam_id = $exam_id,
            s.subject_id = $subject_id,
            s.exam_subject_id = $exam_subject_id,
            s.location_id = $location_id,
            s.room_id = $room_id,
            s.start_time = $start_time,
            s.end_time = $end_time,
            s.description = $description,
            s.status = $status,
            s.date = $date,
            s.additional_info = $additional_info,
            s.created_at = datetime()
        ON MATCH SET
            s.name = $name,
            s.exam_id = $exam_id,
            s.subject_id = $subject_id,
            s.exam_subject_id = $exam_subject_id,
            s.location_id = $location_id,
            s.room_id = $room_id,
            s.start_time = $start_time,
            s.end_time = $end_time,
            s.description = $description,
            s.status = $status,
            s.date = $date,
            s.additional_info = $additional_info,
            s.updated_at = datetime()
        RETURN s
        """
    
    def create_relationships_query(self):
        """
        Tạo Cypher query để thiết lập mối quan hệ giữa ExamSchedule và các node khác.
        """
        query_parts = []
        
        # Quan hệ với Exam
        if self.exam_id:
            query_parts.append(f"""
            // Thiết lập quan hệ với Exam (nếu có)
            MATCH (s:ExamSchedule {{schedule_id: $schedule_id}})
            MATCH (e:Exam {{exam_id: $exam_id}})
            MERGE (e)-[:{FOLLOWS_SCHEDULE_REL}]->(s)
            """)
        
        # Quan hệ với ExamSubject (nếu có)
        if self.exam_subject_id:
            if query_parts:
                query_parts.append("WITH s")
            query_parts.append(f"""
            // Thiết lập quan hệ với ExamSubject (nếu có)
            MATCH (s:ExamSchedule {{schedule_id: $schedule_id}})
            MATCH (es:ExamSubject {{exam_subject_id: $exam_subject_id}})
            MERGE (s)-[:{SCHEDULES_SUBJECT_REL}]->(es)
            """)
        
        # Quan hệ với ExamRoom (nếu có)
        if self.room_id:
            if query_parts:
                query_parts.append("WITH s")
            query_parts.append(f"""
            // Thiết lập quan hệ với ExamRoom (nếu có)
            MATCH (s:ExamSchedule {{schedule_id: $schedule_id}})
            MATCH (r:ExamRoom {{room_id: $room_id}})
            MERGE (s)-[:{ASSIGNED_TO_REL}]->(r)
            """)
        
        # Quan hệ với ExamLocation (nếu có)
        if self.location_id:
            if query_parts:
                query_parts.append("WITH s")
            query_parts.append(f"""
            // Thiết lập quan hệ với ExamLocation (nếu có)
            MATCH (s:ExamSchedule {{schedule_id: $schedule_id}})
            MATCH (l:ExamLocation {{location_id: $location_id}})
            MERGE (s)-[:{SCHEDULE_AT_REL}]->(l)
            """)
        
        return '\n'.join(query_parts) if query_parts else ""
    
    def create_instance_of_relationship_query(self):
        """
        Tạo Cypher query để thiết lập mối quan hệ INSTANCE_OF giữa node ExamSchedule và class definition.
        
        Returns:
            Query tạo quan hệ INSTANCE_OF
        """
        return f"""
        MATCH (s:ExamSchedule:OntologyInstance {{schedule_id: $schedule_id}})
        MATCH (class:OntologyClass {{id: 'examschedule-class'}})
        MERGE (s)-[:{INSTANCE_OF_REL}]->(class)
        """
    
    def to_dict(self):
        """
        Chuyển đổi thành dictionary để sử dụng trong Neo4j query.
        """
        return {
            "schedule_id": self.schedule_id,
            "name": self.name,
            "exam_id": self.exam_id,
            "subject_id": self.subject_id,
            "exam_subject_id": self.exam_subject_id,
            "location_id": self.location_id,
            "room_id": self.room_id,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "description": self.description,
            "status": self.status,
            "date": self.date,
            "additional_info": self.additional_info,
            # Các thuộc tính mặc định cho mối quan hệ (có thể được ghi đè bởi tham số)
            "assigned_date": datetime.now().isoformat() if self.room_id else None,
            "is_confirmed": True,
            "is_primary": True,
            "is_active": True,
            "assignment_date": datetime.now().isoformat() if self.location_id else None,
            "notes": "",
            "duration_minutes": 0,
            "max_score": 100,
            "passing_score": 50,
            "weight": 1.0,
            "is_required": True
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
            schedule_id = schedule_model.get('exam_schedule_id') or schedule_model.get('schedule_id')
            
            # Tạo tên có ý nghĩa nếu có thông tin
            name = f"Schedule {schedule_id}"
            exam_name = schedule_model.get('exam_name')
            subject_name = schedule_model.get('subject_name')
            start_time = schedule_model.get('start_time')
            
            if exam_name and subject_name and start_time:
                formatted_time = start_time.strftime("%d/%m/%Y %H:%M") if hasattr(start_time, 'strftime') else start_time
                name = f"{exam_name} - {subject_name} ({formatted_time})"
            elif exam_name and subject_name:
                name = f"{exam_name} - {subject_name}"
            
            return cls(
                schedule_id=schedule_id,
                exam_id=schedule_model.get('exam_id'),
                subject_id=schedule_model.get('subject_id'),
                exam_subject_id=schedule_model.get('exam_subject_id'),
                location_id=schedule_model.get('location_id'),
                room_id=schedule_model.get('room_id'),
                start_time=schedule_model.get('start_time'),
                end_time=schedule_model.get('end_time'),
                description=schedule_model.get('description'),
                status=schedule_model.get('status'),
                date=schedule_model.get('date'),
                additional_info=schedule_model.get('additional_info')
            )
        else:
            # Trường hợp schedule_model là SQLAlchemy model
            schedule_id = getattr(schedule_model, 'exam_schedule_id', None) or getattr(schedule_model, 'schedule_id', None)
            
            # Tạo tên có ý nghĩa từ thông tin khác
            name = f"Schedule {schedule_id}"
            
            # Lấy thông tin từ các quan hệ nếu có
            exam_name = getattr(schedule_model, 'exam_name', None)
            subject_name = getattr(schedule_model, 'subject_name', None)
            start_time = getattr(schedule_model, 'start_time', None)
            
            if exam_name and subject_name and start_time:
                formatted_time = start_time.strftime("%d/%m/%Y %H:%M") if hasattr(start_time, 'strftime') else start_time
                name = f"{exam_name} - {subject_name} ({formatted_time})"
            elif exam_name and subject_name:
                name = f"{exam_name} - {subject_name}"
            
            node = cls(
                schedule_id=schedule_id,
                exam_id=getattr(schedule_model, 'exam_id', None),
                subject_id=getattr(schedule_model, 'subject_id', None),
                exam_subject_id=getattr(schedule_model, 'exam_subject_id', None),
                location_id=getattr(schedule_model, 'location_id', None),
                room_id=getattr(schedule_model, 'room_id', None),
                start_time=getattr(schedule_model, 'start_time', None),
                end_time=getattr(schedule_model, 'end_time', None),
                description=getattr(schedule_model, 'description', None),
                status=getattr(schedule_model, 'status', None),
                date=getattr(schedule_model, 'date', None),
                additional_info=getattr(schedule_model, 'additional_info', None)
            )
            
            # Thêm tên có ý nghĩa
            node.name = name
            return node
    
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
        schedule_id = node['schedule_id']
        
        # Tạo tên có ý nghĩa nếu có thể
        name = node.get('name', f"Schedule {schedule_id}")
        
        result = ExamScheduleNode(
            schedule_id=schedule_id,
            exam_id=node.get('exam_id'),
            subject_id=node.get('subject_id'),
            exam_subject_id=node.get('exam_subject_id'),
            location_id=node.get('location_id'),
            room_id=node.get('room_id'),
            start_time=node.get('start_time'),
            end_time=node.get('end_time'),
            description=node.get('description'),
            status=node.get('status'),
            date=node.get('date'),
            additional_info=node.get('additional_info')
        )
        
        # Đảm bảo name được thiết lập
        result.name = name
        return result
    
    def __repr__(self):
        return f"<ExamScheduleNode(schedule_id='{self.schedule_id}', start_time='{self.start_time}')>" 