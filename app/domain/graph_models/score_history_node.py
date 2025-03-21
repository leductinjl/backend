"""
Score History Node model.

This module defines the ScoreHistoryNode class for representing ScoreHistory entities in the Neo4j graph.
"""

from datetime import datetime
from typing import Optional, Dict, Any

class ScoreHistoryNode:
    """
    Model for ScoreHistory node in Neo4j Knowledge Graph.
    
    Đại diện cho lịch sử điểm của thí sinh trong knowledge graph.
    """
    
    def __init__(
        self, 
        history_id, 
        history_name=None,
        score_id=None,
        candidate_id=None,
        subject_id=None,
        exam_id=None,
        old_value=None,
        new_value=None,
        change_date=None,
        change_type=None,
        changed_by=None,
        reason=None,
        additional_info=None
    ):
        # Thuộc tính định danh - bắt buộc
        self.history_id = history_id
        self.history_name = history_name or f"History {history_id}"
        self.name = self.history_name  # Thêm thuộc tính 'name' cho nhất quán với các node khác
        
        # Thuộc tính quan hệ - tùy chọn
        self.score_id = score_id
        self.candidate_id = candidate_id
        self.subject_id = subject_id
        self.exam_id = exam_id
        
        # Thuộc tính bổ sung - tùy chọn
        self.old_value = old_value
        self.new_value = new_value
        self.change_date = change_date
        self.change_type = change_type
        self.changed_by = changed_by
        self.reason = reason
        self.additional_info = additional_info
        
    @staticmethod
    def create_query():
        """
        Tạo Cypher query để tạo hoặc cập nhật node ScoreHistory.
        
        Query này tuân theo định nghĩa ontology, bao gồm thiết lập nhãn Thing
        và các thuộc tính được định nghĩa trong ontology.
        """
        return """
        MERGE (h:ScoreHistory {history_id: $history_id})
        ON CREATE SET
            h:Thing, 
            h.history_name = $history_name,
            h.name = $name,
            h.old_value = $old_value,
            h.new_value = $new_value,
            h.change_date = $change_date,
            h.change_type = $change_type,
            h.changed_by = $changed_by,
            h.reason = $reason,
            h.additional_info = $additional_info,
            h.created_at = datetime()
        ON MATCH SET
            h.history_name = $history_name,
            h.name = $name,
            h.old_value = $old_value,
            h.new_value = $new_value,
            h.change_date = $change_date,
            h.change_type = $change_type,
            h.changed_by = $changed_by,
            h.reason = $reason,
            h.additional_info = $additional_info,
            h.updated_at = datetime()
        RETURN h
        """
    
    def create_relationships_query(self):
        """
        Tạo Cypher query để thiết lập các mối quan hệ của ScoreHistory.
        
        Returns:
            Query tạo quan hệ với các node khác
        """
        return """
        // Tạo quan hệ với Score nếu có
        OPTIONAL MATCH (s:Score {score_id: $score_id})
        WITH s
        WHERE s IS NOT NULL
        MATCH (h:ScoreHistory {history_id: $history_id})
        MERGE (h)-[:HISTORY_OF]->(s)
        
        // Tạo quan hệ với Candidate nếu có
        WITH h
        OPTIONAL MATCH (c:Candidate {candidate_id: $candidate_id})
        WITH h, c
        WHERE c IS NOT NULL
        MERGE (h)-[:FOR_CANDIDATE]->(c)
        
        // Tạo quan hệ với Subject nếu có
        WITH h
        OPTIONAL MATCH (s:Subject {subject_id: $subject_id})
        WITH h, s
        WHERE s IS NOT NULL
        MERGE (h)-[:FOR_SUBJECT]->(s)
        
        // Tạo quan hệ với Exam nếu có
        WITH h
        OPTIONAL MATCH (e:Exam {exam_id: $exam_id})
        WITH h, e
        WHERE e IS NOT NULL
        MERGE (h)-[:IN_EXAM]->(e)
        """
    
    def to_dict(self):
        """
        Chuyển đổi thành dictionary để sử dụng trong Neo4j query.
        """
        result = {
            "history_id": self.history_id,
            "history_name": self.history_name,
            "name": self.name,
            "score_id": self.score_id,
            "candidate_id": self.candidate_id,
            "subject_id": self.subject_id,
            "exam_id": self.exam_id,
            "old_value": self.old_value,
            "new_value": self.new_value,
            "change_date": self.change_date,
            "change_type": self.change_type,
            "changed_by": self.changed_by,
            "reason": self.reason,
            "additional_info": self.additional_info
        }
        
        # Chuyển đổi các đối tượng datetime sang chuỗi nếu cần
        if isinstance(self.change_date, datetime):
            result["change_date"] = self.change_date.isoformat()
            
        return result
    
    @classmethod
    def from_sql_model(cls, history_model):
        """
        Tạo đối tượng ScoreHistoryNode từ SQLAlchemy ScoreHistory model.
        
        Args:
            history_model: SQLAlchemy ScoreHistory instance
            
        Returns:
            ScoreHistoryNode instance
        """
        return cls(
            history_id=history_model.history_id,
            history_name=getattr(history_model, 'history_name', f"History {history_model.history_id}"),
            score_id=getattr(history_model, 'score_id', None),
            candidate_id=getattr(history_model, 'candidate_id', None),
            subject_id=getattr(history_model, 'subject_id', None),
            exam_id=getattr(history_model, 'exam_id', None),
            old_value=getattr(history_model, 'old_value', None),
            new_value=getattr(history_model, 'new_value', None),
            change_date=getattr(history_model, 'change_date', None),
            change_type=getattr(history_model, 'change_type', None),
            changed_by=getattr(history_model, 'changed_by', None),
            reason=getattr(history_model, 'reason', None),
            additional_info=getattr(history_model, 'additional_info', None)
        )
        
    @staticmethod
    def from_record(record: Dict[str, Any]) -> 'ScoreHistoryNode':
        """
        Tạo đối tượng ScoreHistoryNode từ Neo4j record.
        
        Args:
            record: Neo4j record chứa node ScoreHistory
            
        Returns:
            ScoreHistoryNode instance
        """
        node = record['h']  # 'h' là alias cho history trong cypher query
        
        # Chuyển đổi chuỗi datetime sang đối tượng datetime nếu cần
        change_date = node.get('change_date')
        if isinstance(change_date, str):
            try:
                change_date = datetime.fromisoformat(change_date)
            except ValueError:
                pass
        
        return ScoreHistoryNode(
            history_id=node['history_id'],
            history_name=node.get('history_name', f"History {node['history_id']}"),
            old_value=node.get('old_value'),
            new_value=node.get('new_value'),
            change_date=change_date,
            change_type=node.get('change_type'),
            changed_by=node.get('changed_by'),
            reason=node.get('reason'),
            additional_info=node.get('additional_info')
        )
    
    def __repr__(self):
        return f"<ScoreHistoryNode(history_id='{self.history_id}', history_name='{self.history_name}')>" 