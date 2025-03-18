# Importing PostgreSQL SQLAlchemy models
from app.domain.models.candidate import Candidate
from app.domain.models.personal_info import PersonalInfo
from app.domain.models.management_unit import ManagementUnit
from app.domain.models.school import School
from app.domain.models.major import Major
from app.domain.models.school_major import SchoolMajor
from app.domain.models.subject import Subject
from app.domain.models.degree import Degree
from app.domain.models.education_history import EducationHistory
from app.domain.models.education_level import EducationLevel
from app.domain.models.candidate_credential import CandidateCredential
from app.domain.models.exam_type import ExamType
from app.domain.models.exam_location import ExamLocation
from app.domain.models.exam import Exam
from app.domain.models.exam_location_mapping import ExamLocationMapping
from app.domain.models.exam_room import ExamRoom
from app.domain.models.exam_subject import ExamSubject
from app.domain.models.exam_schedule import ExamSchedule
from app.domain.models.candidate_exam import CandidateExam
from app.domain.models.exam_score import ExamScore
from app.domain.models.exam_score_history import ExamScoreHistory
from app.domain.models.score_review import ScoreReview
from app.domain.models.exam_attempt_history import ExamAttemptHistory
from app.domain.models.certificate import Certificate
from app.domain.models.recognition import Recognition
from app.domain.models.award import Award
from app.domain.models.achievement import Achievement
from app.domain.models.user import User 
from app.domain.models.invitation import Invitation

# Add new security models
from app.domain.models.role import Role
from app.domain.models.permission import Permission
from app.domain.models.role_permission import RolePermission
from app.domain.models.security_log import SecurityLog
from app.domain.models.two_factor_backup import TwoFactorBackup