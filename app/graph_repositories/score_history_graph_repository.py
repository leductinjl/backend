"""
Score History Graph Repository.

This module defines the ScoreHistoryGraphRepository class for managing ScoreHistory nodes in Neo4j.
"""

import logging
from typing import Dict, List, Optional, Union

from neo4j import Driver
from neo4j.exceptions import Neo4jError

from app.domain.graph_models.score_history_node import ScoreHistoryNode

logger = logging.getLogger(__name__)

class ScoreHistoryGraphRepository:
    """
    Repository for ScoreHistory nodes in Neo4j Knowledge Graph.
    
    Cung cấp các phương thức để tương tác với các node ScoreHistory trong Neo4j.
    """
    
    def __init__(self, driver: Driver):
        """
        Khởi tạo repository với neo4j driver.
        
        Args:
            driver: Neo4j driver instance
        """
        self.driver = driver
        
    def create_or_update(self, history: Union[Dict, ScoreHistoryNode]) -> Optional[ScoreHistoryNode]:
        """
        Tạo mới hoặc cập nhật node ScoreHistory.
        
        Args:
            history: ScoreHistoryNode hoặc dictionary chứa thông tin lịch sử điểm
            
        Returns:
            ScoreHistoryNode đã được tạo hoặc cập nhật, hoặc None nếu lỗi
        """
        if isinstance(history, dict):
            history = ScoreHistoryNode(
                history_id=history.get("history_id"),
                history_name=history.get("history_name"),
                score_id=history.get("score_id"),
                candidate_id=history.get("candidate_id"),
                subject_id=history.get("subject_id"),
                exam_id=history.get("exam_id"),
                old_value=history.get("old_value"),
                new_value=history.get("new_value"),
                change_date=history.get("change_date"),
                change_type=history.get("change_type"),
                changed_by=history.get("changed_by"),
                reason=history.get("reason"),
                additional_info=history.get("additional_info")
            )
        
        try:
            with self.driver.session() as session:
                # Tạo hoặc cập nhật node
                result = session.execute_write(
                    lambda tx: tx.run(
                        ScoreHistoryNode.create_query(),
                        **history.to_dict()
                    ).single()
                )
                
                # Tạo các mối quan hệ
                session.execute_write(
                    lambda tx: tx.run(
                        history.create_relationships_query(),
                        **history.to_dict()
                    )
                )
                
                return ScoreHistoryNode.from_record(result)
        except Neo4jError as e:
            logger.error(f"Error creating/updating ScoreHistory node: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in create_or_update: {e}")
            return None
    
    def get_by_id(self, history_id: str) -> Optional[ScoreHistoryNode]:
        """
        Lấy ScoreHistory theo ID.
        
        Args:
            history_id: ID của lịch sử điểm cần tìm
            
        Returns:
            ScoreHistoryNode nếu tìm thấy, hoặc None nếu không
        """
        query = """
        MATCH (h:ScoreHistory {history_id: $history_id})
        RETURN h
        """
        
        try:
            with self.driver.session() as session:
                result = session.execute_read(
                    lambda tx: tx.run(query, history_id=history_id).single()
                )
                return ScoreHistoryNode.from_record(result) if result else None
        except Neo4jError as e:
            logger.error(f"Error retrieving ScoreHistory by ID: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in get_by_id: {e}")
            return None
    
    def delete(self, history_id: str) -> bool:
        """
        Xóa node ScoreHistory.
        
        Args:
            history_id: ID của lịch sử điểm cần xóa
            
        Returns:
            True nếu xóa thành công, False nếu lỗi
        """
        query = """
        MATCH (h:ScoreHistory {history_id: $history_id})
        DETACH DELETE h
        RETURN count(h) as deleted_count
        """
        
        try:
            with self.driver.session() as session:
                result = session.execute_write(
                    lambda tx: tx.run(query, history_id=history_id).single()
                )
                return result and result["deleted_count"] > 0
        except Neo4jError as e:
            logger.error(f"Error deleting ScoreHistory: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error in delete: {e}")
            return False
    
    def get_by_score(self, score_id: str) -> List[ScoreHistoryNode]:
        """
        Lấy tất cả lịch sử của một điểm.
        
        Args:
            score_id: ID của điểm
            
        Returns:
            Danh sách các ScoreHistoryNode của điểm
        """
        query = """
        MATCH (h:ScoreHistory)-[:HISTORY_OF]->(s:Score {score_id: $score_id})
        RETURN h
        ORDER BY h.change_date DESC
        """
        
        try:
            with self.driver.session() as session:
                result = session.execute_read(
                    lambda tx: tx.run(query, score_id=score_id).data()
                )
                return [ScoreHistoryNode.from_record(record) for record in result]
        except Neo4jError as e:
            logger.error(f"Error retrieving history by score: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error in get_by_score: {e}")
            return []
    
    def get_by_candidate(self, candidate_id: str) -> List[ScoreHistoryNode]:
        """
        Lấy tất cả lịch sử điểm của một thí sinh.
        
        Args:
            candidate_id: ID của thí sinh
            
        Returns:
            Danh sách các ScoreHistoryNode của thí sinh
        """
        query = """
        MATCH (h:ScoreHistory)-[:FOR_CANDIDATE]->(c:Candidate {candidate_id: $candidate_id})
        RETURN h
        ORDER BY h.change_date DESC
        """
        
        try:
            with self.driver.session() as session:
                result = session.execute_read(
                    lambda tx: tx.run(query, candidate_id=candidate_id).data()
                )
                return [ScoreHistoryNode.from_record(record) for record in result]
        except Neo4jError as e:
            logger.error(f"Error retrieving history by candidate: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error in get_by_candidate: {e}")
            return []
    
    def get_by_subject(self, subject_id: str) -> List[ScoreHistoryNode]:
        """
        Lấy tất cả lịch sử điểm của một môn học.
        
        Args:
            subject_id: ID của môn học
            
        Returns:
            Danh sách các ScoreHistoryNode của môn học
        """
        query = """
        MATCH (h:ScoreHistory)-[:FOR_SUBJECT]->(s:Subject {subject_id: $subject_id})
        RETURN h
        ORDER BY h.change_date DESC
        """
        
        try:
            with self.driver.session() as session:
                result = session.execute_read(
                    lambda tx: tx.run(query, subject_id=subject_id).data()
                )
                return [ScoreHistoryNode.from_record(record) for record in result]
        except Neo4jError as e:
            logger.error(f"Error retrieving history by subject: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error in get_by_subject: {e}")
            return []
    
    def get_by_exam(self, exam_id: str) -> List[ScoreHistoryNode]:
        """
        Lấy tất cả lịch sử điểm của một kỳ thi.
        
        Args:
            exam_id: ID của kỳ thi
            
        Returns:
            Danh sách các ScoreHistoryNode của kỳ thi
        """
        query = """
        MATCH (h:ScoreHistory)-[:IN_EXAM]->(e:Exam {exam_id: $exam_id})
        RETURN h
        ORDER BY h.change_date DESC
        """
        
        try:
            with self.driver.session() as session:
                result = session.execute_read(
                    lambda tx: tx.run(query, exam_id=exam_id).data()
                )
                return [ScoreHistoryNode.from_record(record) for record in result]
        except Neo4jError as e:
            logger.error(f"Error retrieving history by exam: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error in get_by_exam: {e}")
            return []
    
    def get_by_change_type(self, change_type: str) -> List[ScoreHistoryNode]:
        """
        Lấy tất cả lịch sử điểm theo loại thay đổi.
        
        Args:
            change_type: Loại thay đổi (ví dụ: "review", "correction", etc.)
            
        Returns:
            Danh sách các ScoreHistoryNode theo loại thay đổi
        """
        query = """
        MATCH (h:ScoreHistory)
        WHERE h.change_type = $change_type
        RETURN h
        ORDER BY h.change_date DESC
        """
        
        try:
            with self.driver.session() as session:
                result = session.execute_read(
                    lambda tx: tx.run(query, change_type=change_type).data()
                )
                return [ScoreHistoryNode.from_record(record) for record in result]
        except Neo4jError as e:
            logger.error(f"Error retrieving history by change type: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error in get_by_change_type: {e}")
            return []
    
    def get_all_histories(self) -> List[ScoreHistoryNode]:
        """
        Lấy tất cả lịch sử điểm.
        
        Returns:
            Danh sách tất cả các ScoreHistoryNode
        """
        query = """
        MATCH (h:ScoreHistory)
        RETURN h
        ORDER BY h.change_date DESC
        """
        
        try:
            with self.driver.session() as session:
                result = session.execute_read(
                    lambda tx: tx.run(query).data()
                )
                return [ScoreHistoryNode.from_record(record) for record in result]
        except Neo4jError as e:
            logger.error(f"Error retrieving all histories: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error in get_all_histories: {e}")
            return [] 