"""
Management Unit Node model.

This module defines the ManagementUnitNode class for representing ManagementUnit entities in the Neo4j graph.
"""

from typing import Optional, Dict, Any

class ManagementUnitNode:
    """
    Model for ManagementUnit node in Neo4j Knowledge Graph.
    
    Đại diện cho đơn vị quản lý (bộ, sở, trường) trong knowledge graph.
    """
    
    def __init__(
        self, 
        unit_id, 
        unit_name,
        unit_code=None,
        unit_type=None,
        address=None,
        contact_info=None,
        parent_id=None,
        level=None,
        region=None,
        status=None,
        additional_info=None
    ):
        # Thuộc tính định danh - bắt buộc
        self.unit_id = unit_id
        self.unit_name = unit_name
        self.name = unit_name  # Thêm thuộc tính 'name' cho nhất quán với các node khác
        
        # Thuộc tính bổ sung - tùy chọn
        self.unit_code = unit_code
        self.unit_type = unit_type
        self.address = address
        self.contact_info = contact_info
        self.parent_id = parent_id
        self.level = level
        self.region = region
        self.status = status
        self.additional_info = additional_info
        
    @staticmethod
    def create_query():
        """
        Tạo Cypher query để tạo hoặc cập nhật node ManagementUnit.
        
        Query này tuân theo định nghĩa ontology, bao gồm thiết lập nhãn OntologyInstance
        và các thuộc tính được định nghĩa trong ontology.
        """
        return """
        MERGE (m:ManagementUnit:OntologyInstance {unit_id: $unit_id})
        ON CREATE SET
            m.unit_name = $unit_name,
            m.name = $name,
            m.unit_code = $unit_code,
            m.unit_type = $unit_type,
            m.address = $address,
            m.contact_info = $contact_info,
            m.parent_id = $parent_id,
            m.level = $level,
            m.region = $region,
            m.status = $status,
            m.additional_info = $additional_info,
            m.created_at = datetime()
        ON MATCH SET
            m.unit_name = $unit_name,
            m.name = $name,
            m.unit_code = $unit_code,
            m.unit_type = $unit_type,
            m.address = $address,
            m.contact_info = $contact_info,
            m.parent_id = $parent_id,
            m.level = $level,
            m.region = $region,
            m.status = $status,
            m.additional_info = $additional_info,
            m.updated_at = datetime()
        RETURN m
        """
    
    def create_relationships_query(self):
        """
        Tạo Cypher query để thiết lập các mối quan hệ của ManagementUnit.
        
        Returns:
            Query tạo quan hệ với các node khác
        """
        return """
        // Tạo quan hệ với đơn vị cha nếu có
        OPTIONAL MATCH (p:ManagementUnit {unit_id: $parent_id})
        WITH p
        WHERE p IS NOT NULL
        MATCH (m:ManagementUnit {unit_id: $unit_id})
        MERGE (m)-[:BELONGS_TO]->(p)
        """
    
    def to_dict(self):
        """
        Chuyển đổi thành dictionary để sử dụng trong Neo4j query.
        """
        return {
            "unit_id": self.unit_id,
            "unit_name": self.unit_name,
            "name": self.name,
            "unit_code": self.unit_code,
            "unit_type": self.unit_type,
            "address": self.address,
            "contact_info": self.contact_info,
            "parent_id": self.parent_id,
            "level": self.level,
            "region": self.region,
            "status": self.status,
            "additional_info": self.additional_info
        }
    
    @classmethod
    def from_sql_model(cls, unit_model):
        """
        Tạo đối tượng ManagementUnitNode từ SQLAlchemy ManagementUnit model.
        
        Args:
            unit_model: SQLAlchemy ManagementUnit instance
            
        Returns:
            ManagementUnitNode instance
        """
        return cls(
            unit_id=unit_model.unit_id,
            unit_name=unit_model.unit_name,
            unit_code=getattr(unit_model, 'unit_code', None),
            unit_type=getattr(unit_model, 'unit_type', None),
            address=getattr(unit_model, 'address', None),
            contact_info=getattr(unit_model, 'contact_info', None),
            parent_id=getattr(unit_model, 'parent_id', None),
            level=getattr(unit_model, 'level', None),
            region=getattr(unit_model, 'region', None),
            status=getattr(unit_model, 'status', None),
            additional_info=getattr(unit_model, 'additional_info', None)
        )
        
    @staticmethod
    def from_record(record: Dict[str, Any]) -> 'ManagementUnitNode':
        """
        Tạo đối tượng ManagementUnitNode từ Neo4j record.
        
        Args:
            record: Neo4j record chứa node ManagementUnit
            
        Returns:
            ManagementUnitNode instance
        """
        node = record['m']  # 'm' là alias cho management_unit trong cypher query
        
        return ManagementUnitNode(
            unit_id=node['unit_id'],
            unit_name=node['unit_name'],
            unit_code=node.get('unit_code'),
            unit_type=node.get('unit_type'),
            address=node.get('address'),
            contact_info=node.get('contact_info'),
            parent_id=node.get('parent_id'),
            level=node.get('level'),
            region=node.get('region'),
            status=node.get('status'),
            additional_info=node.get('additional_info')
        )
    
    def __repr__(self):
        return f"<ManagementUnitNode(unit_id='{self.unit_id}', unit_name='{self.unit_name}')>" 