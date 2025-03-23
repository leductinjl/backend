"""
Credential Node model.

This module defines the CredentialNode class for representing Candidate Credential entities in the Neo4j graph.
"""

from app.infrastructure.ontology.ontology import RELATIONSHIPS, CLASSES

# Import specific relationships
PROVIDES_CREDENTIAL_REL = RELATIONSHIPS["PROVIDES_CREDENTIAL"]["type"]
INSTANCE_OF_REL = RELATIONSHIPS["INSTANCE_OF"]["type"]

class CredentialNode:
    """
    Model for Credential node in Neo4j Knowledge Graph.
    
    Đại diện cho chứng chỉ/thông tin xác thực của thí sinh trong knowledge graph.
    """
    
    def __init__(
        self, 
        credential_id, 
        title,
        candidate_id=None,
        credential_type=None,
        issuing_organization=None,
        issue_date=None,
        expiry_date=None,
        credential_url=None,
        verification_code=None,
        description=None,
        status=None,
        additional_info=None,
        credential_image_url=None
    ):
        # Thuộc tính định danh - bắt buộc
        self.credential_id = credential_id
        self.title = title
        self.name = title  # Thêm thuộc tính 'name' cho nhất quán với các node khác
        
        # Thuộc tính quan hệ - tùy chọn
        self.candidate_id = candidate_id
        
        # Thuộc tính bổ sung - tùy chọn
        self.credential_type = credential_type
        self.issuing_organization = issuing_organization
        self.issue_date = issue_date
        self.expiry_date = expiry_date
        self.credential_url = credential_url
        self.verification_code = verification_code
        self.description = description
        self.status = status
        self.additional_info = additional_info
        self.credential_image_url = credential_image_url
        
    @staticmethod
    def create_query():
        """
        Tạo Cypher query để tạo hoặc cập nhật node Credential.
        
        Query này tuân theo định nghĩa ontology, bao gồm thiết lập nhãn OntologyInstance
        và các thuộc tính được định nghĩa trong ontology.
        """
        return """
        MERGE (c:Credential:OntologyInstance {credential_id: $credential_id})
        ON CREATE SET
            c.title = $title,
            c.name = $name,
            c.credential_type = $credential_type,
            c.issuing_organization = $issuing_organization,
            c.issue_date = $issue_date,
            c.expiry_date = $expiry_date,
            c.credential_url = $credential_url,
            c.verification_code = $verification_code,
            c.description = $description,
            c.status = $status,
            c.additional_info = $additional_info,
            c.created_at = datetime()
        ON MATCH SET
            c.title = $title,
            c.name = $name,
            c.credential_type = $credential_type,
            c.issuing_organization = $issuing_organization,
            c.issue_date = $issue_date,
            c.expiry_date = $expiry_date,
            c.credential_url = $credential_url,
            c.verification_code = $verification_code,
            c.description = $description,
            c.status = $status,
            c.additional_info = $additional_info,
            c.updated_at = datetime()
        RETURN c
        """
    
    def create_relationships_query(self):
        """
        Tạo Cypher query để thiết lập các mối quan hệ của Credential.
        
        Returns:
            Query tạo quan hệ với các node khác
        """
        return f"""
        // Tạo quan hệ với Candidate nếu có
        OPTIONAL MATCH (ca:Candidate {{candidate_id: $candidate_id}})
        WITH ca
        WHERE ca IS NOT NULL
        MATCH (c:Credential {{credential_id: $credential_id}})
        MERGE (ca)-[:{PROVIDES_CREDENTIAL_REL}]->(c)
        """
    
    def create_instance_of_relationship_query(self):
        """
        Tạo Cypher query để thiết lập mối quan hệ INSTANCE_OF giữa node Credential và class definition.
        
        Returns:
            Query tạo quan hệ INSTANCE_OF
        """
        return f"""
        MATCH (c:Credential:OntologyInstance {{credential_id: $credential_id}})
        MATCH (class:OntologyClass {{id: 'credential-class'}})
        MERGE (c)-[:{INSTANCE_OF_REL}]->(class)
        """
    
    def to_dict(self):
        """
        Chuyển đổi thành dictionary để sử dụng trong Neo4j query.
        """
        return {
            "credential_id": self.credential_id,
            "title": self.title,
            "name": self.name,
            "candidate_id": self.candidate_id,
            "credential_type": self.credential_type,
            "issuing_organization": self.issuing_organization,
            "issue_date": self.issue_date,
            "expiry_date": self.expiry_date,
            "credential_url": self.credential_url,
            "verification_code": self.verification_code,
            "description": self.description,
            "status": self.status,
            "additional_info": self.additional_info,
            "credential_image_url": self.credential_image_url
        }
    
    @classmethod
    def from_sql_model(cls, credential_model):
        """
        Tạo đối tượng CredentialNode từ SQLAlchemy CandidateCredential model.
        
        Args:
            credential_model: SQLAlchemy CandidateCredential instance
            
        Returns:
            CredentialNode instance
        """
        return cls(
            credential_id=credential_model.credential_id,
            title=credential_model.title,
            candidate_id=credential_model.candidate_id,
            credential_type=credential_model.credential_type,
            issuing_organization=credential_model.issuing_organization,
            issue_date=credential_model.issue_date,
            expiry_date=credential_model.expiry_date if hasattr(credential_model, 'expiry_date') else None,
            credential_url=credential_model.credential_url if hasattr(credential_model, 'credential_url') else None,
            verification_code=credential_model.verification_code if hasattr(credential_model, 'verification_code') else None,
            description=credential_model.description if hasattr(credential_model, 'description') else None,
            status=credential_model.status if hasattr(credential_model, 'status') else None,
            additional_info=credential_model.additional_info if hasattr(credential_model, 'additional_info') else None,
            credential_image_url=credential_model.credential_image_url if hasattr(credential_model, 'credential_image_url') else None
        )
        
    @staticmethod
    def from_record(record):
        """
        Tạo đối tượng CredentialNode từ Neo4j record.
        
        Args:
            record: Neo4j record chứa node Credential
            
        Returns:
            CredentialNode instance
        """
        if not record:
            return None
            
        node_data = record.get("cr", record.get("credential", None))
        if not node_data:
            return None
            
        node_properties = dict(node_data.items())
        
        return CredentialNode(
            credential_id=node_properties.get("credential_id"),
            title=node_properties.get("credential_name"),
            credential_type=node_properties.get("credential_type"),
            issue_date=node_properties.get("issue_date"),
            expiry_date=node_properties.get("expiry_date"),
            description=node_properties.get("description"),
            candidate_id=node_properties.get("candidate_id"),
            credential_url=node_properties.get("credential_url"),
            verification_code=node_properties.get("verification_code"),
            status=node_properties.get("status"),
            additional_info=node_properties.get("additional_info"),
            credential_image_url=node_properties.get("credential_image_url")
        )
    
    def __repr__(self):
        return f"<CredentialNode(credential_id='{self.credential_id}', title='{self.title}')>" 