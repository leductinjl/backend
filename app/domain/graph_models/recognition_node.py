"""
Recognition Node model.

This module defines the RecognitionNode class for representing Recognition entities in the Neo4j graph.
"""

from app.infrastructure.ontology.ontology import RELATIONSHIPS

# Import specific relationships
INSTANCE_OF_REL = RELATIONSHIPS["INSTANCE_OF"]["type"]
RECEIVES_RECOGNITION_REL = RELATIONSHIPS["RECEIVES_RECOGNITION"]["type"]
RECOGNITION_FOR_EXAM_REL = RELATIONSHIPS["RECOGNITION_FOR_EXAM"]["type"]

class RecognitionNode:
    """
    Model for Recognition node in Neo4j Knowledge Graph.
    
    Đại diện cho sự công nhận/ghi nhận trong knowledge graph.
    """
    
    def __init__(
        self, 
        recognition_id, 
        recognition_name,
        recognition_type=None,
        recognition_date=None,
        description=None,
        candidate_id=None,
        exam_id=None,
        recognition_image_url=None,
        additional_info=None
    ):
        # Thuộc tính định danh - bắt buộc
        self.recognition_id = recognition_id
        self.recognition_name = recognition_name
        self.name = recognition_name  # Thêm thuộc tính 'name' cho nhất quán với các node khác
        
        # Thuộc tính quan hệ - tùy chọn
        self.candidate_id = candidate_id
        self.exam_id = exam_id
        
        # Thuộc tính bổ sung - tùy chọn
        self.recognition_type = recognition_type
        self.recognition_date = recognition_date
        self.description = description
        self.recognition_image_url = recognition_image_url
        self.additional_info = additional_info
        
    @staticmethod
    def create_query():
        """
        Tạo Cypher query để tạo hoặc cập nhật node Recognition.
        
        Query này tuân theo định nghĩa ontology, bao gồm thiết lập nhãn OntologyInstance
        và các thuộc tính được định nghĩa trong ontology.
        """
        return """
        MERGE (r:Recognition:OntologyInstance {recognition_id: $recognition_id})
        ON CREATE SET
            r.recognition_name = $recognition_name,
            r.name = $name,
            r.recognition_type = $recognition_type,
            r.recognition_date = $recognition_date,
            r.recognition_image_url = $recognition_image_url,
            r.description = $description,
            r.additional_info = $additional_info,
            r.created_at = datetime()
        ON MATCH SET
            r.recognition_name = $recognition_name,
            r.name = $name,
            r.recognition_type = $recognition_type,
            r.recognition_date = $recognition_date,
            r.recognition_image_url = $recognition_image_url,
            r.description = $description,
            r.additional_info = $additional_info,
            r.updated_at = datetime()
        RETURN r
        """
    
    def create_instance_of_relationship_query(self):
        """
        Tạo Cypher query để thiết lập mối quan hệ INSTANCE_OF giữa node Recognition và class definition.
        
        Returns:
            Query tạo quan hệ INSTANCE_OF
        """
        return f"""
        MATCH (r:Recognition:OntologyInstance {{recognition_id: $recognition_id}})
        MATCH (class:OntologyClass {{id: 'recognition-class'}})
        MERGE (r)-[:{INSTANCE_OF_REL}]->(class)
        """
    
    def create_relationships_query(self):
        """
        Tạo Cypher query để thiết lập các mối quan hệ của Recognition.
        
        Returns:
            Query tạo quan hệ với các node khác
        """
        return f"""
        // Tạo quan hệ với Candidate nếu có
        OPTIONAL MATCH (c:Candidate {{candidate_id: $candidate_id}})
        WITH c
        WHERE c IS NOT NULL
        MATCH (r:Recognition {{recognition_id: $recognition_id}})
        MERGE (c)-[:{RECEIVES_RECOGNITION_REL}]->(r)
        
        // Tạo quan hệ với Exam nếu có
        WITH r
        OPTIONAL MATCH (e:Exam {{exam_id: $exam_id}})
        WITH r, e
        WHERE e IS NOT NULL
        MERGE (r)-[:{RECOGNITION_FOR_EXAM_REL}]->(e)
        """
    
    def to_dict(self):
        """
        Chuyển đổi thành dictionary để sử dụng trong Neo4j query.
        """
        return {
            "recognition_id": self.recognition_id,
            "recognition_name": self.recognition_name,
            "name": self.name,
            "candidate_id": self.candidate_id,
            "exam_id": self.exam_id,
            "recognition_type": self.recognition_type,
            "recognition_date": self.recognition_date,
            "description": self.description,
            "recognition_image_url": self.recognition_image_url,
            "additional_info": self.additional_info
        }
    
    @classmethod
    def from_sql_model(cls, recognition_model):
        """
        Tạo đối tượng RecognitionNode từ SQLAlchemy Recognition model hoặc dictionary.
        
        Args:
            recognition_model: SQLAlchemy Recognition instance hoặc dictionary
            
        Returns:
            RecognitionNode instance
        """
        # Kiểm tra và trích xuất candidate_id và exam_id
        candidate_id = None
        exam_id = None
        
        if isinstance(recognition_model, dict):
            recognition_id = recognition_model.get('recognition_id', 'unknown')
            
            # Lấy title cho recognition_name
            recognition_name = recognition_model.get('recognition_name')
            if not recognition_name:
                recognition_name = recognition_model.get('title', f"Recognition {recognition_id}")
            
            # Trích xuất candidate_id và exam_id từ candidate_exam nếu có
            if 'candidate_id' in recognition_model:
                candidate_id = recognition_model['candidate_id']
            elif 'candidate_exam' in recognition_model and recognition_model['candidate_exam']:
                candidate_exam = recognition_model['candidate_exam']
                if isinstance(candidate_exam, dict):
                    candidate_id = candidate_exam.get('candidate_id')
                    exam_id = candidate_exam.get('exam_id')
                else:
                    if hasattr(candidate_exam, 'candidate_id'):
                        candidate_id = candidate_exam.candidate_id
                    if hasattr(candidate_exam, 'exam_id'):
                        exam_id = candidate_exam.exam_id
            
            return cls(
                recognition_id=recognition_id,
                recognition_name=recognition_name,
                candidate_id=candidate_id,
                exam_id=exam_id,
                recognition_type=recognition_model.get('recognition_type'),
                recognition_date=recognition_model.get('issue_date'),
                description=recognition_model.get('description'),
                recognition_image_url=recognition_model.get('recognition_image_url'),
                additional_info=recognition_model.get('additional_info')
            )
        else:
            # Xử lý model SQLAlchemy
            recognition_id = getattr(recognition_model, 'recognition_id', 'unknown')
            
            # Lấy title cho recognition_name
            recognition_name = getattr(recognition_model, 'recognition_name', None)
            if not recognition_name:
                recognition_name = getattr(recognition_model, 'title', f"Recognition {recognition_id}")
            
            # Trích xuất candidate_id và exam_id từ candidate_exam
            if hasattr(recognition_model, 'candidate_exam') and recognition_model.candidate_exam:
                candidate_exam = recognition_model.candidate_exam
                if hasattr(candidate_exam, 'candidate_id'):
                    candidate_id = candidate_exam.candidate_id
                if hasattr(candidate_exam, 'exam_id'):
                    exam_id = candidate_exam.exam_id
            
            return cls(
                recognition_id=recognition_id,
                recognition_name=recognition_name,
                candidate_id=candidate_id,
                exam_id=exam_id,
                recognition_type=getattr(recognition_model, 'recognition_type', None),
                recognition_date=getattr(recognition_model, 'issue_date', None),
                description=getattr(recognition_model, 'description', None),
                recognition_image_url=getattr(recognition_model, 'recognition_image_url', None),
                additional_info=getattr(recognition_model, 'additional_info', None)
            )
        
    @staticmethod
    def from_record(record):
        """
        Tạo đối tượng RecognitionNode từ Neo4j record.
        
        Args:
            record: Neo4j record chứa node Recognition
            
        Returns:
            RecognitionNode instance
        """
        if not record:
            return None
            
        node_data = record.get("r", record.get("recognition", None))
        if not node_data:
            return None
            
        node_properties = dict(node_data.items())
        
        return RecognitionNode(
            recognition_id=node_properties.get("recognition_id"),
            recognition_name=node_properties.get("recognition_name"),
            recognition_type=node_properties.get("recognition_type"),
            recognition_date=node_properties.get("recognition_date"),
            description=node_properties.get("description"),
            candidate_id=node_properties.get("candidate_id"),
            exam_id=node_properties.get("exam_id"),
            recognition_image_url=node_properties.get("recognition_image_url"),
            additional_info=node_properties.get("additional_info")
        )
    
    def __repr__(self):
        return f"<RecognitionNode(recognition_id='{self.recognition_id}', recognition_name='{self.recognition_name}')>" 