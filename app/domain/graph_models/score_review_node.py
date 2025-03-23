"""
Score Review Node model.

This module defines the ScoreReviewNode class for representing ScoreReview entities in the Neo4j graph.
"""

from datetime import datetime
from typing import Optional, Dict, Any

from app.infrastructure.ontology.ontology import RELATIONSHIPS

# Import specific relationships
INSTANCE_OF_REL = RELATIONSHIPS["INSTANCE_OF"]["type"]
REQUESTS_REVIEW_REL = RELATIONSHIPS["REQUESTS_REVIEW"]["type"]
FOR_SUBJECT_REL = RELATIONSHIPS["FOR_SUBJECT"]["type"]
IN_EXAM_REL = RELATIONSHIPS["IN_EXAM"]["type"]
REVIEWS_REL = RELATIONSHIPS["REVIEWS"]["type"]

class ScoreReviewNode:
    """
    Model for ScoreReview node in Neo4j Knowledge Graph.
    
    Đại diện cho các đơn phúc khảo điểm trong knowledge graph.
    """
    
    def __init__(
        self, 
        review_id, 
        review_name=None,
        score_id=None,
        candidate_id=None,
        subject_id=None,
        exam_id=None,
        status=None,
        request_date=None,
        resolution_date=None,
        old_score=None,
        new_score=None,
        reviewer=None,
        reason=None,
        additional_info=None
    ):
        # Thuộc tính định danh - bắt buộc
        self.review_id = review_id
        self.review_name = review_name or f"Review {review_id}"
        self.name = self.review_name  # Thêm thuộc tính 'name' cho nhất quán với các node khác
        
        # Thuộc tính quan hệ - tùy chọn
        self.score_id = score_id
        self.candidate_id = candidate_id
        self.subject_id = subject_id
        self.exam_id = exam_id
        
        # Thuộc tính bổ sung - tùy chọn
        self.status = status
        self.request_date = request_date
        self.resolution_date = resolution_date
        self.old_score = old_score
        self.new_score = new_score
        self.reviewer = reviewer
        self.reason = reason
        self.additional_info = additional_info
        
    @staticmethod
    def create_query():
        """
        Tạo Cypher query để tạo hoặc cập nhật node ScoreReview.
        
        Query này tuân theo định nghĩa ontology, bao gồm thiết lập nhãn Thing
        và các thuộc tính được định nghĩa trong ontology.
        """
        return """
        MERGE (r:ScoreReview:OntologyInstance {review_id: $review_id})
        ON CREATE SET
            r.review_name = $review_name,
            r.name = $name,
            r.status = $status,
            r.request_date = $request_date,
            r.resolution_date = $resolution_date,
            r.old_score = $old_score,
            r.new_score = $new_score,
            r.reviewer = $reviewer,
            r.reason = $reason,
            r.additional_info = $additional_info,
            r.created_at = datetime()
        ON MATCH SET
            r.review_name = $review_name,
            r.name = $name,
            r.status = $status,
            r.request_date = $request_date,
            r.resolution_date = $resolution_date,
            r.old_score = $old_score,
            r.new_score = $new_score,
            r.reviewer = $reviewer,
            r.reason = $reason,
            r.additional_info = $additional_info,
            r.updated_at = datetime()
        RETURN r
        """
    
    def create_instance_of_relationship_query(self):
        """
        Tạo Cypher query để thiết lập mối quan hệ INSTANCE_OF giữa node ScoreReview và class definition.
        
        Returns:
            Query tạo quan hệ INSTANCE_OF
        """
        return f"""
        MATCH (r:ScoreReview:OntologyInstance {{review_id: $review_id}})
        MATCH (class:OntologyClass {{id: 'scorereview-class'}})
        MERGE (r)-[:{INSTANCE_OF_REL}]->(class)
        """
    
    def create_relationships_query(self):
        """
        Tạo Cypher query để thiết lập các mối quan hệ của ScoreReview.
        
        Returns:
            Query tạo quan hệ với các node khác
        """
        return f"""
        // Tạo quan hệ với Score nếu có
        MATCH (r:ScoreReview {{review_id: $review_id}})
        OPTIONAL MATCH (s:Score {{score_id: $score_id}})
        WITH r, s
        WHERE s IS NOT NULL
        MERGE (r)-[:{REVIEWS_REL} {{
            review_date: CASE WHEN $request_date IS NULL THEN '' ELSE $request_date END,
            review_status: CASE WHEN $status IS NULL THEN 'PENDING' ELSE $status END,
            reviewer: CASE WHEN $reviewer IS NULL THEN '' ELSE $reviewer END
        }}]->(s)
        
        // Tạo quan hệ với Candidate nếu có
        WITH r
        OPTIONAL MATCH (c:Candidate {{candidate_id: $candidate_id}})
        WITH r, c
        WHERE c IS NOT NULL
        MERGE (c)-[:{REQUESTS_REVIEW_REL}]->(r)
        
        // Tạo quan hệ với Subject nếu có
        WITH r
        OPTIONAL MATCH (s:Subject {{subject_id: $subject_id}})
        WITH r, s
        WHERE s IS NOT NULL
        MERGE (r)-[:{FOR_SUBJECT_REL}]->(s)
        
        // Tạo quan hệ với Exam nếu có
        WITH r
        OPTIONAL MATCH (e:Exam {{exam_id: $exam_id}})
        WITH r, e
        WHERE e IS NOT NULL
        MERGE (r)-[:{IN_EXAM_REL}]->(e)
        """
    
    def to_dict(self):
        """
        Chuyển đổi thành dictionary để sử dụng trong Neo4j query.
        """
        # Convert Decimal values to float for Neo4j compatibility
        old_score = float(self.old_score) if self.old_score is not None else None
        new_score = float(self.new_score) if self.new_score is not None else None
        
        result = {
            "review_id": self.review_id,
            "review_name": self.review_name,
            "name": self.name,
            "score_id": self.score_id,
            "candidate_id": self.candidate_id,
            "subject_id": self.subject_id,
            "exam_id": self.exam_id,
            "status": self.status,
            "request_date": self.request_date,
            "resolution_date": self.resolution_date,
            "old_score": old_score,
            "new_score": new_score,
            "reviewer": self.reviewer,
            "reason": self.reason,
            "additional_info": self.additional_info
        }
        
        # Chuyển đổi các đối tượng datetime sang chuỗi nếu cần
        if isinstance(self.request_date, datetime):
            result["request_date"] = self.request_date.isoformat()
            
        if isinstance(self.resolution_date, datetime):
            result["resolution_date"] = self.resolution_date.isoformat()
            
        return result
    
    @classmethod
    def from_sql_model(cls, review_model):
        """
        Tạo đối tượng ScoreReviewNode từ SQLAlchemy ScoreReview model.
        
        Args:
            review_model: SQLAlchemy ScoreReview instance
            
        Returns:
            ScoreReviewNode instance
        """
        return cls(
            review_id=review_model.review_id,
            review_name=getattr(review_model, 'review_name', f"Review {review_model.review_id}"),
            score_id=getattr(review_model, 'score_id', None),
            candidate_id=getattr(review_model, 'candidate_id', None),
            subject_id=getattr(review_model, 'subject_id', None),
            exam_id=getattr(review_model, 'exam_id', None),
            status=getattr(review_model, 'status', None),
            request_date=getattr(review_model, 'request_date', None),
            resolution_date=getattr(review_model, 'resolution_date', None),
            old_score=getattr(review_model, 'old_score', None),
            new_score=getattr(review_model, 'new_score', None),
            reviewer=getattr(review_model, 'reviewer', None),
            reason=getattr(review_model, 'reason', None),
            additional_info=getattr(review_model, 'additional_info', None)
        )
        
    @staticmethod
    def from_record(record: Dict[str, Any]) -> 'ScoreReviewNode':
        """
        Tạo đối tượng ScoreReviewNode từ Neo4j record.
        
        Args:
            record: Neo4j record chứa node ScoreReview
            
        Returns:
            ScoreReviewNode instance
        """
        node = record['r']  # 'r' là alias cho review trong cypher query
        
        # Chuyển đổi chuỗi datetime sang đối tượng datetime nếu cần
        request_date = node.get('request_date')
        if isinstance(request_date, str):
            try:
                request_date = datetime.fromisoformat(request_date)
            except ValueError:
                pass
                
        resolution_date = node.get('resolution_date')
        if isinstance(resolution_date, str):
            try:
                resolution_date = datetime.fromisoformat(resolution_date)
            except ValueError:
                pass
        
        return ScoreReviewNode(
            review_id=node['review_id'],
            review_name=node.get('review_name', f"Review {node['review_id']}"),
            status=node.get('status'),
            request_date=request_date,
            resolution_date=resolution_date,
            old_score=node.get('old_score'),
            new_score=node.get('new_score'),
            reviewer=node.get('reviewer'),
            reason=node.get('reason'),
            additional_info=node.get('additional_info')
        )
    
    def __repr__(self):
        return f"<ScoreReviewNode(review_id='{self.review_id}', review_name='{self.review_name}')>" 