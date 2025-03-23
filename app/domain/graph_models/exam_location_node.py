"""
Exam Location Node model.

This module defines the ExamLocationNode class for representing ExamLocation entities in the Neo4j graph.
"""

from app.infrastructure.ontology.ontology import RELATIONSHIPS, CLASSES

# Define relationship constants
INSTANCE_OF_REL = RELATIONSHIPS["INSTANCE_OF"]["type"]

class ExamLocationNode:
    """
    Model for ExamLocation node in Neo4j Knowledge Graph.
    
    Đại diện cho địa điểm thi trong knowledge graph.
    """
    
    def __init__(
        self, 
        location_id,
        location_name=None,
        address=None,
        capacity=None,
        coordinates=None,
        status=None,
        contact_info=None,
        additional_info=None
    ):
        # Thuộc tính định danh - bắt buộc
        self.location_id = location_id
        self.location_name = location_name or f"Location {location_id}"
        self.name = self.location_name  # Thêm thuộc tính 'name' cho nhất quán với các node khác
        
        # Thuộc tính bổ sung - tùy chọn
        self.address = address
        self.capacity = capacity
        self.coordinates = coordinates
        self.status = status
        self.contact_info = contact_info
        self.additional_info = additional_info
        
    @staticmethod
    def create_query():
        """
        Tạo Cypher query để tạo hoặc cập nhật node ExamLocation.
        
        Query này tuân theo định nghĩa ontology, bao gồm thiết lập nhãn OntologyInstance
        và các thuộc tính được định nghĩa trong ontology.
        """
        return """
        MERGE (l:ExamLocation:OntologyInstance {location_id: $location_id})
        ON CREATE SET
            l.location_name = $location_name,
            l.name = $name,
            l.address = $address,
            l.capacity = $capacity,
            l.coordinates = $coordinates,
            l.status = $status,
            l.contact_info = $contact_info,
            l.additional_info = $additional_info,
            l.created_at = datetime()
        ON MATCH SET
            l.location_name = $location_name,
            l.name = $name,
            l.address = $address,
            l.capacity = $capacity,
            l.coordinates = $coordinates,
            l.status = $status,
            l.contact_info = $contact_info,
            l.additional_info = $additional_info,
            l.updated_at = datetime()
        RETURN l
        """
    
    def create_relationships_query(self):
        """
        Tạo Cypher query để thiết lập các mối quan hệ của ExamLocation.
        
        Returns:
            Query tạo quan hệ với các node khác
        """
        # Currently, ExamLocation doesn't have predefined relationships in the model
        # Return an empty string to indicate no relationships to establish
        return ""
    
    def create_instance_of_relationship_query(self):
        """
        Tạo Cypher query để thiết lập mối quan hệ INSTANCE_OF giữa node ExamLocation và class definition.
        
        Returns:
            Query tạo quan hệ INSTANCE_OF
        """
        return f"""
        MATCH (l:ExamLocation:OntologyInstance {{location_id: $location_id}})
        MATCH (class:OntologyClass {{id: 'exam-location-class'}})
        MERGE (l)-[:{INSTANCE_OF_REL}]->(class)
        """
    
    def to_dict(self):
        """
        Chuyển đổi thành dictionary để sử dụng trong Neo4j query.
        """
        return {
            "location_id": self.location_id,
            "location_name": self.location_name,
            "name": self.name,
            "address": self.address,
            "capacity": self.capacity,
            "coordinates": self.coordinates,
            "status": self.status,
            "contact_info": self.contact_info,
            "additional_info": self.additional_info
        }
    
    @classmethod
    def from_sql_model(cls, location_model):
        """
        Tạo đối tượng ExamLocationNode từ SQLAlchemy ExamLocation model.
        
        Args:
            location_model: SQLAlchemy ExamLocation instance hoặc dictionary
            
        Returns:
            ExamLocationNode instance
        """
        if isinstance(location_model, dict):
            # Trường hợp location_model là dictionary
            return cls(
                location_id=location_model.get('exam_location_id') or location_model.get('location_id'),
                location_name=location_model.get('location_name'),
                address=location_model.get('address'),
                capacity=location_model.get('capacity'),
                coordinates=location_model.get('coordinates'),
                status=location_model.get('is_active'),
                contact_info=location_model.get('contact_info'),
                additional_info=location_model.get('additional_info')
            )
        else:
            # Trường hợp location_model là SQLAlchemy model
            return cls(
                location_id=getattr(location_model, 'exam_location_id', None) or getattr(location_model, 'location_id', None),
                location_name=getattr(location_model, 'location_name', None),
                address=getattr(location_model, 'address', None),
                capacity=getattr(location_model, 'capacity', None),
                coordinates=getattr(location_model, 'coordinates', None),
                status=getattr(location_model, 'is_active', None),
                contact_info=getattr(location_model, 'contact_info', None),
                additional_info=getattr(location_model, 'additional_info', None)
            )
        
    @staticmethod
    def from_record(record):
        """
        Tạo đối tượng ExamLocationNode từ Neo4j record.
        
        Args:
            record: Neo4j record chứa node ExamLocation
            
        Returns:
            ExamLocationNode instance
        """
        node = record['l']  # 'l' là alias cho location trong cypher query
        return ExamLocationNode(
            location_id=node['location_id'],
            location_name=node['location_name'],
            address=node.get('address'),
            capacity=node.get('capacity'),
            coordinates=node.get('coordinates'),
            status=node.get('status'),
            contact_info=node.get('contact_info'),
            additional_info=node.get('additional_info')
        )
    
    def __repr__(self):
        return f"<ExamLocationNode(location_id='{self.location_id}', location_name='{self.location_name}')>" 