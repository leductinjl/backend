"""
Graph models package.

This package contains the graph models for the knowledge graph.
"""

from app.domain.graph_models.candidate_node import CandidateNode
from app.domain.graph_models.school_node import SchoolNode
from app.domain.graph_models.exam_node import ExamNode
from app.domain.graph_models.subject_node import SubjectNode
from app.domain.graph_models.major_node import MajorNode
from app.domain.graph_models.certificate_node import CertificateNode
from app.domain.graph_models.exam_location_node import ExamLocationNode
from app.domain.graph_models.exam_room_node import ExamRoomNode
from app.domain.graph_models.exam_schedule_node import ExamScheduleNode
from app.domain.graph_models.score_node import ScoreNode
from app.domain.graph_models.score_review_node import ScoreReviewNode
from app.domain.graph_models.award_node import AwardNode
from app.domain.graph_models.recognition_node import RecognitionNode
from app.domain.graph_models.achievement_node import AchievementNode
from app.domain.graph_models.degree_node import DegreeNode
from app.domain.graph_models.credential_node import CredentialNode
from app.domain.graph_models.management_unit_node import ManagementUnitNode

# Importing relationships from ontology
from app.infrastructure.ontology.ontology import RELATIONSHIPS

# Extract specific relationships
STUDIES_AT = RELATIONSHIPS["STUDIES_AT"]
ATTENDS_EXAM = RELATIONSHIPS["ATTENDS_EXAM"]
RECEIVES_SCORE = RELATIONSHIPS["RECEIVES_SCORE"]
EARNS_CERTIFICATE = RELATIONSHIPS["EARNS_CERTIFICATE"] 
EARNS_AWARD = RELATIONSHIPS["EARNS_AWARD"]
BELONGS_TO = RELATIONSHIPS.get("BELONGS_TO", {})
OFFERS_MAJOR = RELATIONSHIPS["OFFERS_MAJOR"]
TEACHES_SUBJECT = RELATIONSHIPS["TEACHES_SUBJECT"]
ORGANIZES_EXAM = RELATIONSHIPS.get("ORGANIZES_EXAM", {})
INCLUDES_SUBJECT = RELATIONSHIPS["INCLUDES_SUBJECT"]
HELD_AT = RELATIONSHIPS["HELD_AT"]
REQUESTS_REVIEW = RELATIONSHIPS["REQUESTS_REVIEW"]
HOLDS_DEGREE = RELATIONSHIPS["HOLDS_DEGREE"]
HAS_EXAM_SCHEDULE = RELATIONSHIPS["HAS_EXAM_SCHEDULE"]
ACHIEVES = RELATIONSHIPS["ACHIEVES"]
RECEIVES_RECOGNITION = RELATIONSHIPS["RECEIVES_RECOGNITION"]
PROVIDES_CREDENTIAL = RELATIONSHIPS["PROVIDES_CREDENTIAL"]
STUDIES_MAJOR = RELATIONSHIPS["STUDIES_MAJOR"]
FOR_SUBJECT = RELATIONSHIPS["FOR_SUBJECT"]
IN_EXAM = RELATIONSHIPS["IN_EXAM"]
FOLLOWS_SCHEDULE = RELATIONSHIPS["FOLLOWS_SCHEDULE"]
LOCATED_IN = RELATIONSHIPS["LOCATED_IN"]
RELATED_TO_EXAM = RELATIONSHIPS["RELATED_TO_EXAM"]

__all__ = [
    'CandidateNode',
    'SchoolNode',
    'ExamNode',
    'SubjectNode',
    'MajorNode',
    'CertificateNode',
    'ExamLocationNode',
    'ExamRoomNode',
    'ExamScheduleNode',
    'ScoreNode',
    'ScoreReviewNode',
    'AwardNode',
    'RecognitionNode',
    'AchievementNode',
    'DegreeNode',
    'CredentialNode',
    'ManagementUnitNode',
    # Relationships
    'STUDIES_AT',
    'ATTENDS_EXAM',
    'RECEIVES_SCORE',
    'EARNS_CERTIFICATE',
    'EARNS_AWARD',
    'BELONGS_TO',
    'OFFERS_MAJOR',
    'TEACHES_SUBJECT',
    'ORGANIZES_EXAM',
    'INCLUDES_SUBJECT',
    'HELD_AT',
    'REQUESTS_REVIEW',
    'HOLDS_DEGREE',
    'HAS_EXAM_SCHEDULE',
    'ACHIEVES',
    'RECEIVES_RECOGNITION',
    'PROVIDES_CREDENTIAL',
    'STUDIES_MAJOR',
    'FOR_SUBJECT',
    'IN_EXAM',
    'FOLLOWS_SCHEDULE',
    'LOCATED_IN',
    'RELATED_TO_EXAM'
] 