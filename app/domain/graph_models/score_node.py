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
        exam_date=None
    ):
        # Thuộc tính định danh - bắt buộc
        self.score_id = score_id
        
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
            s:Thing, 
            s.score_value = $score_value,
            s.status = $status,
            s.graded_by = $graded_by,
            s.graded_at = $graded_at,
            s.score_history = $score_history,
            s.created_at = datetime()
        ON MATCH SET
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
            exam_id: $exam_id,
            exam_name: $exam_name,
            subject_id: $subject_id,
            subject_name: $subject_name,
            registration_status: $registration_status,
            registration_date: $registration_date,
            is_required: $is_required,
            exam_date: $exam_date
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
        return {
            "score_id": self.score_id,
            "candidate_id": self.candidate_id,
            "subject_id": self.subject_id,
            "exam_id": self.exam_id,
            "score_value": self.score_value,
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
            candidate_id = score_model.get('candidate_id')
            subject_id = score_model.get('subject_id')
            exam_id = score_model.get('exam_id')
            score_value = score_model.get('score_value')
            status = score_model.get('status')
            graded_by = score_model.get('graded_by')
            graded_at = score_model.get('graded_at')
            score_history = score_model.get('score_history')
            
            # Thông tin bổ sung cho mối quan hệ RECEIVES_SCORE
            exam_name = score_model.get('exam_name')
            subject_name = score_model.get('subject_name')
            registration_status = score_model.get('registration_status')
            registration_date = score_model.get('registration_date')
            is_required = score_model.get('is_required')
            exam_date = score_model.get('exam_date')
            
            # Bổ sung từ các tham số tùy chọn
            if exam:
                exam_id = exam.get('exam_id') if isinstance(exam, dict) else getattr(exam, 'exam_id', exam_id)
                exam_name = exam.get('exam_name') if isinstance(exam, dict) else getattr(exam, 'exam_name', exam_name)
            
            if subject:
                subject_id = subject.get('subject_id') if isinstance(subject, dict) else getattr(subject, 'subject_id', subject_id)
                subject_name = subject.get('subject_name') if isinstance(subject, dict) else getattr(subject, 'subject_name', subject_name)
            
            if candidate_exam_subject:
                registration_status = candidate_exam_subject.get('status') if isinstance(candidate_exam_subject, dict) else getattr(candidate_exam_subject, 'status', registration_status)
                registration_date = candidate_exam_subject.get('registration_date') if isinstance(candidate_exam_subject, dict) else getattr(candidate_exam_subject, 'registration_date', registration_date)
                is_required = candidate_exam_subject.get('is_required') if isinstance(candidate_exam_subject, dict) else getattr(candidate_exam_subject, 'is_required', is_required)
                exam_date = candidate_exam_subject.get('exam_date') if isinstance(candidate_exam_subject, dict) else getattr(candidate_exam_subject, 'exam_date', exam_date)
            
        else:
            # Trường hợp score_model là SQLAlchemy model
            score_id = getattr(score_model, 'exam_score_id', None)
            candidate_id = getattr(score_model, 'candidate_id', None)
            subject_id = getattr(score_model, 'subject_id', None)
            exam_id = getattr(score_model, 'exam_id', None)
            score_value = getattr(score_model, 'score_value', None)
            status = getattr(score_model, 'status', None)
            graded_by = getattr(score_model, 'graded_by', None)
            graded_at = getattr(score_model, 'graded_at', None)
            score_history = getattr(score_model, 'score_history', None)
            
            # Thông tin bổ sung cho mối quan hệ RECEIVES_SCORE
            exam_name = getattr(score_model, 'exam_name', None)
            subject_name = getattr(score_model, 'subject_name', None)
            registration_status = getattr(score_model, 'registration_status', None)
            registration_date = getattr(score_model, 'registration_date', None)
            is_required = getattr(score_model, 'is_required', None)
            exam_date = getattr(score_model, 'exam_date', None)
            
            # Bổ sung từ các tham số tùy chọn
            if exam:
                exam_id = exam.exam_id if exam_id is None else exam_id
                exam_name = exam.exam_name if exam_name is None else exam_name
            
            if subject:
                subject_id = subject.subject_id if subject_id is None else subject_id
                subject_name = subject.subject_name if subject_name is None else subject_name
            
            if candidate_exam_subject:
                registration_status = candidate_exam_subject.status if registration_status is None else registration_status
                registration_date = candidate_exam_subject.registration_date if registration_date is None else registration_date
                is_required = candidate_exam_subject.is_required if is_required is None else is_required
                exam_date = candidate_exam_subject.exam_date if exam_date is None else exam_date
        
        return cls(
            score_id=score_id,
            candidate_id=candidate_id,
            subject_id=subject_id,
            exam_id=exam_id,
            score_value=score_value,
            status=status,
            graded_by=graded_by,
            graded_at=graded_at,
            score_history=score_history,
            exam_name=exam_name,
            subject_name=subject_name,
            registration_status=registration_status,
            registration_date=registration_date,
            is_required=is_required,
            exam_date=exam_date
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
            graded_by=node.get('graded_by'),
            graded_at=node.get('graded_at'),
            score_history=node.get('score_history')
        )
    
    def __repr__(self):
        return f"<ScoreNode(score_id='{self.score_id}', score_value='{self.score_value}')>" 