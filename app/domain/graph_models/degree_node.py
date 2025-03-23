"""
Degree Node model.

This module defines the DegreeNode class for representing Degree entities in the Neo4j graph.
"""

from app.infrastructure.ontology.ontology import RELATIONSHIPS, CLASSES

# Import specific relationships
HOLDS_DEGREE_REL = RELATIONSHIPS["HOLDS_DEGREE"]["type"]
IN_MAJOR_REL = RELATIONSHIPS["IN_MAJOR"]["type"]
ISSUED_BY_REL = RELATIONSHIPS["ISSUED_BY"]["type"]
INSTANCE_OF_REL = RELATIONSHIPS["INSTANCE_OF"]["type"]

class DegreeNode:
    """
    Model for Degree node in Neo4j Knowledge Graph.
    
    Đại diện cho bằng cấp trong knowledge graph.
    """
    
    def __init__(
        self, 
        degree_id, 
        degree_name,
        candidate_id=None,
        major_id=None,
        school_id=None,
        degree_type=None,
        issue_date=None,
        issuing_organization=None,
        graduation_date=None,
        gpa=None,
        graduation_status=None,
        additional_info=None,
        degree_image_url=None,
        start_year=None,
        end_year=None,
        academic_performance=None
    ):
        # Thuộc tính định danh - bắt buộc
        self.degree_id = degree_id
        self.degree_name = degree_name
        self.name = degree_name  # Thêm thuộc tính 'name' cho nhất quán với các node khác
        
        # Thuộc tính quan hệ - tùy chọn
        self.candidate_id = candidate_id
        self.major_id = major_id
        self.school_id = school_id
        
        # Thuộc tính bổ sung - tùy chọn
        self.degree_type = degree_type
        self.issue_date = issue_date
        self.issuing_organization = issuing_organization
        self.graduation_date = graduation_date
        self.gpa = gpa
        self.graduation_status = graduation_status
        self.additional_info = additional_info
        self.degree_image_url = degree_image_url
        self.start_year = start_year
        self.end_year = end_year
        self.academic_performance = academic_performance
        
    @staticmethod
    def create_query():
        """
        Tạo Cypher query để tạo hoặc cập nhật node Degree.
        
        Query này tuân theo định nghĩa ontology, bao gồm thiết lập nhãn OntologyInstance
        và các thuộc tính được định nghĩa trong ontology.
        """
        return """
        MERGE (d:Degree:OntologyInstance {degree_id: $degree_id})
        ON CREATE SET
            d.degree_name = $degree_name,
            d.name = $name,
            d.degree_type = $degree_type,
            d.issue_date = $issue_date,
            d.issuing_organization = $issuing_organization,
            d.graduation_date = $graduation_date,
            d.gpa = $gpa,
            d.graduation_status = $graduation_status,
            d.additional_info = $additional_info,
            d.created_at = datetime()
        ON MATCH SET
            d.degree_name = $degree_name,
            d.name = $name,
            d.degree_type = $degree_type,
            d.issue_date = $issue_date,
            d.issuing_organization = $issuing_organization,
            d.graduation_date = $graduation_date,
            d.gpa = $gpa,
            d.graduation_status = $graduation_status,
            d.additional_info = $additional_info,
            d.updated_at = datetime()
        RETURN d
        """
    
    def create_relationships_query(self):
        """
        Tạo Cypher query để thiết lập các mối quan hệ của Degree.
        
        Returns:
            Query tạo quan hệ với các node khác
        """
        return f"""
        // Tạo quan hệ với Candidate nếu có
        OPTIONAL MATCH (c:Candidate {{candidate_id: $candidate_id}})
        WITH c
        WHERE c IS NOT NULL
        MATCH (d:Degree {{degree_id: $degree_id}})
        MERGE (c)-[:{HOLDS_DEGREE_REL}]->(d)
        
        // Tạo quan hệ với Major nếu có
        WITH d
        OPTIONAL MATCH (m:Major {{major_id: $major_id}})
        WITH d, m
        WHERE m IS NOT NULL
        MERGE (d)-[:{IN_MAJOR_REL}]->(m)
        
        // Tạo quan hệ với School nếu có
        WITH d
        OPTIONAL MATCH (s:School {{school_id: $school_id}})
        WITH d, s
        WHERE s IS NOT NULL
        MERGE (d)-[:{ISSUED_BY_REL}]->(s)
        """
    
    @staticmethod
    def create_instance_of_relationship_query():
        """
        Tạo Cypher query để thiết lập mối quan hệ INSTANCE_OF giữa node Degree
        và node class Degree trong ontology.
        """
        return f"""
        MATCH (instance:Degree:OntologyInstance {{degree_id: $degree_id}})
        MATCH (class:OntologyClass {{id: 'degree-class'}})
        MERGE (instance)-[r:{INSTANCE_OF_REL}]->(class)
        RETURN r
        """
    
    def to_dict(self):
        """
        Chuyển đổi thành dictionary để sử dụng trong Neo4j query.
        """
        return {
            "degree_id": self.degree_id,
            "degree_name": self.degree_name,
            "name": self.name,
            "candidate_id": self.candidate_id,
            "major_id": self.major_id,
            "school_id": self.school_id,
            "degree_type": self.degree_type,
            "issue_date": self.issue_date,
            "issuing_organization": self.issuing_organization,
            "graduation_date": self.graduation_date,
            "gpa": self.gpa,
            "graduation_status": self.graduation_status,
            "additional_info": self.additional_info,
            "degree_image_url": self.degree_image_url,
            "start_year": self.start_year,
            "end_year": self.end_year,
            "academic_performance": self.academic_performance
        }
    
    @classmethod
    def from_sql_model(cls, sql_model, candidate_degree=None):
        """
        Tạo đối tượng DegreeNode từ SQLAlchemy Degree model.
        
        Args:
            sql_model: SQLAlchemy Degree instance
            candidate_degree: SQLAlchemy CandidateDegree instance
            
        Returns:
            DegreeNode instance
        """
        candidate_id = None
        
        if candidate_degree:
            candidate_id = candidate_degree.candidate_id
        
        # Tạo tên mặc định nếu không có
        degree_name = f"Degree {sql_model.degree_id}"
        
        # Tạo degree type mặc định nếu không có
        degree_type = "Academic"  # Giá trị mặc định
        
        return cls(
            degree_id=sql_model.degree_id,
            degree_name=degree_name,
            candidate_id=candidate_id,
            major_id=getattr(sql_model, 'major_id', None),
            school_id=getattr(sql_model, 'school_id', None),
            degree_type=degree_type,
            issue_date=None,  # Không có trong model
            issuing_organization=None,  # Không có trong model
            graduation_date=None,  # Không có trong model
            gpa=None,  # Không có trong model
            graduation_status=None,  # Không có trong model
            additional_info=getattr(sql_model, 'additional_info', None),
            degree_image_url=getattr(sql_model, 'degree_image_url', None),
            start_year=getattr(sql_model, 'start_year', None),
            end_year=getattr(sql_model, 'end_year', None),
            academic_performance=getattr(sql_model, 'academic_performance', None)
        )
        
    @staticmethod
    def from_record(record):
        """
        Tạo đối tượng DegreeNode từ Neo4j record.
        
        Args:
            record: Neo4j record chứa node Degree
            
        Returns:
            DegreeNode instance
        """
        if not record:
            return None
            
        node_data = record.get("d", record.get("degree", None))
        if not node_data:
            return None
            
        node_properties = dict(node_data.items())
        
        return DegreeNode(
            degree_id=node_properties.get("degree_id"),
            degree_name=node_properties.get("degree_name"),
            candidate_id=node_properties.get("candidate_id"),
            major_id=node_properties.get("major_id"),
            school_id=node_properties.get("school_id"),
            degree_type=node_properties.get("degree_type"),
            issue_date=node_properties.get("issue_date"),
            issuing_organization=node_properties.get("issuing_organization"),
            graduation_date=node_properties.get("graduation_date"),
            gpa=node_properties.get("gpa"),
            graduation_status=node_properties.get("graduation_status"),
            additional_info=node_properties.get("additional_info"),
            degree_image_url=node_properties.get("degree_image_url"),
            start_year=node_properties.get("start_year"),
            end_year=node_properties.get("end_year"),
            academic_performance=node_properties.get("academic_performance")
        )
    
    def __repr__(self):
        return f"<DegreeNode(degree_id='{self.degree_id}', degree_name='{self.degree_name}')>" 