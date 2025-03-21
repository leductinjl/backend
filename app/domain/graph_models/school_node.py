"""
School Node model.

This module defines the SchoolNode class for representing School entities in the Neo4j graph.
"""

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