"""
Exam Room Node model.

This module defines the ExamRoomNode class for representing ExamRoom entities in the Neo4j graph.
"""

from app.infrastructure.ontology.ontology import RELATIONSHIPS, CLASSES

# Define relationship constants
INSTANCE_OF_REL = RELATIONSHIPS["INSTANCE_OF"]["type"]
LOCATED_IN_REL = RELATIONSHIPS["LOCATED_IN"]["type"]

class ExamRoomNode:
    """
    Model for ExamRoom node in Neo4j Knowledge Graph.
    
    Đại diện cho phòng thi trong knowledge graph.
    """
    
    def __init__(
        self, 
        room_id, 
        room_name=None,
        location_id=None,
        capacity=None,
        floor=None,
        room_number=None,
        room_type=None,
        status=None,
        room_facilities=None,
        additional_info=None
    ):
        # Thuộc tính định danh - bắt buộc
        self.room_id = room_id
        self.room_name = room_name or f"Room {room_id}"
        self.name = self.room_name  # Thêm thuộc tính 'name' cho nhất quán với các node khác
        
        # Thuộc tính quan hệ - tùy chọn
        self.location_id = location_id
        
        # Thuộc tính bổ sung - tùy chọn
        self.capacity = capacity
        self.floor = floor
        self.room_number = room_number
        self.room_type = room_type
        self.status = status
        self.room_facilities = room_facilities
        self.additional_info = additional_info
        
    @staticmethod
    def create_query():
        """
        Tạo Cypher query để tạo hoặc cập nhật node ExamRoom.
        
        Query này tuân theo định nghĩa ontology, bao gồm thiết lập nhãn OntologyInstance
        và các thuộc tính được định nghĩa trong ontology.
        """
        return """
        MERGE (r:ExamRoom:OntologyInstance {room_id: $room_id})
        ON CREATE SET
            r.room_name = $room_name,
            r.name = $name,
            r.capacity = $capacity,
            r.floor = $floor,
            r.room_number = $room_number,
            r.room_type = $room_type,
            r.status = $status,
            r.room_facilities = $room_facilities,
            r.additional_info = $additional_info,
            r.created_at = datetime()
        ON MATCH SET
            r.room_name = $room_name,
            r.name = $name,
            r.capacity = $capacity,
            r.floor = $floor,
            r.room_number = $room_number,
            r.room_type = $room_type,
            r.status = $status,
            r.room_facilities = $room_facilities,
            r.additional_info = $additional_info,
            r.updated_at = datetime()
        RETURN r
        """
    
    def create_relationships_query(self):
        """
        Tạo Cypher query để thiết lập các mối quan hệ của ExamRoom.
        
        Returns:
            Query tạo quan hệ với các node khác
        """
        return f"""
        // Tạo quan hệ với ExamLocation nếu có
        MATCH (r:ExamRoom {{room_id: $room_id}})
        OPTIONAL MATCH (l:ExamLocation {{location_id: $location_id}})
        WITH r, l
        WHERE l IS NOT NULL
        MERGE (r)-[:{LOCATED_IN_REL}]->(l)
        """
    
    def create_instance_of_relationship_query(self):
        """
        Tạo Cypher query để thiết lập mối quan hệ INSTANCE_OF giữa node ExamRoom và class definition.
        
        Returns:
            Query tạo quan hệ INSTANCE_OF
        """
        return f"""
        MATCH (r:ExamRoom:OntologyInstance {{room_id: $room_id}})
        MATCH (class:OntologyClass {{id: 'examroom-class'}})
        MERGE (r)-[:{INSTANCE_OF_REL}]->(class)
        """
    
    def to_dict(self):
        """
        Chuyển đổi thành dictionary để sử dụng trong Neo4j query.
        """
        return {
            "room_id": self.room_id,
            "room_name": self.room_name,
            "name": self.name,
            "location_id": self.location_id,
            "capacity": self.capacity,
            "floor": self.floor,
            "room_number": self.room_number,
            "room_type": self.room_type,
            "status": self.status,
            "room_facilities": self.room_facilities,
            "additional_info": self.additional_info
        }
    
    @classmethod
    def from_sql_model(cls, room_model):
        """
        Tạo đối tượng ExamRoomNode từ SQLAlchemy ExamRoom model.
        
        Args:
            room_model: SQLAlchemy ExamRoom instance hoặc dictionary
            
        Returns:
            ExamRoomNode instance
        """
        if isinstance(room_model, dict):
            # Trường hợp room_model là dictionary
            return cls(
                room_id=room_model.get('exam_room_id') or room_model.get('room_id'),
                room_name=room_model.get('room_name'),
                location_id=room_model.get('location_id'),
                capacity=room_model.get('capacity'),
                floor=room_model.get('floor'),
                room_number=room_model.get('room_number'),
                room_type=room_model.get('room_type'),
                status=room_model.get('is_active'),
                room_facilities=room_model.get('room_facilities'),
                additional_info=room_model.get('additional_info')
            )
        else:
            # Trường hợp room_model là SQLAlchemy model
            return cls(
                room_id=getattr(room_model, 'exam_room_id', None) or getattr(room_model, 'room_id', None),
                room_name=getattr(room_model, 'room_name', None),
                location_id=getattr(room_model, 'location_id', None),
                capacity=getattr(room_model, 'capacity', None),
                floor=getattr(room_model, 'floor', None),
                room_number=getattr(room_model, 'room_number', None),
                room_type=getattr(room_model, 'room_type', None),
                status=getattr(room_model, 'is_active', None),
                room_facilities=getattr(room_model, 'room_facilities', None),
                additional_info=getattr(room_model, 'additional_info', None)
            )
        
    @staticmethod
    def from_record(record):
        """
        Tạo đối tượng ExamRoomNode từ Neo4j record.
        
        Args:
            record: Neo4j record chứa node ExamRoom
            
        Returns:
            ExamRoomNode instance
        """
        node = record['r']  # 'r' là alias cho room trong cypher query
        return ExamRoomNode(
            room_id=node['room_id'],
            room_name=node['room_name'],
            capacity=node.get('capacity'),
            floor=node.get('floor'),
            room_number=node.get('room_number'),
            room_type=node.get('room_type'),
            status=node.get('status'),
            room_facilities=node.get('room_facilities'),
            additional_info=node.get('additional_info')
        )
    
    def __repr__(self):
        return f"<ExamRoomNode(room_id='{self.room_id}', room_name='{self.room_name}')>" 