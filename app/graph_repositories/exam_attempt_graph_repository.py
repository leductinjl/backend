"""
Exam Attempt Graph Repository.

This module defines the ExamAttemptGraphRepository class for managing ExamAttempt nodes in Neo4j.
"""

import logging
from typing import Dict, List, Optional, Union

from neo4j import Driver
from neo4j.exceptions import Neo4jError

from app.domain.graph_models.exam_attempt_node import ExamAttemptNode

logger = logging.getLogger(__name__)

class ExamAttemptGraphRepository:
    """
    Repository for ExamAttempt nodes in Neo4j Knowledge Graph.
    
    Cung cấp các phương thức để tương tác với các node ExamAttempt trong Neo4j.
    """
    
    def __init__(self, driver: Driver):
        """
        Khởi tạo repository với neo4j driver.
        
        Args:
            driver: Neo4j driver instance
        """
        self.driver = driver
        
    def create_or_update(self, attempt: Union[Dict, ExamAttemptNode]) -> Optional[ExamAttemptNode]:
        """
        Tạo mới hoặc cập nhật node ExamAttempt.
        
        Args:
            attempt: ExamAttemptNode hoặc dictionary chứa thông tin lần thi
            
        Returns:
            ExamAttemptNode đã được tạo hoặc cập nhật, hoặc None nếu lỗi
        """
        if isinstance(attempt, dict):
            attempt = ExamAttemptNode(
                attempt_id=attempt.get("attempt_id"),
                attempt_name=attempt.get("attempt_name"),
                candidate_id=attempt.get("candidate_id"),
                exam_id=attempt.get("exam_id"),
                schedule_id=attempt.get("schedule_id"),
                room_id=attempt.get("room_id"),
                status=attempt.get("status"),
                start_time=attempt.get("start_time"),
                end_time=attempt.get("end_time"),
                duration=attempt.get("duration"),
                score=attempt.get("score"),
                attempt_number=attempt.get("attempt_number"),
                submitted=attempt.get("submitted"),
                additional_info=attempt.get("additional_info")
            )
        
        try:
            with self.driver.session() as session:
                # Tạo hoặc cập nhật node
                result = session.execute_write(
                    lambda tx: tx.run(
                        ExamAttemptNode.create_query(),
                        **attempt.to_dict()
                    ).single()
                )
                
                # Tạo các mối quan hệ
                session.execute_write(
                    lambda tx: tx.run(
                        attempt.create_relationships_query(),
                        **attempt.to_dict()
                    )
                )
                
                return ExamAttemptNode.from_record(result)
        except Neo4jError as e:
            logger.error(f"Error creating/updating ExamAttempt node: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in create_or_update: {e}")
            return None
    
    def get_by_id(self, attempt_id: str) -> Optional[ExamAttemptNode]:
        """
        Lấy ExamAttempt theo ID.
        
        Args:
            attempt_id: ID của lần thi cần tìm
            
        Returns:
            ExamAttemptNode nếu tìm thấy, hoặc None nếu không
        """
        query = """
        MATCH (a:ExamAttempt {attempt_id: $attempt_id})
        RETURN a
        """
        
        try:
            with self.driver.session() as session:
                result = session.execute_read(
                    lambda tx: tx.run(query, attempt_id=attempt_id).single()
                )
                return ExamAttemptNode.from_record(result) if result else None
        except Neo4jError as e:
            logger.error(f"Error retrieving ExamAttempt by ID: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in get_by_id: {e}")
            return None
    
    def delete(self, attempt_id: str) -> bool:
        """
        Xóa node ExamAttempt.
        
        Args:
            attempt_id: ID của lần thi cần xóa
            
        Returns:
            True nếu xóa thành công, False nếu lỗi
        """
        query = """
        MATCH (a:ExamAttempt {attempt_id: $attempt_id})
        DETACH DELETE a
        RETURN count(a) as deleted_count
        """
        
        try:
            with self.driver.session() as session:
                result = session.execute_write(
                    lambda tx: tx.run(query, attempt_id=attempt_id).single()
                )
                return result and result["deleted_count"] > 0
        except Neo4jError as e:
            logger.error(f"Error deleting ExamAttempt: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error in delete: {e}")
            return False
    
    def get_by_candidate(self, candidate_id: str) -> List[ExamAttemptNode]:
        """
        Lấy tất cả các lần thi của một thí sinh.
        
        Args:
            candidate_id: ID của thí sinh
            
        Returns:
            Danh sách các ExamAttemptNode của thí sinh
        """
        query = """
        MATCH (c:Candidate {candidate_id: $candidate_id})-[:ATTEMPTED]->(a:ExamAttempt)
        RETURN a
        """
        
        try:
            with self.driver.session() as session:
                result = session.execute_read(
                    lambda tx: tx.run(query, candidate_id=candidate_id).data()
                )
                return [ExamAttemptNode.from_record(record) for record in result]
        except Neo4jError as e:
            logger.error(f"Error retrieving attempts by candidate: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error in get_by_candidate: {e}")
            return []
    
    def get_by_exam(self, exam_id: str) -> List[ExamAttemptNode]:
        """
        Lấy tất cả các lần thi của một kỳ thi.
        
        Args:
            exam_id: ID của kỳ thi
            
        Returns:
            Danh sách các ExamAttemptNode cho kỳ thi
        """
        query = """
        MATCH (a:ExamAttempt)-[:FOR_EXAM]->(e:Exam {exam_id: $exam_id})
        RETURN a
        """
        
        try:
            with self.driver.session() as session:
                result = session.execute_read(
                    lambda tx: tx.run(query, exam_id=exam_id).data()
                )
                return [ExamAttemptNode.from_record(record) for record in result]
        except Neo4jError as e:
            logger.error(f"Error retrieving attempts by exam: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error in get_by_exam: {e}")
            return []
    
    def get_by_schedule(self, schedule_id: str) -> List[ExamAttemptNode]:
        """
        Lấy tất cả các lần thi trong một lịch thi.
        
        Args:
            schedule_id: ID của lịch thi
            
        Returns:
            Danh sách các ExamAttemptNode trong lịch thi
        """
        query = """
        MATCH (a:ExamAttempt)-[:IN_SCHEDULE]->(s:ExamSchedule {schedule_id: $schedule_id})
        RETURN a
        """
        
        try:
            with self.driver.session() as session:
                result = session.execute_read(
                    lambda tx: tx.run(query, schedule_id=schedule_id).data()
                )
                return [ExamAttemptNode.from_record(record) for record in result]
        except Neo4jError as e:
            logger.error(f"Error retrieving attempts by schedule: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error in get_by_schedule: {e}")
            return []
    
    def get_by_room(self, room_id: str) -> List[ExamAttemptNode]:
        """
        Lấy tất cả các lần thi tại một phòng thi.
        
        Args:
            room_id: ID của phòng thi
            
        Returns:
            Danh sách các ExamAttemptNode tại phòng thi
        """
        query = """
        MATCH (a:ExamAttempt)-[:IN_ROOM]->(r:ExamRoom {room_id: $room_id})
        RETURN a
        """
        
        try:
            with self.driver.session() as session:
                result = session.execute_read(
                    lambda tx: tx.run(query, room_id=room_id).data()
                )
                return [ExamAttemptNode.from_record(record) for record in result]
        except Neo4jError as e:
            logger.error(f"Error retrieving attempts by room: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error in get_by_room: {e}")
            return []
    
    def get_by_status(self, status: str) -> List[ExamAttemptNode]:
        """
        Lấy tất cả các lần thi có trạng thái cụ thể.
        
        Args:
            status: Trạng thái của lần thi
            
        Returns:
            Danh sách các ExamAttemptNode có trạng thái tương ứng
        """
        query = """
        MATCH (a:ExamAttempt)
        WHERE a.status = $status
        RETURN a
        """
        
        try:
            with self.driver.session() as session:
                result = session.execute_read(
                    lambda tx: tx.run(query, status=status).data()
                )
                return [ExamAttemptNode.from_record(record) for record in result]
        except Neo4jError as e:
            logger.error(f"Error retrieving attempts by status: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error in get_by_status: {e}")
            return []
    
    def get_all_attempts(self) -> List[ExamAttemptNode]:
        """
        Lấy tất cả các lần thi.
        
        Returns:
            Danh sách tất cả các ExamAttemptNode
        """
        query = """
        MATCH (a:ExamAttempt)
        RETURN a
        """
        
        try:
            with self.driver.session() as session:
                result = session.execute_read(
                    lambda tx: tx.run(query).data()
                )
                return [ExamAttemptNode.from_record(record) for record in result]
        except Neo4jError as e:
            logger.error(f"Error retrieving all attempts: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error in get_all_attempts: {e}")
            return [] 