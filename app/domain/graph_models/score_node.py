"""
Score Node model.

This module defines the ScoreNode class for representing Score entities in the Neo4j graph.
"""

class ScoreNode:
    """
    Model for Score node in Neo4j Knowledge Graph.
    
    Đại diện cho điểm thi trong knowledge graph.
    """
    
    def __init__(
        self, 
        score_id,
        candidate_id=None,
        exam_subject_id=None,
        score_value=None,
        status=None,
        verified=None,
        submitted_at=None,
        verified_at=None
    ):
        # Thuộc tính định danh - bắt buộc
        self.score_id = score_id
        
        # Thuộc tính quan hệ - tùy chọn
        self.candidate_id = candidate_id
        self.exam_subject_id = exam_subject_id
        
        # Thuộc tính dữ liệu - tùy chọn
        self.score_value = score_value
        self.status = status
        self.verified = verified
        self.submitted_at = submitted_at
        self.verified_at = verified_at
        
    @staticmethod
    def create_query():
        """
        Tạo Cypher query để tạo hoặc cập nhật node Score.
        
        Query này tuân theo định nghĩa ontology, bao gồm thiết lập nhãn Thing
        và các thuộc tính được định nghĩa trong ontology.
        """
        return """
        MERGE (s:Score {score_id: $score_id})
        ON CREATE SET
            s:Thing, 
            s.score_value = $score_value,
            s.status = $status,
            s.verified = $verified,
            s.submitted_at = $submitted_at,
            s.verified_at = $verified_at,
            s.created_at = datetime()
        ON MATCH SET
            s.score_value = $score_value,
            s.status = $status,
            s.verified = $verified,
            s.submitted_at = $submitted_at,
            s.verified_at = $verified_at,
            s.updated_at = datetime()
        RETURN s
        """
    
    def create_relationships_query(self):
        """
        Tạo Cypher query để thiết lập các mối quan hệ của Score.
        """
        return """
        // Thiết lập quan hệ với Candidate
        MATCH (s:Score {score_id: $score_id})
        OPTIONAL MATCH (c:Candidate {candidate_id: $candidate_id})
        WITH s, c
        WHERE c IS NOT NULL
        MERGE (c)-[:HAS_SCORE]->(s)
        
        // Thiết lập quan hệ với ExamSubject
        WITH s
        MATCH (es:ExamSubject {exam_subject_id: $exam_subject_id})
        MERGE (s)-[:FOR_SUBJECT]->(es)
        """
    
    def to_dict(self):
        """
        Chuyển đổi thành dictionary để sử dụng trong Neo4j query.
        """
        return {
            "score_id": self.score_id,
            "candidate_id": self.candidate_id,
            "exam_subject_id": self.exam_subject_id,
            "score_value": self.score_value,
            "status": self.status,
            "verified": self.verified,
            "submitted_at": self.submitted_at,
            "verified_at": self.verified_at
        }
    
    @classmethod
    def from_sql_model(cls, score_model):
        """
        Tạo đối tượng ScoreNode từ SQLAlchemy Score model.
        
        Args:
            score_model: SQLAlchemy Score instance hoặc dictionary
            
        Returns:
            ScoreNode instance
        """
        if isinstance(score_model, dict):
            # Trường hợp score_model là dictionary
            return cls(
                score_id=score_model.get('exam_score_id'),
                candidate_id=score_model.get('candidate_id'),
                exam_subject_id=score_model.get('exam_subject_id'),
                score_value=score_model.get('score_value'),
                status=score_model.get('status'),
                verified=score_model.get('verified'),
                submitted_at=score_model.get('submitted_at'),
                verified_at=score_model.get('verified_at')
            )
        else:
            # Trường hợp score_model là SQLAlchemy model
            return cls(
                score_id=getattr(score_model, 'exam_score_id', None),
                candidate_id=getattr(score_model, 'candidate_id', None),
                exam_subject_id=getattr(score_model, 'exam_subject_id', None),
                score_value=getattr(score_model, 'score_value', None),
                status=getattr(score_model, 'status', None),
                verified=getattr(score_model, 'verified', None),
                submitted_at=getattr(score_model, 'submitted_at', None),
                verified_at=getattr(score_model, 'verified_at', None)
            )
    
    @staticmethod
    def from_record(record):
        """
        Tạo đối tượng ScoreNode từ Neo4j record.
        
        Args:
            record: Neo4j record chứa node Score
            
        Returns:
            ScoreNode instance
        """
        node = record['s']  # 's' là alias cho score trong cypher query
        return ScoreNode(
            score_id=node['score_id'],
            score_value=node.get('score_value'),
            status=node.get('status'),
            verified=node.get('verified'),
            submitted_at=node.get('submitted_at'),
            verified_at=node.get('verified_at')
        )
    
    def __repr__(self):
        return f"<ScoreNode(score_id='{self.score_id}', score_value='{self.score_value}')>" 