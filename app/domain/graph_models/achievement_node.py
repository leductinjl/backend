"""
Achievement Node model.

This module defines the AchievementNode class for representing Achievement entities in the Neo4j graph.
"""

from app.infrastructure.ontology.ontology import RELATIONSHIPS, CLASSES

# Import specific relationships
ACHIEVES_REL = RELATIONSHIPS["ACHIEVES"]["type"]
ACHIEVEMENT_FOR_EXAM_REL = RELATIONSHIPS["ACHIEVEMENT_FOR_EXAM"]["type"]
INSTANCE_OF_REL = RELATIONSHIPS["INSTANCE_OF"]["type"]

class AchievementNode:
    """
    Model for Achievement node in Neo4j Knowledge Graph.
    
    Đại diện cho thành tích trong knowledge graph.
    """
    
    def __init__(
        self, 
        achievement_id, 
        achievement_name,
        candidate_id=None,
        exam_id=None,
        achievement_type=None,
        achievement_date=None,
        issuing_organization=None,
        description=None,
        additional_info=None,
        achievement_image_url=None
    ):
        # Thuộc tính định danh - bắt buộc
        self.achievement_id = achievement_id
        self.achievement_name = achievement_name
        self.name = achievement_name  # Thêm thuộc tính 'name' cho nhất quán với các node khác
        
        # Thuộc tính quan hệ - tùy chọn
        self.candidate_id = candidate_id
        self.exam_id = exam_id
        
        # Thuộc tính bổ sung - tùy chọn
        self.achievement_type = achievement_type
        self.achievement_date = achievement_date
        self.issuing_organization = issuing_organization
        self.description = description
        self.additional_info = additional_info
        self.achievement_image_url = achievement_image_url
        
    @staticmethod
    def create_query():
        """
        Tạo Cypher query để tạo hoặc cập nhật node Achievement.
        
        Query này tuân theo định nghĩa ontology, bao gồm thiết lập nhãn OntologyInstance
        và các thuộc tính được định nghĩa trong ontology.
        """
        return """
        MERGE (a:Achievement:OntologyInstance {achievement_id: $achievement_id})
        ON CREATE SET
            a.achievement_name = $achievement_name,
            a.name = $name,
            a.achievement_type = $achievement_type,
            a.achievement_date = $achievement_date,
            a.issuing_organization = $issuing_organization,
            a.description = $description,
            a.additional_info = $additional_info,
            a.created_at = datetime()
        ON MATCH SET
            a.achievement_name = $achievement_name,
            a.name = $name,
            a.achievement_type = $achievement_type,
            a.achievement_date = $achievement_date,
            a.issuing_organization = $issuing_organization,
            a.description = $description,
            a.additional_info = $additional_info,
            a.updated_at = datetime()
        RETURN a
        """
    
    def create_relationships_query(self):
        """
        Tạo Cypher query để thiết lập các mối quan hệ của Achievement.
        
        Returns:
            Query tạo quan hệ với các node khác
        """
        return f"""
        // Tạo quan hệ với Candidate nếu có
        OPTIONAL MATCH (c:Candidate {{candidate_id: $candidate_id}})
        WITH c
        WHERE c IS NOT NULL
        MATCH (a:Achievement {{achievement_id: $achievement_id}})
        MERGE (c)-[:{ACHIEVES_REL}]->(a)
        
        // Tạo quan hệ với Exam nếu có
        WITH a
        OPTIONAL MATCH (e:Exam {{exam_id: $exam_id}})
        WITH a, e
        WHERE e IS NOT NULL
        MERGE (a)-[:{ACHIEVEMENT_FOR_EXAM_REL}]->(e)
        """
    
    @staticmethod
    def create_instance_of_relationship_query():
        """
        Tạo Cypher query để thiết lập mối quan hệ INSTANCE_OF giữa node Achievement
        và node class Achievement trong ontology.
        """
        return f"""
        MATCH (instance:Achievement:OntologyInstance {{achievement_id: $achievement_id}})
        MATCH (class:Achievement:OntologyClass {{id: 'achievement-class'}})
        MERGE (instance)-[r:{INSTANCE_OF_REL}]->(class)
        RETURN r
        """
    
    def to_dict(self):
        """
        Chuyển đổi thành dictionary để sử dụng trong Neo4j query.
        """
        return {
            "achievement_id": self.achievement_id,
            "achievement_name": self.achievement_name,
            "name": self.name,
            "candidate_id": self.candidate_id,
            "exam_id": self.exam_id,
            "achievement_type": self.achievement_type,
            "achievement_date": self.achievement_date,
            "issuing_organization": self.issuing_organization,
            "description": self.description,
            "additional_info": self.additional_info,
            "achievement_image_url": self.achievement_image_url
        }
    
    @classmethod
    def from_sql_model(cls, achievement_model):
        """
        Tạo đối tượng AchievementNode từ SQLAlchemy Achievement model hoặc dictionary.
        
        Args:
            achievement_model: SQLAlchemy Achievement instance hoặc dictionary
            
        Returns:
            AchievementNode instance
        """
        # Kiểm tra và trích xuất candidate_id và exam_id
        candidate_id = None
        exam_id = None
        
        if isinstance(achievement_model, dict):
            achievement_id = achievement_model.get('achievement_id', 'unknown')
            achievement_name = achievement_model.get('achievement_name')
            
            # Trích xuất candidate_id và exam_id từ candidate_exam nếu có
            if 'candidate_id' in achievement_model:
                candidate_id = achievement_model['candidate_id']
            elif 'candidate_exam' in achievement_model and achievement_model['candidate_exam']:
                candidate_exam = achievement_model['candidate_exam']
                if isinstance(candidate_exam, dict):
                    candidate_id = candidate_exam.get('candidate_id')
                    exam_id = candidate_exam.get('exam_id')
                else:
                    if hasattr(candidate_exam, 'candidate_id'):
                        candidate_id = candidate_exam.candidate_id
                    if hasattr(candidate_exam, 'exam_id'):
                        exam_id = candidate_exam.exam_id
            
            return cls(
                achievement_id=achievement_id,
                achievement_name=achievement_name,
                candidate_id=candidate_id,
                exam_id=exam_id,
                achievement_type=achievement_model.get('achievement_type'),
                achievement_date=achievement_model.get('achievement_date'),
                issuing_organization=achievement_model.get('organization'),
                description=achievement_model.get('description'),
                additional_info=achievement_model.get('additional_info'),
                achievement_image_url=achievement_model.get('proof_url')
            )
        else:
            # Xử lý model SQLAlchemy
            achievement_id = getattr(achievement_model, 'achievement_id', 'unknown')
            achievement_name = getattr(achievement_model, 'achievement_name', f"Achievement {achievement_id}")
            
            # Trích xuất candidate_id và exam_id từ candidate_exam
            if hasattr(achievement_model, 'candidate_exam') and achievement_model.candidate_exam:
                candidate_exam = achievement_model.candidate_exam
                if hasattr(candidate_exam, 'candidate_id'):
                    candidate_id = candidate_exam.candidate_id
                if hasattr(candidate_exam, 'exam_id'):
                    exam_id = candidate_exam.exam_id
            
            return cls(
                achievement_id=achievement_id,
                achievement_name=achievement_name,
                candidate_id=candidate_id,
                exam_id=exam_id,
                achievement_type=getattr(achievement_model, 'achievement_type', None),
                achievement_date=getattr(achievement_model, 'achievement_date', None),
                issuing_organization=getattr(achievement_model, 'organization', None),
                description=getattr(achievement_model, 'description', None),
                additional_info=getattr(achievement_model, 'additional_info', None),
                achievement_image_url=getattr(achievement_model, 'proof_url', None)
            )
        
    @staticmethod
    def from_record(record):
        """
        Tạo đối tượng AchievementNode từ Neo4j record.
        
        Args:
            record: Neo4j record chứa node Achievement
            
        Returns:
            AchievementNode instance
        """
        if not record:
            return None
            
        node_data = record.get("a", record.get("achievement", None))
        if not node_data:
            return None
            
        node_properties = dict(node_data.items())
        
        return AchievementNode(
            achievement_id=node_properties.get("achievement_id"),
            achievement_name=node_properties.get("achievement_name"),
            achievement_type=node_properties.get("achievement_type"),
            achievement_date=node_properties.get("achievement_date"),
            description=node_properties.get("description"),
            candidate_id=node_properties.get("candidate_id"),
            achievement_image_url=node_properties.get("achievement_image_url"),
            additional_info=node_properties.get("additional_info")
        )
    
    def __repr__(self):
        return f"<AchievementNode(achievement_id='{self.achievement_id}', achievement_name='{self.achievement_name}')>" 