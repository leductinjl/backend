"""
Score Node model.

This module defines the ScoreNode class for representing Score entities in the Neo4j graph.
"""

from app.infrastructure.ontology.ontology import RELATIONSHIPS

# Import specific relationships
INSTANCE_OF_REL = RELATIONSHIPS["INSTANCE_OF"]["type"]
RECEIVES_SCORE_REL = RELATIONSHIPS["RECEIVES_SCORE"]["type"]
FOR_SUBJECT_REL = RELATIONSHIPS["FOR_SUBJECT"]["type"]
IN_EXAM_REL = RELATIONSHIPS["IN_EXAM"]["type"]

class ScoreNode:
    """
    Model for Score node in Neo4j Knowledge Graph.
    
    Đại diện cho điểm thi trong knowledge graph.
    """
    
    def __init__(
        self, 
        score_id,
        candidate_id=None,
        subject_id=None,
        exam_id=None,
        score_value=None,
        status=None,
        graded_by=None,
        graded_at=None,
        score_history=None,
        # Thuộc tính bổ sung cho mối quan hệ RECEIVES_SCORE
        exam_name=None,
        subject_name=None,
        registration_status=None,
        registration_date=None,
        is_required=None,
        exam_date=None,
        name=None
    ):
        # Thuộc tính định danh - bắt buộc
        self.score_id = score_id
        
        # Tên hiển thị cho node
        self.name = name
        if not self.name:
            if score_value is not None and subject_name:
                self.name = f"{subject_name}: {score_value}"
            elif score_value is not None and exam_name:
                self.name = f"{exam_name}: {score_value}"
            else:
                self.name = f"Score {score_id}"
        
        # Thuộc tính quan hệ - tùy chọn
        self.candidate_id = candidate_id
        self.subject_id = subject_id
        self.exam_id = exam_id
        
        # Thuộc tính dữ liệu - tùy chọn
        self.score_value = score_value
        self.status = status
        self.graded_by = graded_by
        self.graded_at = graded_at
        self.score_history = score_history
        
        # Thuộc tính cho mối quan hệ RECEIVES_SCORE
        self.exam_name = exam_name
        self.subject_name = subject_name
        self.registration_status = registration_status
        self.registration_date = registration_date
        self.is_required = is_required
        self.exam_date = exam_date
        
    @staticmethod
    def create_query():
        """
        Tạo Cypher query để tạo hoặc cập nhật node Score.
        
        Query này tuân theo định nghĩa ontology, bao gồm thiết lập nhãn Thing
        và các thuộc tính được định nghĩa trong ontology.
        """
        return """
        MERGE (s:Score:OntologyInstance {score_id: $score_id})
        ON CREATE SET
            s.name = $name,
            s.score_value = $score_value,
            s.status = $status,
            s.graded_by = $graded_by,
            s.graded_at = $graded_at,
            s.score_history = $score_history,
            s.created_at = datetime()
        ON MATCH SET
            s.name = $name,
            s.score_value = $score_value,
            s.status = $status,
            s.graded_by = $graded_by,
            s.graded_at = $graded_at,
            s.score_history = $score_history,
            s.updated_at = datetime()
        RETURN s
        """
    
    def create_instance_of_relationship_query(self):
        """
        Tạo Cypher query để thiết lập mối quan hệ INSTANCE_OF giữa node Score và class definition.
        
        Returns:
            Query tạo quan hệ INSTANCE_OF
        """
        return f"""
        MATCH (s:Score:OntologyInstance {{score_id: $score_id}})
        MATCH (class:OntologyClass {{id: 'score-class'}})
        MERGE (s)-[:{INSTANCE_OF_REL}]->(class)
        """
    
    @staticmethod
    def create_relationships_query():
        """
        Tạo Cypher query để thiết lập các mối quan hệ của Score.
        
        Sử dụng các định nghĩa quan hệ từ ontology.
        """
        return f"""
        // Thiết lập quan hệ với Candidate ({RECEIVES_SCORE_REL})
        MATCH (s:Score {{score_id: $score_id}})
        OPTIONAL MATCH (c:Candidate {{candidate_id: $candidate_id}})
        WITH s, c
        WHERE c IS NOT NULL
        MERGE (c)-[r:{RECEIVES_SCORE_REL} {{
            exam_id: CASE WHEN $exam_id IS NULL THEN '' ELSE $exam_id END,
            exam_name: CASE WHEN $exam_name IS NULL THEN '' ELSE $exam_name END,
            subject_id: CASE WHEN $subject_id IS NULL THEN '' ELSE $subject_id END,
            subject_name: CASE WHEN $subject_name IS NULL THEN '' ELSE $subject_name END,
            registration_status: CASE WHEN $registration_status IS NULL THEN 'REGISTERED' ELSE $registration_status END,
            registration_date: CASE WHEN $registration_date IS NULL THEN '' ELSE $registration_date END,
            is_required: CASE WHEN $is_required IS NULL THEN false ELSE $is_required END,
            exam_date: CASE WHEN $exam_date IS NULL THEN '' ELSE $exam_date END
        }}]->(s)
        
        // Thiết lập quan hệ với Subject
        WITH s
        OPTIONAL MATCH (subj:Subject {{subject_id: $subject_id}})
        WITH s, subj
        WHERE subj IS NOT NULL
        MERGE (s)-[:{FOR_SUBJECT_REL}]->(subj)
        
        // Thiết lập quan hệ với Exam
        WITH s
        OPTIONAL MATCH (e:Exam {{exam_id: $exam_id}})
        WITH s, e
        WHERE e IS NOT NULL
        MERGE (s)-[:{IN_EXAM_REL}]->(e)
        """
    
    def to_dict(self):
        """
        Chuyển đổi thành dictionary để sử dụng trong Neo4j query.
        """
        # Convert decimal.Decimal to float for Neo4j compatibility
        score_value = float(self.score_value) if self.score_value is not None else None
        
        return {
            "score_id": self.score_id,
            "name": self.name,
            "candidate_id": self.candidate_id,
            "subject_id": self.subject_id,
            "exam_id": self.exam_id,
            "score_value": score_value,
            "status": self.status,
            "graded_by": self.graded_by,
            "graded_at": self.graded_at,
            "score_history": self.score_history,
            # Thuộc tính cho mối quan hệ RECEIVES_SCORE
            "exam_name": self.exam_name,
            "subject_name": self.subject_name,
            "registration_status": self.registration_status,
            "registration_date": self.registration_date,
            "is_required": self.is_required,
            "exam_date": self.exam_date
        }
    
    @classmethod
    def from_sql_model(cls, score_model, candidate_exam_subject=None, exam=None, subject=None):
        """
        Tạo đối tượng ScoreNode từ SQLAlchemy Score model.
        
        Args:
            score_model: SQLAlchemy Score instance hoặc dictionary
            candidate_exam_subject: Thông tin về đăng ký môn của thí sinh (tùy chọn)
            exam: Thông tin về kỳ thi (tùy chọn)
            subject: Thông tin về môn thi (tùy chọn)
            
        Returns:
            ScoreNode instance
        """
        if isinstance(score_model, dict):
            # Trường hợp score_model là dictionary
            score_id = score_model.get('exam_score_id')
            score_value = score_model.get('score_value')
            status = score_model.get('status')
            graded_by = score_model.get('graded_by')
            graded_at = score_model.get('graded_at')
            score_history = score_model.get('score_history')
            
            # Tạo tên hiển thị cho node
            name = None
            subject_name = score_model.get('subject_name')
            exam_name = score_model.get('exam_name')
            if score_value is not None and subject_name:
                name = f"{subject_name}: {score_value}"
            elif score_value is not None and exam_name:
                name = f"{exam_name}: {score_value}"
            else:
                name = f"Score {score_id}"
            
        else:
            # Trường hợp score_model là SQLAlchemy model
            score_id = getattr(score_model, 'exam_score_id', None)
            score_value = getattr(score_model, 'score_value', None) or getattr(score_model, 'score', None)
            status = getattr(score_model, 'status', None)
            graded_by = getattr(score_model, 'graded_by', None)
            graded_at = getattr(score_model, 'graded_at', None)
            score_history = getattr(score_model, 'score_history', None)
            
            # Tạo tên hiển thị cho node
            name = f"Score {score_id}"
            if hasattr(score_model, 'subject') and score_model.subject and score_value is not None:
                name = f"{score_model.subject.subject_name}: {score_value}"
            elif hasattr(score_model, 'exam') and score_model.exam and score_value is not None:
                name = f"{score_model.exam.exam_name}: {score_value}"
        
        return cls(
            score_id=score_id,
            score_value=score_value,
            status=status,
            graded_by=graded_by,
            graded_at=graded_at,
            score_history=score_history,
            name=name
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
        score_node = ScoreNode(
            score_id=node['score_id'],
            score_value=node.get('score_value'),
            status=node.get('status'),
            graded_by=node.get('graded_by'),
            graded_at=node.get('graded_at'),
            score_history=node.get('score_history'),
            name=node.get('name', f"Score {node['score_id']}")
        )
        return score_node
    
    def __repr__(self):
        return f"<ScoreNode(score_id='{self.score_id}', score_value='{self.score_value}')>" 