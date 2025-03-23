"""
Exam Node model.

This module defines the ExamNode class for representing Exam entities in the Neo4j graph.
"""

from app.infrastructure.ontology.ontology import RELATIONSHIPS, CLASSES

# Define relationship constants
INSTANCE_OF_REL = RELATIONSHIPS["INSTANCE_OF"]["type"]

class ExamNode:
    """
    Model for Exam node in Neo4j Knowledge Graph
    """
    
    def __init__(self, exam_id, exam_name, exam_type=None, 
                 start_date=None, end_date=None, scope=None):
        self.exam_id = exam_id
        self.exam_name = exam_name
        self.exam_type = exam_type
        self.start_date = start_date
        self.end_date = end_date
        self.scope = scope
        self.name = exam_name  # Thêm thuộc tính name giống với exam_name
        
    @staticmethod
    def create_query():
        """
        Get the Cypher query to create or update an Exam node.
        """
        return """
        MERGE (e:Exam:OntologyInstance {exam_id: $exam_id})
        ON CREATE SET
            e.exam_name = $exam_name,
            e.name = $name,
            e.exam_type = $exam_type,
            e.start_date = $start_date,
            e.end_date = $end_date,
            e.scope = $scope,
            e.created_at = datetime(),
            e.updated_at = datetime()
        ON MATCH SET
            e.exam_name = $exam_name,
            e.name = $name,
            e.exam_type = $exam_type,
            e.start_date = $start_date,
            e.end_date = $end_date,
            e.scope = $scope,
            e.updated_at = datetime()
        RETURN e
        """
    
    def create_instance_of_relationship_query(self):
        """
        Tạo Cypher query để thiết lập mối quan hệ INSTANCE_OF giữa node Exam và class definition.
        
        Returns:
            Query tạo quan hệ INSTANCE_OF
        """
        return f"""
        MATCH (e:Exam:OntologyInstance {{exam_id: $exam_id}})
        MATCH (class:OntologyClass {{id: 'exam-class'}})
        MERGE (e)-[:{INSTANCE_OF_REL}]->(class)
        """
    
    def to_dict(self):
        """
        Convert to dictionary for use in queries.
        """
        return {
            "exam_id": self.exam_id,
            "exam_name": self.exam_name,
            "name": self.name,
            "exam_type": self.exam_type,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "scope": self.scope
        }
        
    @staticmethod
    def from_record(record):
        """
        Create an ExamNode object from a Neo4j record.
        """
        node = record['e']  # 'e' is alias for exam in cypher query
        return ExamNode(
            exam_id=node['exam_id'],
            exam_name=node['exam_name'],
            exam_type=node.get('exam_type'),
            start_date=node.get('start_date'),
            end_date=node.get('end_date'),
            scope=node.get('scope')
        )
    
    @classmethod
    def from_sql_model(cls, sql_model):
        """
        Tạo đối tượng ExamNode từ SQLAlchemy Exam model.
        
        Args:
            sql_model: SQLAlchemy Exam instance
            
        Returns:
            ExamNode instance
        """
        return cls(
            exam_id=getattr(sql_model, 'exam_id', None),
            exam_name=getattr(sql_model, 'exam_name', None),
            exam_type=getattr(sql_model, 'type_id', None),  # Mapping từ type_id trong sql model
            start_date=getattr(sql_model, 'start_date', None),
            end_date=getattr(sql_model, 'end_date', None),
            scope=getattr(sql_model, 'scope', None)
        )
    
    def __repr__(self):
        return f"<ExamNode(exam_id='{self.exam_id}', exam_name='{self.exam_name}', type='{self.exam_type}')>" 