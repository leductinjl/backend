"""
Management Unit Graph Repository.

This module defines the ManagementUnitGraphRepository class for managing ManagementUnit nodes in Neo4j.
"""

import logging
from typing import Dict, List, Optional, Union

from neo4j import Driver
from neo4j.exceptions import Neo4jError

from app.domain.graph_models.management_unit_node import (
    ManagementUnitNode, INSTANCE_OF_REL, ORGANIZED_BY_REL
)
from app.infrastructure.ontology.ontology import RELATIONSHIPS

# Define other relationship constants
MANAGES_REL = "MANAGES"
OPERATES_REL = "OPERATES"

logger = logging.getLogger(__name__)

class ManagementUnitGraphRepository:
    """
    Repository for ManagementUnit nodes in Neo4j Knowledge Graph.
    
    Cung cấp các phương thức để tương tác với các node ManagementUnit trong Neo4j.
    """
    
    def __init__(self, driver):
        """
        Khởi tạo repository với neo4j driver.
        
        Args:
            driver: Neo4j connection instance
        """
        self.neo4j = driver
        
    async def create_or_update(self, unit: Union[Dict, ManagementUnitNode]) -> Optional[ManagementUnitNode]:
        """
        Tạo mới hoặc cập nhật node ManagementUnit.
        
        Args:
            unit: ManagementUnitNode hoặc dictionary chứa thông tin đơn vị quản lý
            
        Returns:
            ManagementUnitNode đã được tạo hoặc cập nhật, hoặc None nếu lỗi
        """
        if isinstance(unit, dict):
            unit = ManagementUnitNode(
                unit_id=unit.get("unit_id"),
                unit_name=unit.get("unit_name"),
                unit_code=unit.get("unit_code"),
                unit_type=unit.get("unit_type"),
                address=unit.get("address"),
                contact_info=unit.get("contact_info"),
                parent_id=unit.get("parent_id"),
                level=unit.get("level"),
                region=unit.get("region"),
                status=unit.get("status"),
                additional_info=unit.get("additional_info")
            )
        
        try:
            # Tạo hoặc cập nhật node
            params = unit.to_dict()
            result = await self.neo4j.execute_query(
                ManagementUnitNode.create_query(),
                params
            )
            
            # Create INSTANCE_OF relationship if the method exists
            if hasattr(unit, 'create_instance_of_relationship_query'):
                await self.neo4j.execute_query(
                    unit.create_instance_of_relationship_query(),
                    params
                )
                logger.info(f"Created INSTANCE_OF relationship for management unit {unit.unit_id}")
            
            if result and len(result) > 0:
                logger.info(f"Successfully created/updated management unit {unit.unit_id} in Neo4j")
                return unit
            else:
                logger.error(f"No result returned for management unit {unit.unit_id}")
                return None
                
        except Neo4jError as e:
            logger.error(f"Error creating/updating ManagementUnit node: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in create_or_update: {e}")
            return None
    
    async def get_by_id(self, unit_id: str) -> Optional[ManagementUnitNode]:
        """
        Lấy ManagementUnit theo ID.
        
        Args:
            unit_id: ID của đơn vị quản lý cần tìm
            
        Returns:
            ManagementUnitNode nếu tìm thấy, hoặc None nếu không
        """
        query = """
        MATCH (m:ManagementUnit {unit_id: $unit_id})
        RETURN m
        """
        
        try:
            result = await self.neo4j.execute_query(query, {"unit_id": unit_id})
            if result and len(result) > 0 and result[0][0] is not None:
                node_data = dict(result[0][0])
                # Create ManagementUnitNode directly from the node properties
                return ManagementUnitNode(
                    unit_id=node_data.get('unit_id'),
                    unit_name=node_data.get('unit_name', f"Unit {unit_id}"),
                    unit_code=node_data.get('unit_code'),
                    unit_type=node_data.get('unit_type'),
                    address=node_data.get('address'),
                    contact_info=node_data.get('contact_info'),
                    parent_id=node_data.get('parent_id'),
                    level=node_data.get('level'),
                    region=node_data.get('region'),
                    status=node_data.get('status'),
                    additional_info=node_data.get('additional_info')
                )
            return None
        except Neo4jError as e:
            logger.error(f"Error retrieving ManagementUnit by ID {unit_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in get_by_id: {e}")
            return None
    
    async def delete(self, unit_id: str) -> bool:
        """
        Xóa node ManagementUnit.
        
        Args:
            unit_id: ID của đơn vị quản lý cần xóa
            
        Returns:
            True nếu xóa thành công, False nếu lỗi
        """
        query = """
        MATCH (m:ManagementUnit {unit_id: $unit_id})
        DETACH DELETE m
        RETURN count(m) as deleted_count
        """
        
        try:
            result = await self.neo4j.execute_query(query, {"unit_id": unit_id})
            return result and len(result) > 0 and result[0][0] > 0
        except Neo4jError as e:
            logger.error(f"Error deleting ManagementUnit: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error in delete: {e}")
            return False
    
    async def get_by_type(self, unit_type: str) -> List[ManagementUnitNode]:
        """
        Lấy tất cả các đơn vị quản lý theo loại.
        
        Args:
            unit_type: Loại đơn vị quản lý (ví dụ: "MINISTRY", "DEPARTMENT", "SCHOOL")
            
        Returns:
            Danh sách các ManagementUnitNode thuộc loại cụ thể
        """
        query = """
        MATCH (m:ManagementUnit)
        WHERE m.unit_type = $unit_type
        RETURN m
        ORDER BY m.unit_name
        """
        
        try:
            result = await self.neo4j.execute_query(query, {"unit_type": unit_type})
            units = []
            if result and len(result) > 0:
                for record in result:
                    units.append(ManagementUnitNode.from_record({"m": record[0]}))
            return units
        except Neo4jError as e:
            logger.error(f"Error retrieving units by type: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error in get_by_type: {e}")
            return []
    
    async def get_children(self, parent_id: str) -> List[ManagementUnitNode]:
        """
        Lấy tất cả các đơn vị con của một đơn vị quản lý.
        
        Args:
            parent_id: ID của đơn vị quản lý cha
            
        Returns:
            Danh sách các ManagementUnitNode con
        """
        query = """
        MATCH (c:ManagementUnit)-[:BELONGS_TO]->(p:ManagementUnit {unit_id: $parent_id})
        RETURN c as m
        ORDER BY c.unit_name
        """
        
        try:
            result = await self.neo4j.execute_query(query, {"parent_id": parent_id})
            units = []
            if result and len(result) > 0:
                for record in result:
                    units.append(ManagementUnitNode.from_record({"m": record[0]}))
            return units
        except Neo4jError as e:
            logger.error(f"Error retrieving children units: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error in get_children: {e}")
            return []
    
    async def get_parent(self, unit_id: str) -> Optional[ManagementUnitNode]:
        """
        Lấy đơn vị quản lý cha của một đơn vị.
        
        Args:
            unit_id: ID của đơn vị quản lý con
            
        Returns:
            ManagementUnitNode cha nếu có, hoặc None nếu không
        """
        query = """
        MATCH (c:ManagementUnit {unit_id: $unit_id})-[:BELONGS_TO]->(p:ManagementUnit)
        RETURN p as m
        """
        
        try:
            result = await self.neo4j.execute_query(query, {"unit_id": unit_id})
            if result and len(result) > 0:
                return ManagementUnitNode.from_record({"m": result[0][0]})
            return None
        except Neo4jError as e:
            logger.error(f"Error retrieving parent unit: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in get_parent: {e}")
            return None
    
    async def get_by_region(self, region: str) -> List[ManagementUnitNode]:
        """
        Lấy tất cả các đơn vị quản lý trong một khu vực.
        
        Args:
            region: Khu vực (ví dụ: "North", "South", "Central")
            
        Returns:
            Danh sách các ManagementUnitNode trong khu vực
        """
        query = """
        MATCH (m:ManagementUnit)
        WHERE m.region = $region
        RETURN m
        ORDER BY m.unit_name
        """
        
        try:
            result = await self.neo4j.execute_query(query, {"region": region})
            units = []
            if result and len(result) > 0:
                for record in result:
                    units.append(ManagementUnitNode.from_record({"m": record[0]}))
            return units
        except Neo4jError as e:
            logger.error(f"Error retrieving units by region: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error in get_by_region: {e}")
            return []
    
    async def get_all_units(self) -> List[ManagementUnitNode]:
        """
        Lấy tất cả các đơn vị quản lý.
        
        Returns:
            Danh sách tất cả các ManagementUnitNode
        """
        query = """
        MATCH (m:ManagementUnit)
        RETURN m
        ORDER BY m.unit_name
        """
        
        try:
            result = await self.neo4j.execute_query(query)
            units = []
            if result and len(result) > 0:
                for record in result:
                    units.append(ManagementUnitNode.from_record({"m": record[0]}))
            return units
        except Neo4jError as e:
            logger.error(f"Error retrieving all units: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error in get_all_units: {e}")
            return []
    
    async def add_manages_exam_relationship(self, unit_id: str, exam_id: str) -> bool:
        """
        Thêm mối quan hệ quản lý giữa đơn vị và kỳ thi.
        
        Args:
            unit_id: ID của đơn vị quản lý
            exam_id: ID của kỳ thi
            
        Returns:
            True nếu thành công, False nếu lỗi
        """
        query = f"""
        MATCH (m:ManagementUnit {{unit_id: $unit_id}})
        MATCH (e:Exam {{exam_id: $exam_id}})
        MERGE (e)-[r:{ORGANIZED_BY_REL}]->(m)
        RETURN m, e
        """
        
        try:
            result = await self.neo4j.execute_query(
                query, 
                {"unit_id": unit_id, "exam_id": exam_id}
            )
            if result and len(result) > 0:
                logger.info(f"Added {ORGANIZED_BY_REL} relationship between Exam {exam_id} and ManagementUnit {unit_id}")
                return True
            else:
                logger.error(f"Failed to add {ORGANIZED_BY_REL} relationship between Exam {exam_id} and ManagementUnit {unit_id}")
                return False
        except Neo4jError as e:
            logger.error(f"Error adding manages exam relationship: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error in add_manages_exam_relationship: {e}")
            return False
    
    async def add_operates_location_relationship(self, unit_id: str, location_id: str) -> bool:
        """
        Thêm mối quan hệ vận hành giữa đơn vị và địa điểm thi.
        
        Args:
            unit_id: ID của đơn vị quản lý
            location_id: ID của địa điểm thi
            
        Returns:
            True nếu thành công, False nếu lỗi
        """
        query = f"""
        MATCH (m:ManagementUnit {{unit_id: $unit_id}})
        MATCH (l:ExamLocation {{location_id: $location_id}})
        MERGE (m)-[r:{OPERATES_REL}]->(l)
        RETURN m, l
        """
        
        try:
            result = await self.neo4j.execute_query(
                query, 
                {"unit_id": unit_id, "location_id": location_id}
            )
            if result and len(result) > 0:
                logger.info(f"Added {OPERATES_REL} relationship between ManagementUnit {unit_id} and ExamLocation {location_id}")
                return True
            else:
                logger.error(f"Failed to add {OPERATES_REL} relationship between ManagementUnit {unit_id} and ExamLocation {location_id}")
                return False
        except Neo4jError as e:
            logger.error(f"Error adding operates location relationship: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error in add_operates_location_relationship: {e}")
            return False
            
    async def get_organized_exams(self, unit_id: str) -> List[Dict]:
        """
        Lấy tất cả các kỳ thi được tổ chức bởi đơn vị quản lý.
        
        Args:
            unit_id: ID của đơn vị quản lý
            
        Returns:
            Danh sách các kỳ thi
        """
        query = f"""
        MATCH (e:Exam)-[r:{ORGANIZED_BY_REL}]->(m:ManagementUnit {{unit_id: $unit_id}})
        RETURN e, r
        """
        
        try:
            result = await self.neo4j.execute_query(query, {"unit_id": unit_id})
            exams = []
            if result and len(result) > 0:
                for record in result:
                    exam = record[0]
                    relationship = record[1]
                    exams.append({
                        "exam_id": exam["exam_id"],
                        "exam_name": exam["exam_name"],
                        "start_date": exam.get("start_date"),
                        "end_date": exam.get("end_date"),
                        "scope": exam.get("scope"),
                        "relationship": {
                            "role": relationship.get("role"),
                            "start_date": relationship.get("start_date"),
                            "end_date": relationship.get("end_date")
                        }
                    })
            return exams
        except Neo4jError as e:
            logger.error(f"Error retrieving organized exams: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error in get_organized_exams: {e}")
            return []
    
    async def add_organizes_relationship(self, unit_id: str, exam_id: str) -> bool:
        """
        Add an organizing relationship between a management unit and an exam.
        
        Args:
            unit_id: ID of the management unit
            exam_id: ID of the exam
            
        Returns:
            True if successful, False otherwise
        """
        # This method just calls the add_manages_exam_relationship method
        # with a more descriptive name that matches what's used in the sync service
        return await self.add_manages_exam_relationship(unit_id, exam_id)