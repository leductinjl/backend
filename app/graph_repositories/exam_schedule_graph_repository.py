"""
Exam Schedule Graph Repository.

This module defines the ExamScheduleGraphRepository class for managing ExamSchedule nodes in Neo4j.
"""

import logging
from typing import Dict, List, Optional, Union

from neo4j import Driver
from neo4j.exceptions import Neo4jError

from app.domain.graph_models.exam_schedule_node import ExamScheduleNode

logger = logging.getLogger(__name__)

class ExamScheduleGraphRepository:
    """
    Repository for ExamSchedule nodes in Neo4j Knowledge Graph.
    
    Cung cấp các phương thức để tương tác với các node ExamSchedule trong Neo4j.
    """
    
    def __init__(self, driver: Driver):
        """
        Khởi tạo repository với neo4j driver.
        
        Args:
            driver: Neo4j driver instance
        """
        self.driver = driver
        
    def create_or_update(self, schedule: Union[Dict, ExamScheduleNode]) -> Optional[ExamScheduleNode]:
        """
        Tạo mới hoặc cập nhật node ExamSchedule.
        
        Args:
            schedule: ExamScheduleNode hoặc dictionary chứa thông tin lịch thi
            
        Returns:
            ExamScheduleNode đã được tạo hoặc cập nhật, hoặc None nếu lỗi
        """
        if isinstance(schedule, dict):
            schedule = ExamScheduleNode(
                schedule_id=schedule.get("schedule_id"),
                schedule_name=schedule.get("schedule_name", f"Schedule {schedule.get('schedule_id')}"),
                exam_id=schedule.get("exam_id"),
                room_id=schedule.get("room_id"),
                start_time=schedule.get("start_time"),
                end_time=schedule.get("end_time"),
                date=schedule.get("date"),
                status=schedule.get("status"),
                max_participants=schedule.get("max_participants"),
                additional_info=schedule.get("additional_info")
            )
        
        try:
            with self.driver.session() as session:
                # Tạo hoặc cập nhật node
                result = session.execute_write(
                    lambda tx: tx.run(
                        ExamScheduleNode.create_query(),
                        **schedule.to_dict()
                    ).single()
                )
                
                # Tạo các mối quan hệ
                session.execute_write(
                    lambda tx: tx.run(
                        schedule.create_relationships_query(),
                        **schedule.to_dict()
                    )
                )
                
                return ExamScheduleNode.from_record(result)
        except Neo4jError as e:
            logger.error(f"Error creating/updating ExamSchedule node: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in create_or_update: {e}")
            return None
    
    def get_by_id(self, schedule_id: str) -> Optional[ExamScheduleNode]:
        """
        Lấy ExamSchedule theo ID.
        
        Args:
            schedule_id: ID của lịch thi cần tìm
            
        Returns:
            ExamScheduleNode nếu tìm thấy, hoặc None nếu không
        """
        query = """
        MATCH (s:ExamSchedule {schedule_id: $schedule_id})
        RETURN s
        """
        
        try:
            with self.driver.session() as session:
                result = session.execute_read(
                    lambda tx: tx.run(query, schedule_id=schedule_id).single()
                )
                return ExamScheduleNode.from_record(result) if result else None
        except Neo4jError as e:
            logger.error(f"Error retrieving ExamSchedule by ID: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in get_by_id: {e}")
            return None
    
    def delete(self, schedule_id: str) -> bool:
        """
        Xóa node ExamSchedule.
        
        Args:
            schedule_id: ID của lịch thi cần xóa
            
        Returns:
            True nếu xóa thành công, False nếu lỗi
        """
        query = """
        MATCH (s:ExamSchedule {schedule_id: $schedule_id})
        DETACH DELETE s
        RETURN count(s) as deleted_count
        """
        
        try:
            with self.driver.session() as session:
                result = session.execute_write(
                    lambda tx: tx.run(query, schedule_id=schedule_id).single()
                )
                return result and result["deleted_count"] > 0
        except Neo4jError as e:
            logger.error(f"Error deleting ExamSchedule: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error in delete: {e}")
            return False
    
    def get_by_exam(self, exam_id: str) -> List[ExamScheduleNode]:
        """
        Lấy tất cả các lịch thi cho một kỳ thi.
        
        Args:
            exam_id: ID của kỳ thi
            
        Returns:
            Danh sách các ExamScheduleNode cho kỳ thi
        """
        query = """
        MATCH (s:ExamSchedule)-[:SCHEDULES]->(e:Exam {exam_id: $exam_id})
        RETURN s
        """
        
        try:
            with self.driver.session() as session:
                result = session.execute_read(
                    lambda tx: tx.run(query, exam_id=exam_id).data()
                )
                return [ExamScheduleNode.from_record(record) for record in result]
        except Neo4jError as e:
            logger.error(f"Error retrieving schedules by exam: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error in get_by_exam: {e}")
            return []
    
    def get_by_room(self, room_id: str) -> List[ExamScheduleNode]:
        """
        Lấy tất cả các lịch thi tại một phòng thi.
        
        Args:
            room_id: ID của phòng thi
            
        Returns:
            Danh sách các ExamScheduleNode tại phòng thi
        """
        query = """
        MATCH (s:ExamSchedule)-[:ASSIGNED_TO]->(r:ExamRoom {room_id: $room_id})
        RETURN s
        """
        
        try:
            with self.driver.session() as session:
                result = session.execute_read(
                    lambda tx: tx.run(query, room_id=room_id).data()
                )
                return [ExamScheduleNode.from_record(record) for record in result]
        except Neo4jError as e:
            logger.error(f"Error retrieving schedules by room: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error in get_by_room: {e}")
            return []
    
    def get_by_date_range(self, start_date, end_date) -> List[ExamScheduleNode]:
        """
        Lấy tất cả các lịch thi trong một khoảng thời gian.
        
        Args:
            start_date: Ngày bắt đầu
            end_date: Ngày kết thúc
            
        Returns:
            Danh sách các ExamScheduleNode trong khoảng thời gian
        """
        query = """
        MATCH (s:ExamSchedule)
        WHERE s.date >= $start_date AND s.date <= $end_date
        RETURN s
        """
        
        try:
            with self.driver.session() as session:
                result = session.execute_read(
                    lambda tx: tx.run(query, start_date=start_date, end_date=end_date).data()
                )
                return [ExamScheduleNode.from_record(record) for record in result]
        except Neo4jError as e:
            logger.error(f"Error retrieving schedules by date range: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error in get_by_date_range: {e}")
            return []
    
    def get_all_schedules(self) -> List[ExamScheduleNode]:
        """
        Lấy tất cả các lịch thi.
        
        Returns:
            Danh sách tất cả các ExamScheduleNode
        """
        query = """
        MATCH (s:ExamSchedule)
        RETURN s
        """
        
        try:
            with self.driver.session() as session:
                result = session.execute_read(
                    lambda tx: tx.run(query).data()
                )
                return [ExamScheduleNode.from_record(record) for record in result]
        except Neo4jError as e:
            logger.error(f"Error retrieving all schedules: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error in get_all_schedules: {e}")
            return []
    
    def add_participant(self, schedule_id: str, candidate_id: str) -> bool:
        """
        Thêm thí sinh vào lịch thi.
        
        Args:
            schedule_id: ID của lịch thi
            candidate_id: ID của thí sinh
            
        Returns:
            True nếu thành công, False nếu lỗi
        """
        query = """
        MATCH (s:ExamSchedule {schedule_id: $schedule_id})
        MATCH (c:Candidate {candidate_id: $candidate_id})
        MERGE (c)-[:PARTICIPATES_IN]->(s)
        RETURN s, c
        """
        
        try:
            with self.driver.session() as session:
                result = session.execute_write(
                    lambda tx: tx.run(query, schedule_id=schedule_id, candidate_id=candidate_id).data()
                )
                return len(result) > 0
        except Neo4jError as e:
            logger.error(f"Error adding participant: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error in add_participant: {e}")
            return False
    
    def get_participants(self, schedule_id: str) -> List[Dict]:
        """
        Lấy danh sách thí sinh tham gia lịch thi.
        
        Args:
            schedule_id: ID của lịch thi
            
        Returns:
            Danh sách các thông tin thí sinh
        """
        query = """
        MATCH (c:Candidate)-[:PARTICIPATES_IN]->(s:ExamSchedule {schedule_id: $schedule_id})
        RETURN c
        """
        
        try:
            with self.driver.session() as session:
                result = session.execute_read(
                    lambda tx: tx.run(query, schedule_id=schedule_id).data()
                )
                return [record["c"] for record in result]
        except Neo4jError as e:
            logger.error(f"Error retrieving participants: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error in get_participants: {e}")
            return [] 