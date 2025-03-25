"""
Exam Room Graph Repository.

This module defines the ExamRoomGraphRepository class for managing ExamRoom nodes in Neo4j.
"""

import logging
from typing import Dict, List, Optional, Union

from neo4j import AsyncDriver
from neo4j.exceptions import Neo4jError

from app.domain.graph_models.exam_room_node import ExamRoomNode, INSTANCE_OF_REL, LOCATED_IN_REL
from app.infrastructure.ontology.ontology import RELATIONSHIPS

logger = logging.getLogger(__name__)

# Define relationship constants
HELD_IN_REL = RELATIONSHIPS["HELD_AT"]["type"]  # Using HELD_AT since there's no HELD_IN in ontology

class ExamRoomGraphRepository:
    """
    Repository for ExamRoom nodes in Neo4j Knowledge Graph.
    
    Cung cấp các phương thức để tương tác với các node ExamRoom trong Neo4j.
    """
    
    def __init__(self, driver: AsyncDriver):
        """
        Khởi tạo repository với neo4j driver.
        
        Args:
            driver: Neo4j async driver instance
        """
        self.driver = driver
        
    async def create_or_update(self, room: Union[Dict, ExamRoomNode]) -> Optional[ExamRoomNode]:
        """
        Tạo mới hoặc cập nhật node ExamRoom.
        
        Args:
            room: ExamRoomNode hoặc dictionary chứa thông tin phòng thi
            
        Returns:
            ExamRoomNode đã được tạo hoặc cập nhật, hoặc None nếu lỗi
        """
        if isinstance(room, dict):
            room = ExamRoomNode(
                room_id=room.get("room_id"),
                room_name=room.get("room_name"),
                location_id=room.get("location_id"),
                capacity=room.get("capacity"),
                floor=room.get("floor"),
                room_number=room.get("room_number"),
                room_type=room.get("room_type"),
                status=room.get("status"),
                additional_info=room.get("additional_info")
            )
        
        try:
            async with self.driver.session() as session:
                # Tạo hoặc cập nhật node
                result = await session.run(
                    ExamRoomNode.create_query(),
                    **room.to_dict()
                )
                record = await result.single()
                
                # Tạo mối quan hệ INSTANCE_OF nếu có phương thức
                if hasattr(room, 'create_instance_of_relationship_query'):
                    await session.run(
                        room.create_instance_of_relationship_query(),
                        **room.to_dict()
                    )
                    logger.info(f"Created INSTANCE_OF relationship for exam room {room.room_id}")
                
                return ExamRoomNode.from_record(record)
        except Neo4jError as e:
            logger.error(f"Error creating/updating ExamRoom node: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in create_or_update: {e}")
            return None
    
    async def get_by_id(self, room_id: str) -> Optional[ExamRoomNode]:
        """
        Lấy ExamRoom theo ID.
        
        Args:
            room_id: ID của phòng thi cần tìm
            
        Returns:
            ExamRoomNode nếu tìm thấy, hoặc None nếu không
        """
        query = """
        MATCH (r:ExamRoom {room_id: $room_id})
        RETURN r
        """
        
        try:
            async with self.driver.session() as session:
                result = await session.run(query, room_id=room_id)
                record = await result.single()
                return ExamRoomNode.from_record(record) if record else None
        except Neo4jError as e:
            logger.error(f"Error retrieving ExamRoom by ID: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in get_by_id: {e}")
            return None
    
    async def delete(self, room_id: str) -> bool:
        """
        Xóa node ExamRoom.
        
        Args:
            room_id: ID của phòng thi cần xóa
            
        Returns:
            True nếu xóa thành công, False nếu lỗi
        """
        query = """
        MATCH (r:ExamRoom {room_id: $room_id})
        DETACH DELETE r
        RETURN count(r) as deleted_count
        """
        
        try:
            async with self.driver.session() as session:
                result = await session.run(query, room_id=room_id)
                record = await result.single()
                return record and record["deleted_count"] > 0
        except Neo4jError as e:
            logger.error(f"Error deleting ExamRoom: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error in delete: {e}")
            return False
    
    async def get_by_location(self, location_id: str) -> List[ExamRoomNode]:
        """
        Lấy tất cả các phòng thi tại một địa điểm.
        
        Args:
            location_id: ID của địa điểm
            
        Returns:
            Danh sách các ExamRoomNode tại địa điểm
        """
        query = f"""
        MATCH (r:ExamRoom)-[:{LOCATED_IN_REL}]->(l:ExamLocation {{location_id: $location_id}})
        RETURN r
        """
        
        try:
            async with self.driver.session() as session:
                result = await session.run(query, location_id=location_id)
                records = await result.data()
                return [ExamRoomNode.from_record(record) for record in records]
        except Neo4jError as e:
            logger.error(f"Error retrieving rooms by location: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error in get_by_location: {e}")
            return []
    
    async def get_exams(self, room_id: str) -> List[Dict]:
        """
        Lấy tất cả các kỳ thi diễn ra tại một phòng thi.
        
        Args:
            room_id: ID của phòng thi
            
        Returns:
            Danh sách các thông tin kỳ thi
        """
        query = f"""
        MATCH (e:Exam)-[:{HELD_IN_REL}]->(r:ExamRoom {{room_id: $room_id}})
        RETURN e
        """
        
        try:
            async with self.driver.session() as session:
                result = await session.run(query, room_id=room_id)
                records = await result.data()
                return [record["e"] for record in records]
        except Neo4jError as e:
            logger.error(f"Error retrieving exams for room: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error in get_exams: {e}")
            return []
    
    async def get_all_rooms(self) -> List[ExamRoomNode]:
        """
        Lấy tất cả các phòng thi.
        
        Returns:
            Danh sách tất cả các ExamRoomNode
        """
        query = """
        MATCH (r:ExamRoom)
        RETURN r
        """
        
        try:
            async with self.driver.session() as session:
                result = await session.run(query)
                records = await result.data()
                return [ExamRoomNode.from_record(record) for record in records]
        except Neo4jError as e:
            logger.error(f"Error retrieving all rooms: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error in get_all_rooms: {e}")
            return []
    
    async def add_exam_relationship(self, room_id: str, exam_id: str) -> bool:
        """
        Thêm mối quan hệ giữa phòng thi và kỳ thi.
        
        Args:
            room_id: ID của phòng thi
            exam_id: ID của kỳ thi
            
        Returns:
            True nếu thành công, False nếu lỗi
        """
        query = f"""
        MATCH (r:ExamRoom {{room_id: $room_id}})
        MATCH (e:Exam {{exam_id: $exam_id}})
        MERGE (e)-[:{HELD_IN_REL}]->(r)
        RETURN r, e
        """
        
        try:
            async with self.driver.session() as session:
                result = await session.run(query, room_id=room_id, exam_id=exam_id)
                record = await result.single()
                return record is not None
        except Neo4jError as e:
            logger.error(f"Error adding exam relationship: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error in add_exam_relationship: {e}")
            return False 