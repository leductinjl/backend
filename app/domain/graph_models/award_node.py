"""
Award Node model.

This module defines the AwardNode class for representing Award entities in the Neo4j graph.
"""

from app.infrastructure.ontology.ontology import RELATIONSHIPS, CLASSES

# Import specific relationships
EARNS_AWARD_REL = RELATIONSHIPS["EARNS_AWARD"]["type"]
AWARD_FOR_EXAM_REL = RELATIONSHIPS["AWARD_FOR_EXAM"]["type"]
INSTANCE_OF_REL = RELATIONSHIPS["INSTANCE_OF"]["type"]

class AwardNode:
    """
    Model for Award node in Neo4j Knowledge Graph.
    
    Đại diện cho giải thưởng trong knowledge graph.
    """
    
    def __init__(
        self, 
        award_id, 
        award_name,
        award_type=None,
        award_date=None,
        description=None,
        candidate_id=None,
        award_image_url=None,
        additional_info=None
    ):
        # Thuộc tính định danh - bắt buộc
        self.award_id = award_id
        self.award_name = award_name
        self.name = award_name  # Thêm thuộc tính 'name' cho nhất quán với các node khác
        
        # Thuộc tính quan hệ - tùy chọn
        self.candidate_id = candidate_id
        
        # Thuộc tính bổ sung - tùy chọn
        self.award_type = award_type
        self.award_date = award_date
        self.description = description
        self.award_image_url = award_image_url
        self.additional_info = additional_info
        
    @staticmethod
    def create_query():
        """
        Tạo Cypher query để tạo hoặc cập nhật node Award.
        
        Query này tuân theo định nghĩa ontology, bao gồm thiết lập nhãn OntologyInstance
        và các thuộc tính được định nghĩa trong ontology.
        """
        return """
        MERGE (a:Award:OntologyInstance {award_id: $award_id})
        ON CREATE SET
            a.award_name = $award_name,
            a.name = $name,
            a.award_type = $award_type,
            a.award_date = $award_date,
            a.description = $description,
            a.award_image_url = $award_image_url,
            a.additional_info = $additional_info,
            a.created_at = datetime()
        ON MATCH SET
            a.award_name = $award_name,
            a.name = $name,
            a.award_type = $award_type,
            a.award_date = $award_date,
            a.description = $description,
            a.award_image_url = $award_image_url,
            a.additional_info = $additional_info,
            a.updated_at = datetime()
        RETURN a
        """
    
    def create_relationships_query(self):
        """
        Tạo Cypher query để thiết lập các mối quan hệ của Award.
        
        Returns:
            Query tạo quan hệ với các node khác
        """
        return f"""
        // Tạo quan hệ với Candidate nếu có
        OPTIONAL MATCH (c:Candidate {{candidate_id: $candidate_id}})
        WITH c
        WHERE c IS NOT NULL
        MATCH (a:Award {{award_id: $award_id}})
        MERGE (c)-[:{EARNS_AWARD_REL}]->(a)
        
        // Tạo quan hệ với Exam nếu có
        WITH a
        OPTIONAL MATCH (e:Exam {{exam_id: $exam_id}})
        WITH a, e
        WHERE e IS NOT NULL
        MERGE (a)-[:{AWARD_FOR_EXAM_REL}]->(e)
        """
    
    @staticmethod
    def create_instance_of_relationship_query():
        """
        Tạo Cypher query để thiết lập mối quan hệ INSTANCE_OF giữa node Award
        và node class Award trong ontology.
        """
        return f"""
        MATCH (instance:Award:OntologyInstance {{award_id: $award_id}})
        MATCH (class:Award:OntologyClass {{id: 'award-class'}})
        MERGE (instance)-[r:{INSTANCE_OF_REL}]->(class)
        RETURN r
        """
    
    def to_dict(self):
        """
        Chuyển đổi thành dictionary để sử dụng trong Neo4j query.
        """
        return {
            "award_id": self.award_id,
            "award_name": self.award_name,
            "name": self.name,
            "candidate_id": self.candidate_id,
            "exam_id": getattr(self, 'exam_id', None),
            "award_type": self.award_type,
            "award_date": self.award_date,
            "description": self.description,
            "award_image_url": self.award_image_url,
            "additional_info": self.additional_info
        }
    
    @classmethod
    def from_sql_model(cls, sql_model):
        """
        Tạo đối tượng AwardNode từ SQLAlchemy Award model.
        
        Args:
            sql_model: SQLAlchemy Award instance
            
        Returns:
            AwardNode instance
        """
        # Tạo award_name từ achievement hoặc award_type nếu không có award_name
        award_name = getattr(sql_model, 'award_name', None)
        if not award_name:
            if hasattr(sql_model, 'achievement') and sql_model.achievement:
                award_name = sql_model.achievement
            elif hasattr(sql_model, 'award_type') and sql_model.award_type:
                award_name = sql_model.award_type
            else:
                award_name = f"Award {sql_model.award_id}"
        
        # Lấy thông tin candidate_id và exam_id nếu có
        candidate_id = None
        exam_id = None
        
        if hasattr(sql_model, 'candidate_id'):
            candidate_id = sql_model.candidate_id
        
        if hasattr(sql_model, 'exam_id'):
            exam_id = sql_model.exam_id
        
        # Trích xuất từ candidate_exam nếu có
        if hasattr(sql_model, 'candidate_exam') and sql_model.candidate_exam:
            if hasattr(sql_model.candidate_exam, 'candidate_id'):
                candidate_id = sql_model.candidate_exam.candidate_id
            if hasattr(sql_model.candidate_exam, 'exam_id'):
                exam_id = sql_model.candidate_exam.exam_id
        
        award = cls(
            award_id=sql_model.award_id,
            award_name=award_name,
            award_type=getattr(sql_model, 'award_type', None),
            award_date=getattr(sql_model, 'award_date', None),
            description=getattr(sql_model, 'achievement', None),
            candidate_id=candidate_id,
            award_image_url=getattr(sql_model, 'certificate_image_url', None),
            additional_info=getattr(sql_model, 'additional_info', None)
        )
        
        # Lưu exam_id như một thuộc tính bổ sung
        award.exam_id = exam_id
        
        return award
        
    @staticmethod
    def from_record(record):
        """
        Tạo đối tượng AwardNode từ Neo4j record.
        
        Args:
            record: Neo4j record chứa node Award
            
        Returns:
            AwardNode instance
        """
        if not record:
            return None
            
        node_data = record.get("aw", record.get("award", None))
        if not node_data:
            return None
            
        node_properties = dict(node_data.items())
        
        return AwardNode(
            award_id=node_properties.get("award_id"),
            award_name=node_properties.get("award_name"),
            award_type=node_properties.get("award_type"),
            award_date=node_properties.get("award_date"),
            description=node_properties.get("description"),
            candidate_id=node_properties.get("candidate_id"),
            award_image_url=node_properties.get("award_image_url"),
            additional_info=node_properties.get("additional_info")
        )
    
    def __repr__(self):
        return f"<AwardNode(award_id='{self.award_id}', award_name='{self.award_name}')>" 