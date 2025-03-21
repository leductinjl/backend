import logging

logger = logging.getLogger(__name__)

class CandidateNode:
    """
    Model cho thí sinh trong Neo4j Knowledge Graph.
    
    Node này kết hợp thông tin cơ bản từ Candidate và thông tin cần thiết từ PersonalInfo,
    được tối ưu hóa cho các truy vấn knowledge graph.
    """
    
    def __init__(self, candidate_id, full_name, birth_date=None, id_number=None, 
                 phone_number=None, email=None, address=None, id_card_image_url=None,
                 candidate_card_image_url=None, face_recognition_data_url=None,
                 additional_info=None):
        # Thuộc tính định danh - bắt buộc
        self.candidate_id = candidate_id
        self.candidate_name = full_name  # For consistency with other node types
        self.full_name = full_name
        self.name = full_name  # Thêm thuộc tính 'name' cho nhất quán với các node khác
        
        # Thuộc tính bổ sung cho truy vấn - tùy chọn
        self.birth_date = birth_date
        self.id_number = id_number
        self.phone_number = phone_number
        self.email = email
        self.address = address  # Đơn giản hóa thành 1 trường address
        self.id_card_image_url = id_card_image_url
        self.candidate_card_image_url = candidate_card_image_url
        self.face_recognition_data_url = face_recognition_data_url
        self.additional_info = additional_info
        
    @staticmethod
    def create_query():
        """
        Tạo Cypher query để tạo hoặc cập nhật node Candidate.
        
        Query này tuân theo định nghĩa ontology mới, sử dụng nhãn OntologyInstance 
        thay vì Thing và các thuộc tính được định nghĩa trong ontology.
        """
        return """
        MERGE (c:Candidate {candidate_id: $candidate_id}) 
        ON CREATE SET 
            c:OntologyInstance,
            c.candidate_name = $candidate_name,
            c.full_name = $full_name,
            c.name = $name,
            c.birth_date = $birth_date,
            c.id_number = $id_number,
            c.phone_number = $phone_number,
            c.email = $email,
            c.address = $address,
            c.id_card_image_url = $id_card_image_url,
            c.candidate_card_image_url = $candidate_card_image_url,
            c.face_recognition_data_url = $face_recognition_data_url,
            c.additional_info = $additional_info,
            c.created_at = datetime()
        ON MATCH SET 
            c.candidate_name = $candidate_name,
            c.full_name = $full_name,
            c.name = $name,
            c.birth_date = $birth_date,
            c.id_number = $id_number,
            c.phone_number = $phone_number,
            c.email = $email,
            c.address = $address,
            c.id_card_image_url = $id_card_image_url,
            c.candidate_card_image_url = $candidate_card_image_url,
            c.face_recognition_data_url = $face_recognition_data_url,
            c.additional_info = $additional_info,
            c.updated_at = datetime()
        RETURN c
        """
    
    def to_dict(self):
        """
        Chuyển đổi thành dictionary để sử dụng trong Neo4j query.
        """
        return {
            "candidate_id": self.candidate_id,
            "candidate_name": self.candidate_name,
            "full_name": self.full_name,
            "name": self.name,
            "birth_date": self.birth_date,
            "id_number": self.id_number,
            "phone_number": self.phone_number,
            "email": self.email,
            "address": self.address,
            "id_card_image_url": self.id_card_image_url,
            "candidate_card_image_url": self.candidate_card_image_url,
            "face_recognition_data_url": self.face_recognition_data_url,
            "additional_info": self.additional_info
        }
        
    @classmethod
    def from_sql_model(cls, candidate_model, personal_info_model=None):
        """
        Tạo đối tượng CandidateNode từ SQLAlchemy Candidate và PersonalInfo models.
        
        Args:
            candidate: SQLAlchemy Candidate instance
            personal_info: SQLAlchemy PersonalInfo instance (optional)
            
        Returns:
            CandidateNode instance
        """
        try:
            # Log the input data
            logger.info(f"Creating CandidateNode from models - Candidate ID: {candidate_model.candidate_id}")
            if personal_info_model:
                logger.info(f"Personal info found for candidate {candidate_model.candidate_id}")
            
            # Create node with basic candidate info
            node = cls(
                candidate_id=candidate_model.candidate_id,
                full_name=candidate_model.full_name
            )
            
            # Add personal info if available
            if personal_info_model:
                node.birth_date = personal_info_model.birth_date
                node.id_number = personal_info_model.id_number
                node.phone_number = personal_info_model.phone_number
                node.email = personal_info_model.email
                node.address = personal_info_model.primary_address
                node.id_card_image_url = personal_info_model.id_card_image_url
                node.candidate_card_image_url = personal_info_model.candidate_card_image_url
                node.face_recognition_data_url = personal_info_model.face_recognition_data_url
                node.additional_info = None
            
            logger.info(f"Successfully created CandidateNode for {candidate_model.candidate_id}")
            return node
            
        except Exception as e:
            logger.error(f"Error creating CandidateNode from models: {e}", exc_info=True)
            return None
        
    @staticmethod
    def from_record(record):
        """
        Tạo đối tượng CandidateNode từ Neo4j record.
        
        Args:
            record: Neo4j record chứa node Candidate
            
        Returns:
            CandidateNode instance
        """
        if not record:
            return None
            
        node_data = record.get("c", record.get("candidate", None))
        if not node_data:
            return None
            
        node_properties = dict(node_data.items())
        
        return CandidateNode(
            candidate_id=node_properties.get("candidate_id"),
            full_name=node_properties.get("full_name"),
            birth_date=node_properties.get("birth_date"),
            id_number=node_properties.get("id_number"),
            phone_number=node_properties.get("phone_number"),
            email=node_properties.get("email"),
            address=node_properties.get("address"),
            id_card_image_url=node_properties.get("id_card_image_url"),
            candidate_card_image_url=node_properties.get("candidate_card_image_url"),
            face_recognition_data_url=node_properties.get("face_recognition_data_url"),
            additional_info=node_properties.get("additional_info")
        ) 