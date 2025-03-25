"""
Exam Location Node model.

This module defines the ExamLocationNode class for representing ExamLocation entities in the Neo4j graph.
"""

from app.infrastructure.ontology.ontology import RELATIONSHIPS, CLASSES
import logging

# Define relationship constants
INSTANCE_OF_REL = RELATIONSHIPS["INSTANCE_OF"]["type"]

logger = logging.getLogger(__name__)

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
            l.contact_info_str = $contact_info_str,
            l.contact_website = $contact_website, 
            l.contact_phone = $contact_phone,
            l.contact_email = $contact_email,
            l.additional_info = $additional_info,
            l.created_at = datetime()
        ON MATCH SET
            l.location_name = $location_name,
            l.name = $name,
            l.address = $address,
            l.capacity = $capacity,
            l.coordinates = $coordinates,
            l.status = $status,
            l.contact_info_str = $contact_info_str,
            l.contact_website = $contact_website,
            l.contact_phone = $contact_phone,
            l.contact_email = $contact_email,
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
        MATCH (class:OntologyClass {{id: 'examlocation-class'}})
        MERGE (l)-[:{INSTANCE_OF_REL}]->(class)
        """
    
    def to_dict(self):
        """
        Chuyển đổi thành dictionary để sử dụng trong Neo4j query.
        """
        # Process contact_info to ensure it's compatible with Neo4j
        # Neo4j doesn't support nested objects as properties
        contact_info_str = None
        contact_website = None
        contact_phone = None
        contact_email = None
        
        # Extract individual contact fields if contact_info is a dictionary
        if isinstance(self.contact_info, dict):
            contact_website = self.contact_info.get('website')
            contact_phone = self.contact_info.get('phone')
            contact_email = self.contact_info.get('email')
            import json
            try:
                contact_info_str = json.dumps(self.contact_info)
            except:
                contact_info_str = str(self.contact_info)
        elif self.contact_info is not None:
            contact_info_str = str(self.contact_info)
            
        return {
            "location_id": self.location_id,
            "location_name": self.location_name,
            "name": self.name,
            "address": self.address,
            "capacity": self.capacity,
            "coordinates": self.coordinates,
            "status": self.status,
            # Replace contact_info with serialized string and individual fields
            "contact_info_str": contact_info_str,
            "contact_website": contact_website,
            "contact_phone": contact_phone,
            "contact_email": contact_email,
            "additional_info": self.additional_info
        }
    
    @classmethod
    def from_sql_model(cls, sql_model):
        """
        Tạo đối tượng ExamLocationNode từ SQLAlchemy ExamLocation model.
        
        Args:
            sql_model: SQLAlchemy ExamLocation instance hoặc dictionary
            
        Returns:
            ExamLocationNode instance
        """
        if isinstance(sql_model, dict):
            # Trường hợp location_model là dictionary
            return cls(
                location_id=sql_model.get('exam_location_id') or sql_model.get('location_id'),
                location_name=sql_model.get('location_name'),
                address=sql_model.get('address'),
                capacity=sql_model.get('capacity'),
                coordinates=sql_model.get('coordinates'),
                status=sql_model.get('is_active'),
                contact_info=sql_model.get('contact_info'),
                additional_info=sql_model.get('additional_info')
            )
        else:
            # Trường hợp location_model là SQLAlchemy model
            return cls(
                location_id=getattr(sql_model, 'exam_location_id', None) or getattr(sql_model, 'location_id', None),
                location_name=getattr(sql_model, 'location_name', None),
                address=getattr(sql_model, 'address', None),
                capacity=getattr(sql_model, 'capacity', None),
                coordinates=getattr(sql_model, 'coordinates', None),
                status=getattr(sql_model, 'is_active', None),
                contact_info=getattr(sql_model, 'contact_info', None),
                additional_info=getattr(sql_model, 'additional_info', None)
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
        
        # Ensure location_id is present
        location_id = node.get('location_id')
        if not location_id:
            # Try to get it from the node identity if available
            try:
                if hasattr(node, 'id') and node.id:
                    location_id = f"neo4j_{node.id}"  # Use Neo4j's internal ID as fallback
                else:
                    location_id = "unknown_location"  # Last resort fallback
                logger.warning(f"Missing location_id in Neo4j node, using fallback: {location_id}")
            except Exception as e:
                logger.error(f"Error getting fallback location_id: {e}")
                location_id = "unknown_location"
        
        # Reconstruct contact_info from individual fields if available
        contact_info = None
        if node.get('contact_website') or node.get('contact_phone') or node.get('contact_email'):
            contact_info = {}
            if node.get('contact_website'):
                contact_info['website'] = node.get('contact_website')
            if node.get('contact_phone'):
                contact_info['phone'] = node.get('contact_phone')
            if node.get('contact_email'):
                contact_info['email'] = node.get('contact_email')
        # Fall back to contact_info_str
        elif node.get('contact_info_str'):
            import json
            try:
                contact_info = json.loads(node.get('contact_info_str'))
            except:
                contact_info = node.get('contact_info_str')
        
        return ExamLocationNode(
            location_id=location_id,
            location_name=node.get('location_name', f"Location {location_id}"),
            address=node.get('address'),
            capacity=node.get('capacity'),
            coordinates=node.get('coordinates'),
            status=node.get('status'),
            contact_info=contact_info,
            additional_info=node.get('additional_info')
        )
    
    def __repr__(self):
        return f"<ExamLocationNode(location_id='{self.location_id}', location_name='{self.location_name}')>" 