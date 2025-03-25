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
        
    async def create_or_update(self, review: Union[Dict, ScoreReviewNode]) -> Optional[ScoreReviewNode]:
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
            # Tạo hoặc cập nhật node
            params = review.to_dict()
            result = await self.driver.execute_query(
                ScoreReviewNode.create_query(),
                params
            )
            
            # Tạo mối quan hệ INSTANCE_OF
            if hasattr(review, 'create_instance_of_relationship_query'):
                instance_query = review.create_instance_of_relationship_query()
                if instance_query:
                    await self.driver.execute_query(
                        instance_query,
                        params
                    )
                    logger.info(f"Created INSTANCE_OF relationship for ScoreReview {review.review_id}")
            
            logger.info(f"Successfully created/updated ScoreReview node: {review.review_id}")
            if result and len(result) > 0:
                return review
            return None
        except Neo4jError as e:
            logger.error(f"Error creating/updating ScoreReview node: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in create_or_update: {e}")
            return None
    
    async def get_by_id(self, review_id: str) -> Optional[ScoreReviewNode]:
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
            result = await self.driver.execute_query(
                query, 
                {"review_id": review_id}
            )
            if result and len(result) > 0:
                return ScoreReviewNode.from_record({"r": result[0][0]})
            return None
        except Neo4jError as e:
            logger.error(f"Error retrieving ScoreReview by ID: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in get_by_id: {e}")
            return None
    
    async def delete(self, review_id: str) -> bool:
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
            result = await self.driver.execute_query(
                query,
                {"review_id": review_id}
            )
            
            deleted = result and len(result) > 0 and result[0][0] > 0
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
    
    async def get_by_candidate(self, candidate_id: str) -> List[ScoreReviewNode]:
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
            result = await self.driver.execute_query(
                query,
                {"candidate_id": candidate_id}
            )
            
            reviews = []
            if result and len(result) > 0:
                for record in result:
                    reviews.append(ScoreReviewNode.from_record({"r": record[0]}))
                    
            logger.info(f"Retrieved {len(reviews)} score reviews for candidate {candidate_id}")
            return reviews
        except Neo4jError as e:
            logger.error(f"Error retrieving reviews by candidate: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error in get_by_candidate: {e}")
            return []
    
    async def get_by_score(self, score_id: str) -> List[ScoreReviewNode]:
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
            result = await self.driver.execute_query(
                query,
                {"score_id": score_id}
            )
            
            reviews = []
            if result and len(result) > 0:
                for record in result:
                    reviews.append(ScoreReviewNode.from_record({"r": record[0]}))
                    
            logger.info(f"Retrieved {len(reviews)} score reviews for score {score_id}")
            return reviews
        except Neo4jError as e:
            logger.error(f"Error retrieving reviews by score: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error in get_by_score: {e}")
            return []
    
    async def get_by_exam(self, exam_id: str) -> List[ScoreReviewNode]:
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
            result = await self.driver.execute_query(
                query,
                {"exam_id": exam_id}
            )
            
            reviews = []
            if result and len(result) > 0:
                for record in result:
                    reviews.append(ScoreReviewNode.from_record({"r": record[0]}))
                    
            logger.info(f"Retrieved {len(reviews)} score reviews for exam {exam_id}")
            return reviews
        except Neo4jError as e:
            logger.error(f"Error retrieving reviews by exam: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error in get_by_exam: {e}")
            return []
    
    async def get_by_subject(self, subject_id: str) -> List[ScoreReviewNode]:
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
            result = await self.driver.execute_query(
                query,
                {"subject_id": subject_id}
            )
            
            reviews = []
            if result and len(result) > 0:
                for record in result:
                    reviews.append(ScoreReviewNode.from_record({"r": record[0]}))
                    
            logger.info(f"Retrieved {len(reviews)} score reviews for subject {subject_id}")
            return reviews
        except Neo4jError as e:
            logger.error(f"Error retrieving reviews by subject: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error in get_by_subject: {e}")
            return []
    
    async def get_by_status(self, status: str) -> List[ScoreReviewNode]:
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
            result = await self.driver.execute_query(
                query,
                {"status": status}
            )
            
            reviews = []
            if result and len(result) > 0:
                for record in result:
                    reviews.append(ScoreReviewNode.from_record({"r": record[0]}))
                    
            logger.info(f"Retrieved {len(reviews)} score reviews with status '{status}'")
            return reviews
        except Neo4jError as e:
            logger.error(f"Error retrieving reviews by status: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error in get_by_status: {e}")
            return []
    
    async def get_all_reviews(self) -> List[ScoreReviewNode]:
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
            result = await self.driver.execute_query(query, {})
            
            reviews = []
            if result and len(result) > 0:
                for record in result:
                    reviews.append(ScoreReviewNode.from_record({"r": record[0]}))
                    
            logger.info(f"Retrieved {len(reviews)} score reviews in total")
            return reviews
        except Neo4jError as e:
            logger.error(f"Error retrieving all reviews: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error in get_all_reviews: {e}")
            return []
    
    async def add_for_score_relationship(self, review_id: str, score_id: str) -> bool:
        """
        Thêm mối quan hệ REVIEWS giữa ScoreReview và Score.
        
        Args:
            review_id: ID của đơn phúc khảo
            score_id: ID của điểm
            
        Returns:
            bool: True nếu thành công, False nếu thất bại
        """
        query = f"""
        MATCH (r:ScoreReview {{review_id: $review_id}})
        MATCH (s:Score {{score_id: $score_id}})
        MERGE (r)-[rel:{REVIEWS_REL}]->(s)
        RETURN rel
        """
        params = {
            "review_id": review_id,
            "score_id": score_id
        }
        
        try:
            result = await self.driver.execute_query(query, params)
            success = result and len(result) > 0
            if success:
                logger.info(f"Created REVIEWS relationship between ScoreReview {review_id} and Score {score_id}")
            return success
        except Exception as e:
            logger.error(f"Error creating REVIEWS relationship: {e}")
            return False
    
    async def add_requested_by_relationship(self, review_id: str, candidate_id: str) -> bool:
        """
        Thêm mối quan hệ REQUESTS_REVIEW giữa Candidate và ScoreReview.
        
        Args:
            review_id: ID của đơn phúc khảo
            candidate_id: ID của thí sinh
            
        Returns:
            bool: True nếu thành công, False nếu thất bại
        """
        query = f"""
        MATCH (c:Candidate {{candidate_id: $candidate_id}})
        MATCH (r:ScoreReview {{review_id: $review_id}})
        MERGE (c)-[rel:{REQUESTS_REVIEW_REL}]->(r)
        RETURN rel
        """
        params = {
            "review_id": review_id,
            "candidate_id": candidate_id
        }
        
        try:
            result = await self.driver.execute_query(query, params)
            success = result and len(result) > 0
            if success:
                logger.info(f"Created REQUESTS_REVIEW relationship between Candidate {candidate_id} and ScoreReview {review_id}")
            return success
        except Exception as e:
            logger.error(f"Error creating REQUESTS_REVIEW relationship: {e}")
            return False
    
    async def add_for_subject_relationship(self, review_id: str, subject_id: str) -> bool:
        """
        Thêm mối quan hệ FOR_SUBJECT giữa ScoreReview và Subject.
        
        Args:
            review_id: ID của đơn phúc khảo
            subject_id: ID của môn học
            
        Returns:
            bool: True nếu thành công, False nếu thất bại
        """
        query = f"""
        MATCH (r:ScoreReview {{review_id: $review_id}})
        MATCH (s:Subject {{subject_id: $subject_id}})
        MERGE (r)-[rel:{FOR_SUBJECT_REL}]->(s)
        RETURN rel
        """
        params = {
            "review_id": review_id,
            "subject_id": subject_id
        }
        
        try:
            result = await self.driver.execute_query(query, params)
            success = result and len(result) > 0
            if success:
                logger.info(f"Created FOR_SUBJECT relationship between ScoreReview {review_id} and Subject {subject_id}")
            return success
        except Exception as e:
            logger.error(f"Error creating FOR_SUBJECT relationship: {e}")
            return False 