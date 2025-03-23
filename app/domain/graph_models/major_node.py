"""
Major Node model.

This module defines the MajorNode class for representing Major entities in the Neo4j graph.
"""

from app.infrastructure.ontology.ontology import RELATIONSHIPS, CLASSES

# Define relationship constants
INSTANCE_OF_REL = RELATIONSHIPS["INSTANCE_OF"]["type"]
OFFERS_MAJOR_REL = RELATIONSHIPS["OFFERS_MAJOR"]["type"]
STUDIES_MAJOR_REL = RELATIONSHIPS["STUDIES_MAJOR"]["type"]

class MajorNode:
    """
    Model for Major node in Neo4j Knowledge Graph.
    
    Đại diện cho ngành học trong knowledge graph.
    """
    
    def __init__(self, major_id, major_name, major_code=None, description=None):
        # Thuộc tính định danh - bắt buộc
        self.major_id = major_id
        self.major_name = major_name
        self.name = major_name  # Thêm thuộc tính 'name' cho nhất quán với các node khác
        
        # Thuộc tính bổ sung cho truy vấn - tùy chọn
        self.major_code = major_code
        self.description = description
        
    @staticmethod
    def create_query():
        """
        Tạo Cypher query để tạo hoặc cập nhật node Major.
        
        Query này tuân theo định nghĩa ontology, bao gồm thiết lập nhãn OntologyInstance
        và các thuộc tính được định nghĩa trong ontology.
        """
        return """
        MERGE (m:Major:OntologyInstance {major_id: $major_id})
        ON CREATE SET
            m.major_name = $major_name,
            m.name = $name,
            m.major_code = $major_code,
            m.description = $description,
            m.created_at = datetime()
        ON MATCH SET
            m.major_name = $major_name,
            m.name = $name,
            m.major_code = $major_code,
            m.description = $description,
            m.updated_at = datetime()
        RETURN m
        """
    
    def create_instance_of_relationship_query(self):
        """
        Tạo Cypher query để thiết lập mối quan hệ INSTANCE_OF giữa node Major và class definition.
        
        Returns:
            Query tạo quan hệ INSTANCE_OF
        """
        return f"""
        MATCH (m:Major:OntologyInstance {{major_id: $major_id}})
        MATCH (class:OntologyClass {{id: 'major-class'}})
        MERGE (m)-[:{INSTANCE_OF_REL}]->(class)
        """
    
    def create_relationships_query(self):
        """
        Tạo Cypher query để thiết lập các mối quan hệ giữa Major và các node khác.
        Phương thức này là placeholder và sẽ được gọi từ repository nếu cần.
        
        Returns:
            Empty string vì các mối quan hệ sẽ được tạo từ repository
        """
        return ""
    
    def to_dict(self):
        """
        Chuyển đổi thành dictionary để sử dụng trong Neo4j query.
        """
        return {
            "major_id": self.major_id,
            "major_name": self.major_name,
            "name": self.name,
            "major_code": self.major_code,
            "description": self.description
        }
    
    @classmethod
    def from_sql_model(cls, major_model):
        """
        Tạo đối tượng MajorNode từ SQLAlchemy Major model.
        
        Args:
            major_model: SQLAlchemy Major instance
            
        Returns:
            MajorNode instance
        """
        return cls(
            major_id=getattr(major_model, 'major_id', None),
            major_name=getattr(major_model, 'major_name', None),
            major_code=getattr(major_model, 'ministry_code', None),
            description=getattr(major_model, 'description', None)
        )
        
    @staticmethod
    def from_record(record):
        """
        Tạo đối tượng MajorNode từ Neo4j record.
        
        Args:
            record: Neo4j record chứa node Major
            
        Returns:
            MajorNode instance
        """
        node = record['m']  # 'm' là alias cho major trong cypher query
        return MajorNode(
            major_id=node['major_id'],
            major_name=node['major_name'],
            major_code=node.get('major_code'),
            description=node.get('description')
        )
    
    def __repr__(self):
        return f"<MajorNode(major_id='{self.major_id}', major_name='{self.major_name}')>" 