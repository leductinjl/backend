"""
Certificate Node model.

This module defines the CertificateNode class for representing Certificate entities in the Neo4j graph.
"""

from app.infrastructure.ontology.ontology import RELATIONSHIPS, CLASSES

# Import specific relationships
EARNS_CERTIFICATE_REL = RELATIONSHIPS["EARNS_CERTIFICATE"]["type"]
CERTIFICATE_FOR_EXAM_REL = RELATIONSHIPS["CERTIFICATE_FOR_EXAM"]["type"]
INSTANCE_OF_REL = RELATIONSHIPS["INSTANCE_OF"]["type"]

class CertificateNode:
    """
    Model for Certificate node in Neo4j Knowledge Graph.
    
    Đại diện cho chứng chỉ trong knowledge graph.
    """
    
    def __init__(
        self, 
        certificate_id,
        certificate_name,
        certificate_number=None,
        candidate_id=None,
        exam_id=None,
        issue_date=None,
        expiry_date=None,
        issuing_organization=None,
        status=None,
        additional_info=None,
        certificate_image_url=None
    ):
        # Thuộc tính định danh - bắt buộc
        self.certificate_id = certificate_id
        self.certificate_name = certificate_name
        self.name = certificate_name  # Thêm thuộc tính 'name' cho nhất quán với các node khác
        
        # Thuộc tính quan hệ - tùy chọn
        self.candidate_id = candidate_id
        self.exam_id = exam_id
        
        # Thuộc tính bổ sung - tùy chọn
        self.certificate_number = certificate_number
        self.issue_date = issue_date
        self.expiry_date = expiry_date
        self.issuing_organization = issuing_organization
        self.status = status
        self.additional_info = additional_info
        self.certificate_image_url = certificate_image_url
        
    @staticmethod
    def create_query():
        """
        Tạo Cypher query để tạo hoặc cập nhật node Certificate.
        
        Query này tuân theo định nghĩa ontology, bao gồm thiết lập nhãn OntologyInstance
        và các thuộc tính được định nghĩa trong ontology.
        """
        return """
        MERGE (c:Certificate:OntologyInstance {certificate_id: $certificate_id})
        ON CREATE SET
            c.certificate_name = $certificate_name,
            c.name = $name,
            c.certificate_number = $certificate_number,
            c.issue_date = $issue_date,
            c.expiry_date = $expiry_date,
            c.issuing_organization = $issuing_organization,
            c.status = $status,
            c.additional_info = $additional_info,
            c.created_at = datetime()
        ON MATCH SET
            c.certificate_name = $certificate_name,
            c.name = $name,
            c.certificate_number = $certificate_number,
            c.issue_date = $issue_date,
            c.expiry_date = $expiry_date,
            c.issuing_organization = $issuing_organization,
            c.status = $status,
            c.additional_info = $additional_info,
            c.updated_at = datetime()
        RETURN c
        """
    
    def create_relationships_query(self):
        """
        Tạo Cypher query để thiết lập các mối quan hệ của Certificate.
        
        Returns:
            Query tạo quan hệ với các node khác
        """
        return f"""
        // Tạo quan hệ với Candidate nếu có
        OPTIONAL MATCH (c:Candidate {{candidate_id: $candidate_id}})
        WITH c
        WHERE c IS NOT NULL
        MATCH (cert:Certificate {{certificate_id: $certificate_id}})
        MERGE (c)-[:{EARNS_CERTIFICATE_REL}]->(cert)
        
        // Tạo quan hệ với Exam nếu có
        WITH cert
        OPTIONAL MATCH (e:Exam {{exam_id: $exam_id}})
        WITH cert, e
        WHERE e IS NOT NULL
        MERGE (cert)-[:{CERTIFICATE_FOR_EXAM_REL}]->(e)
        """
    
    @staticmethod
    def create_instance_of_relationship_query():
        """
        Tạo Cypher query để thiết lập mối quan hệ INSTANCE_OF giữa node Certificate
        và node class Certificate trong ontology.
        """
        return f"""
        MATCH (instance:Certificate:OntologyInstance {{certificate_id: $certificate_id}})
        MATCH (class:Certificate:OntologyClass {{id: 'certificate-class'}})
        MERGE (instance)-[r:{INSTANCE_OF_REL}]->(class)
        RETURN r
        """
    
    def to_dict(self):
        """
        Chuyển đổi thành dictionary để sử dụng trong Neo4j query.
        """
        return {
            "certificate_id": self.certificate_id,
            "certificate_name": self.certificate_name,
            "name": self.name,
            "certificate_number": self.certificate_number,
            "candidate_id": self.candidate_id,
            "exam_id": self.exam_id,
            "issue_date": self.issue_date,
            "expiry_date": self.expiry_date,
            "issuing_organization": self.issuing_organization,
            "status": self.status,
            "additional_info": self.additional_info,
            "certificate_image_url": self.certificate_image_url
        }
    
    @classmethod
    def from_sql_model(cls, certificate_model):
        """
        Tạo đối tượng CertificateNode từ SQLAlchemy Certificate model hoặc dictionary.
        
        Args:
            certificate_model: SQLAlchemy Certificate instance hoặc dictionary
            
        Returns:
            CertificateNode instance
        """
        # Kiểm tra nếu certificate_model là dictionary
        if isinstance(certificate_model, dict):
            cert_id = certificate_model.get('certificate_id', 'unknown')
            # Tạo certificate_name từ các thông tin khác nếu không có
            cert_name = certificate_model.get('certificate_name')
            if not cert_name:
                if 'certificate_number' in certificate_model:
                    cert_name = f"Certificate {certificate_model['certificate_number']}"
                else:
                    cert_name = f"Certificate {cert_id}"
                    
            return cls(
                certificate_id=cert_id,
                certificate_name=cert_name,
                certificate_number=certificate_model.get('certificate_number'),
                issue_date=certificate_model.get('issue_date'),
                expiry_date=certificate_model.get('expiry_date'),
                issuing_organization=certificate_model.get('issuing_organization'),
                status=certificate_model.get('status'),
                additional_info=certificate_model.get('additional_info'),
                certificate_image_url=certificate_model.get('certificate_image_url')
            )
        else:
            # Xử lý SQLAlchemy model
            cert_id = getattr(certificate_model, 'certificate_id', 'unknown')
            cert_name = getattr(certificate_model, 'certificate_name', None)
            
            if not cert_name:
                if hasattr(certificate_model, 'certificate_number') and certificate_model.certificate_number:
                    cert_name = f"Certificate {certificate_model.certificate_number}"
                else:
                    cert_name = f"Certificate {cert_id}"
            
            return cls(
                certificate_id=cert_id,
                certificate_name=cert_name,
                certificate_number=getattr(certificate_model, 'certificate_number', None),
                issue_date=getattr(certificate_model, 'issue_date', None),
                expiry_date=getattr(certificate_model, 'expiry_date', None),
                issuing_organization=getattr(certificate_model, 'issuing_organization', None),
                status=getattr(certificate_model, 'status', None),
                additional_info=getattr(certificate_model, 'additional_info', None),
                certificate_image_url=getattr(certificate_model, 'certificate_image_url', None)
            )
        
    @staticmethod
    def from_record(record):
        """
        Tạo đối tượng CertificateNode từ Neo4j record.
        
        Args:
            record: Neo4j record chứa node Certificate
            
        Returns:
            CertificateNode instance
        """
        if not record:
            return None
            
        node_data = record.get("c", record.get("certificate", None))
        if not node_data:
            return None
            
        node_properties = dict(node_data.items())
        
        return CertificateNode(
            certificate_id=node_properties.get("certificate_id"),
            certificate_name=node_properties.get("certificate_name"),
            certificate_number=node_properties.get("certificate_number"),
            issue_date=node_properties.get("issue_date"),
            expiry_date=node_properties.get("expiry_date"),
            issuing_organization=node_properties.get("issuing_organization"),
            status=node_properties.get("status"),
            additional_info=node_properties.get("additional_info"),
            certificate_image_url=node_properties.get("certificate_image_url")
        )
    
    def __repr__(self):
        return f"<CertificateNode(certificate_id='{self.certificate_id}', certificate_name='{self.certificate_name}')>" 