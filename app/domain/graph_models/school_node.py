"""
School Node model.

This module defines the SchoolNode class for representing School entities in the Neo4j graph.
"""

from app.infrastructure.ontology.ontology import RELATIONSHIPS, CLASSES

# Import specific relationships
INSTANCE_OF_REL = RELATIONSHIPS["INSTANCE_OF"]["type"]
OFFERS_MAJOR_REL = RELATIONSHIPS["OFFERS_MAJOR"]["type"]
STUDIES_AT_REL = RELATIONSHIPS["STUDIES_AT"]["type"]
ISSUED_BY_REL = RELATIONSHIPS["ISSUED_BY"]["type"]

class SchoolNode:
    """
    Model for School node in Neo4j Knowledge Graph.
    
    Đại diện cho trường học, đại học, hoặc các cơ sở giáo dục khác
    trong knowledge graph.
    """
    
    def __init__(self, school_id, school_name, address=None, type=None):
        # Thuộc tính định danh - bắt buộc
        self.school_id = school_id
        self.school_name = school_name
        self.name = school_name  # Thêm thuộc tính 'name' cho nhất quán với các node khác
        
        # Thuộc tính bổ sung cho truy vấn - tùy chọn
        self.address = address
        self.type = type  # Loại trường (đại học, cao đẳng, THPT, ...)
        
    @staticmethod
    def create_query():
        """
        Tạo Cypher query để tạo hoặc cập nhật node School.
        
        Query này tuân theo định nghĩa ontology, bao gồm thiết lập nhãn OntologyInstance
        và các thuộc tính được định nghĩa trong ontology.
        """
        return """
        MERGE (s:School:OntologyInstance {school_id: $school_id})
        ON CREATE SET
            s:Thing,
            s.school_name = $school_name,
            s.name = $name,
            s.address = $address,
            s.type = $type,
            s.created_at = datetime()
        ON MATCH SET
            s.school_name = $school_name,
            s.name = $name,
            s.address = $address,
            s.type = $type,
            s.updated_at = datetime()
        RETURN s
        """
    
    def create_instance_of_relationship_query(self):
        """
        Tạo Cypher query để thiết lập mối quan hệ INSTANCE_OF giữa node School và class definition.
        
        Returns:
            Query tạo quan hệ INSTANCE_OF
        """
        return f"""
        MATCH (s:School:OntologyInstance {{school_id: $school_id}})
        MATCH (class:OntologyClass {{id: 'school-class'}})
        MERGE (s)-[:{INSTANCE_OF_REL}]->(class)
        """
    
    def to_dict(self):
        """
        Chuyển đổi thành dictionary để sử dụng trong Neo4j query.
        """
        return {
            "school_id": self.school_id,
            "school_name": self.school_name,
            "name": self.name,
            "address": self.address,
            "type": self.type
        }
    
    @classmethod
    def from_sql_model(cls, school_model):
        """
        Tạo đối tượng SchoolNode từ SQLAlchemy School model.
        
        Args:
            school_model: SQLAlchemy School instance
            
        Returns:
            SchoolNode instance
        """
        return cls(
            school_id=school_model.school_id,
            school_name=school_model.school_name,
            address=school_model.address,
            type=None  # Có thể thêm type nếu model PostgreSQL có trường này
        )
        
    @staticmethod
    def from_record(record):
        """
        Tạo đối tượng SchoolNode từ Neo4j record.
        
        Args:
            record: Neo4j record chứa node School
            
        Returns:
            SchoolNode instance
        """
        node = record['s']  # 's' là alias cho school trong cypher query
        return SchoolNode(
            school_id=node['school_id'],
            school_name=node['school_name'],
            address=node.get('address'),
            type=node.get('type')
        )
    
    def __repr__(self):
        return f"<SchoolNode(school_id='{self.school_id}', school_name='{self.school_name}')>" 