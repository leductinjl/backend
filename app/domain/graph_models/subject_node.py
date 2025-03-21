"""
Subject Node model.

This module defines the SubjectNode class for representing Subject entities in the Neo4j graph.
"""

class SubjectNode:
    """
    Model for Subject node in Neo4j Knowledge Graph.
    
    Đại diện cho môn học trong knowledge graph.
    """
    
    def __init__(self, subject_id, subject_name, description=None, subject_code=None):
        # Thuộc tính định danh - bắt buộc
        self.subject_id = subject_id
        self.subject_name = subject_name
        self.name = subject_name  # Thêm thuộc tính 'name' cho nhất quán với các node khác
        
        # Thuộc tính bổ sung cho truy vấn - tùy chọn
        self.description = description
        self.subject_code = subject_code
        
    @staticmethod
    def create_query():
        """
        Tạo Cypher query để tạo hoặc cập nhật node Subject.
        
        Query này tuân theo định nghĩa ontology, bao gồm thiết lập nhãn OntologyInstance
        và các thuộc tính được định nghĩa trong ontology.
        """
        return """
        MERGE (s:Subject:OntologyInstance {subject_id: $subject_id})
        ON CREATE SET
            s.subject_name = $subject_name,
            s.name = $name,
            s.description = $description,
            s.subject_code = $subject_code,
            s.created_at = datetime()
        ON MATCH SET
            s.subject_name = $subject_name,
            s.name = $name,
            s.description = $description,
            s.subject_code = $subject_code,
            s.updated_at = datetime()
        RETURN s
        """
    
    def to_dict(self):
        """
        Chuyển đổi thành dictionary để sử dụng trong Neo4j query.
        """
        return {
            "subject_id": self.subject_id,
            "subject_name": self.subject_name,
            "name": self.name,
            "description": self.description,
            "subject_code": self.subject_code
        }
    
    @classmethod
    def from_sql_model(cls, subject_model):
        """
        Tạo đối tượng SubjectNode từ SQLAlchemy Subject model.
        
        Args:
            subject_model: SQLAlchemy Subject instance
            
        Returns:
            SubjectNode instance
        """
        return cls(
            subject_id=subject_model.subject_id,
            subject_name=subject_model.subject_name,
            description=subject_model.description,
            subject_code=subject_model.subject_code
        )
        
    @staticmethod
    def from_record(record):
        """
        Tạo đối tượng SubjectNode từ Neo4j record.
        
        Args:
            record: Neo4j record chứa node Subject
            
        Returns:
            SubjectNode instance
        """
        node = record['s']  # 's' là alias cho subject trong cypher query
        return SubjectNode(
            subject_id=node['subject_id'],
            subject_name=node['subject_name'],
            description=node.get('description'),
            subject_code=node.get('subject_code')
        )
    
    def __repr__(self):
        return f"<SubjectNode(subject_id='{self.subject_id}', subject_name='{self.subject_name}')>" 