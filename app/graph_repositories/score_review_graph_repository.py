"""
Score Review Graph Repository.

This module defines the ScoreReviewGraphRepository class for managing ScoreReview nodes in Neo4j.
"""

import logging
from typing import Dict, List, Optional, Union

from neo4j import Driver
from neo4j.exceptions import Neo4jError

from app.domain.graph_models.score_review_node import (
    ScoreReviewNode, INSTANCE_OF_REL, REQUESTS_REVIEW_REL, 
    FOR_SUBJECT_REL, IN_EXAM_REL, REVIEWS_REL
)

logger = logging.getLogger(__name__)

class ScoreReviewGraphRepository:
    """
    Repository for ScoreReview nodes in Neo4j Knowledge Graph.
    
    Cung cấp các phương thức để tương tác với các node ScoreReview trong Neo4j.
    """
    
    def __init__(self, driver: Driver):
        """
        Khởi tạo repository với neo4j driver.
        
        Args:
            driver: Neo4j driver instance
        """
        self.driver = driver
        
    def create_or_update(self, review: Union[Dict, ScoreReviewNode]) -> Optional[ScoreReviewNode]:
        """
        Tạo mới hoặc cập nhật node ScoreReview.
        
        Args:
            review: ScoreReviewNode hoặc dictionary chứa thông tin phúc khảo
            
        Returns:
            ScoreReviewNode đã được tạo hoặc cập nhật, hoặc None nếu lỗi
        """
        if isinstance(review, dict):
            review = ScoreReviewNode(
                review_id=review.get("review_id"),
                review_name=review.get("review_name"),
                score_id=review.get("score_id"),
                candidate_id=review.get("candidate_id"),
                subject_id=review.get("subject_id"),
                exam_id=review.get("exam_id"),
                status=review.get("status"),
                request_date=review.get("request_date"),
                resolution_date=review.get("resolution_date"),
                old_score=review.get("old_score"),
                new_score=review.get("new_score"),
                reviewer=review.get("reviewer"),
                reason=review.get("reason"),
                additional_info=review.get("additional_info")
            )
        
        try:
            with self.driver.session() as session:
                # Tạo hoặc cập nhật node
                result = session.execute_write(
                    lambda tx: tx.run(
                        ScoreReviewNode.create_query(),
                        **review.to_dict()
                    ).single()
                )
                
                # Tạo các mối quan hệ
                session.execute_write(
                    lambda tx: tx.run(
                        review.create_relationships_query(),
                        **review.to_dict()
                    )
                )
                
                # Tạo mối quan hệ INSTANCE_OF
                if hasattr(review, 'create_instance_of_relationship_query'):
                    session.execute_write(
                        lambda tx: tx.run(
                            review.create_instance_of_relationship_query(),
                            **review.to_dict()
                        )
                    )
                    logger.info(f"Created INSTANCE_OF relationship for ScoreReview {review.review_id}")
                
                logger.info(f"Successfully created/updated ScoreReview node: {review.review_id}")
                return ScoreReviewNode.from_record(result)
        except Neo4jError as e:
            logger.error(f"Error creating/updating ScoreReview node: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in create_or_update: {e}")
            return None
    
    def get_by_id(self, review_id: str) -> Optional[ScoreReviewNode]:
        """
        Lấy ScoreReview theo ID.
        
        Args:
            review_id: ID của đơn phúc khảo cần tìm
            
        Returns:
            ScoreReviewNode nếu tìm thấy, hoặc None nếu không
        """
        query = """
        MATCH (r:ScoreReview {review_id: $review_id})
        RETURN r
        """
        
        try:
            with self.driver.session() as session:
                result = session.execute_read(
                    lambda tx: tx.run(query, review_id=review_id).single()
                )
                return ScoreReviewNode.from_record(result) if result else None
        except Neo4jError as e:
            logger.error(f"Error retrieving ScoreReview by ID: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in get_by_id: {e}")
            return None
    
    def delete(self, review_id: str) -> bool:
        """
        Xóa node ScoreReview.
        
        Args:
            review_id: ID của đơn phúc khảo cần xóa
            
        Returns:
            True nếu xóa thành công, False nếu lỗi
        """
        query = """
        MATCH (r:ScoreReview {review_id: $review_id})
        DETACH DELETE r
        RETURN count(r) as deleted_count
        """
        
        try:
            with self.driver.session() as session:
                result = session.execute_write(
                    lambda tx: tx.run(query, review_id=review_id).single()
                )
                deleted = result and result["deleted_count"] > 0
                if deleted:
                    logger.info(f"Successfully deleted ScoreReview: {review_id}")
                else:
                    logger.warning(f"No ScoreReview found to delete with ID: {review_id}")
                return deleted
        except Neo4jError as e:
            logger.error(f"Error deleting ScoreReview: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error in delete: {e}")
            return False
    
    def get_by_candidate(self, candidate_id: str) -> List[ScoreReviewNode]:
        """
        Lấy tất cả các đơn phúc khảo của một thí sinh.
        
        Args:
            candidate_id: ID của thí sinh
            
        Returns:
            Danh sách các ScoreReviewNode của thí sinh
        """
        query = f"""
        MATCH (c:Candidate {{candidate_id: $candidate_id}})-[:{REQUESTS_REVIEW_REL}]->(r:ScoreReview)
        RETURN r
        """
        
        try:
            with self.driver.session() as session:
                result = session.execute_read(
                    lambda tx: tx.run(query, candidate_id=candidate_id).data()
                )
                reviews = [ScoreReviewNode.from_record(record) for record in result]
                logger.info(f"Retrieved {len(reviews)} score reviews for candidate {candidate_id}")
                return reviews
        except Neo4jError as e:
            logger.error(f"Error retrieving reviews by candidate: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error in get_by_candidate: {e}")
            return []
    
    def get_by_score(self, score_id: str) -> List[ScoreReviewNode]:
        """
        Lấy tất cả các đơn phúc khảo cho một điểm.
        
        Args:
            score_id: ID của điểm
            
        Returns:
            Danh sách các ScoreReviewNode cho điểm
        """
        query = f"""
        MATCH (r:ScoreReview)-[:{REVIEWS_REL}]->(s:Score {{score_id: $score_id}})
        RETURN r
        """
        
        try:
            with self.driver.session() as session:
                result = session.execute_read(
                    lambda tx: tx.run(query, score_id=score_id).data()
                )
                reviews = [ScoreReviewNode.from_record(record) for record in result]
                logger.info(f"Retrieved {len(reviews)} score reviews for score {score_id}")
                return reviews
        except Neo4jError as e:
            logger.error(f"Error retrieving reviews by score: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error in get_by_score: {e}")
            return []
    
    def get_by_exam(self, exam_id: str) -> List[ScoreReviewNode]:
        """
        Lấy tất cả các đơn phúc khảo trong một kỳ thi.
        
        Args:
            exam_id: ID của kỳ thi
            
        Returns:
            Danh sách các ScoreReviewNode trong kỳ thi
        """
        query = f"""
        MATCH (r:ScoreReview)-[:{IN_EXAM_REL}]->(e:Exam {{exam_id: $exam_id}})
        RETURN r
        """
        
        try:
            with self.driver.session() as session:
                result = session.execute_read(
                    lambda tx: tx.run(query, exam_id=exam_id).data()
                )
                reviews = [ScoreReviewNode.from_record(record) for record in result]
                logger.info(f"Retrieved {len(reviews)} score reviews for exam {exam_id}")
                return reviews
        except Neo4jError as e:
            logger.error(f"Error retrieving reviews by exam: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error in get_by_exam: {e}")
            return []
    
    def get_by_subject(self, subject_id: str) -> List[ScoreReviewNode]:
        """
        Lấy tất cả các đơn phúc khảo cho một môn học.
        
        Args:
            subject_id: ID của môn học
            
        Returns:
            Danh sách các ScoreReviewNode cho môn học
        """
        query = f"""
        MATCH (r:ScoreReview)-[:{FOR_SUBJECT_REL}]->(s:Subject {{subject_id: $subject_id}})
        RETURN r
        """
        
        try:
            with self.driver.session() as session:
                result = session.execute_read(
                    lambda tx: tx.run(query, subject_id=subject_id).data()
                )
                reviews = [ScoreReviewNode.from_record(record) for record in result]
                logger.info(f"Retrieved {len(reviews)} score reviews for subject {subject_id}")
                return reviews
        except Neo4jError as e:
            logger.error(f"Error retrieving reviews by subject: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error in get_by_subject: {e}")
            return []
    
    def get_by_status(self, status: str) -> List[ScoreReviewNode]:
        """
        Lấy tất cả các đơn phúc khảo có trạng thái cụ thể.
        
        Args:
            status: Trạng thái của đơn phúc khảo
            
        Returns:
            Danh sách các ScoreReviewNode có trạng thái tương ứng
        """
        query = """
        MATCH (r:ScoreReview)
        WHERE r.status = $status
        RETURN r
        """
        
        try:
            with self.driver.session() as session:
                result = session.execute_read(
                    lambda tx: tx.run(query, status=status).data()
                )
                reviews = [ScoreReviewNode.from_record(record) for record in result]
                logger.info(f"Retrieved {len(reviews)} score reviews with status '{status}'")
                return reviews
        except Neo4jError as e:
            logger.error(f"Error retrieving reviews by status: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error in get_by_status: {e}")
            return []
    
    def get_all_reviews(self) -> List[ScoreReviewNode]:
        """
        Lấy tất cả các đơn phúc khảo.
        
        Returns:
            Danh sách tất cả các ScoreReviewNode
        """
        query = """
        MATCH (r:ScoreReview)
        RETURN r
        """
        
        try:
            with self.driver.session() as session:
                result = session.execute_read(
                    lambda tx: tx.run(query).data()
                )
                reviews = [ScoreReviewNode.from_record(record) for record in result]
                logger.info(f"Retrieved {len(reviews)} score reviews in total")
                return reviews
        except Neo4jError as e:
            logger.error(f"Error retrieving all reviews: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error in get_all_reviews: {e}")
            return [] 