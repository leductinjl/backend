"""
Repository Factory module.

This module provides a factory class for creating and managing repository instances.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.candidate_repository import CandidateRepository
from app.repositories.school_repository import SchoolRepository
from app.repositories.exam_repository import ExamRepository
from app.repositories.subject_repository import SubjectRepository
from app.repositories.exam_score_repository import ExamScoreRepository
from app.repositories.major_repository import MajorRepository
from app.repositories.award_repository import AwardRepository
from app.repositories.certificate_repository import CertificateRepository
from app.repositories.achievement_repository import AchievementRepository
from app.repositories.recognition_repository import RecognitionRepository
from app.repositories.degree_repository import DegreeRepository
from app.repositories.candidate_credential_repository import CandidateCredentialRepository
from app.repositories.exam_score_history_repository import ExamScoreHistoryRepository
from app.repositories.management_unit_repository import ManagementUnitRepository

class RepositoryFactory:
    """
    Factory for creating and managing repository instances.
    
    This class provides a centralized way to access repositories,
    ensuring that they share the same database session.
    """
    
    def __init__(self, db_session: AsyncSession):
        """
        Initialize the factory with a database session.
        
        Args:
            db_session: SQLAlchemy AsyncSession object
        """
        self.db_session = db_session
        self._repositories = {}
    
    def get_candidate_repository(self) -> CandidateRepository:
        """Get or create a CandidateRepository instance."""
        if 'candidate' not in self._repositories:
            self._repositories['candidate'] = CandidateRepository(self.db_session)
        return self._repositories['candidate']
    
    def get_school_repository(self) -> SchoolRepository:
        """Get or create a SchoolRepository instance."""
        if 'school' not in self._repositories:
            self._repositories['school'] = SchoolRepository(self.db_session)
        return self._repositories['school']
    
    def get_exam_repository(self) -> ExamRepository:
        """Get or create an ExamRepository instance."""
        if 'exam' not in self._repositories:
            self._repositories['exam'] = ExamRepository(self.db_session)
        return self._repositories['exam']
    
    def get_subject_repository(self) -> SubjectRepository:
        """Get or create a SubjectRepository instance."""
        if 'subject' not in self._repositories:
            self._repositories['subject'] = SubjectRepository(self.db_session)
        return self._repositories['subject']
    
    def get_score_repository(self) -> ExamScoreRepository:
        """Get or create an ExamScoreRepository instance."""
        if 'score' not in self._repositories:
            self._repositories['score'] = ExamScoreRepository(self.db_session)
        return self._repositories['score']
    
    def get_exam_score_repository(self) -> ExamScoreRepository:
        """Alias for get_score_repository."""
        return self.get_score_repository()
    
    def get_major_repository(self) -> MajorRepository:
        """Get or create a MajorRepository instance."""
        if 'major' not in self._repositories:
            self._repositories['major'] = MajorRepository(self.db_session)
        return self._repositories['major']
    
    def get_award_repository(self) -> AwardRepository:
        """Get or create an AwardRepository instance."""
        if 'award' not in self._repositories:
            self._repositories['award'] = AwardRepository(self.db_session)
        return self._repositories['award']
    
    def get_certificate_repository(self) -> CertificateRepository:
        """Get or create a CertificateRepository instance."""
        if 'certificate' not in self._repositories:
            self._repositories['certificate'] = CertificateRepository(self.db_session)
        return self._repositories['certificate']
    
    def get_achievement_repository(self) -> AchievementRepository:
        """Get or create an AchievementRepository instance."""
        if 'achievement' not in self._repositories:
            self._repositories['achievement'] = AchievementRepository(self.db_session)
        return self._repositories['achievement']
    
    def get_recognition_repository(self) -> RecognitionRepository:
        """Get or create a RecognitionRepository instance."""
        if 'recognition' not in self._repositories:
            self._repositories['recognition'] = RecognitionRepository(self.db_session)
        return self._repositories['recognition']
    
    def get_degree_repository(self) -> DegreeRepository:
        """Get or create a DegreeRepository instance."""
        if 'degree' not in self._repositories:
            self._repositories['degree'] = DegreeRepository(self.db_session)
        return self._repositories['degree']
    
    def get_credential_repository(self) -> CandidateCredentialRepository:
        """Get or create a CandidateCredentialRepository instance."""
        if 'credential' not in self._repositories:
            self._repositories['credential'] = CandidateCredentialRepository(self.db_session)
        return self._repositories['credential']
    
    def get_score_history_repository(self) -> ExamScoreHistoryRepository:
        """Get or create a ScoreHistoryRepository instance."""
        if 'score_history' not in self._repositories:
            self._repositories['score_history'] = ExamScoreHistoryRepository(self.db_session)
        return self._repositories['score_history']
    
    def get_management_unit_repository(self) -> ManagementUnitRepository:
        """Get or create a ManagementUnitRepository instance."""
        if 'management_unit' not in self._repositories:
            self._repositories['management_unit'] = ManagementUnitRepository(self.db_session)
        return self._repositories['management_unit']
    
    def get_exam_location_repository(self):
        """Get or create an ExamLocationRepository instance."""
        if 'exam_location' not in self._repositories:
            # Import here to avoid circular imports
            from app.repositories.exam_location_repository import ExamLocationRepository
            self._repositories['exam_location'] = ExamLocationRepository(self.db_session)
        return self._repositories['exam_location']
    
    def get_exam_room_repository(self):
        """Get or create an ExamRoomRepository instance."""
        if 'exam_room' not in self._repositories:
            # Import here to avoid circular imports
            from app.repositories.exam_room_repository import ExamRoomRepository
            self._repositories['exam_room'] = ExamRoomRepository(self.db_session)
        return self._repositories['exam_room']
    
    def get_exam_schedule_repository(self):
        """Get or create an ExamScheduleRepository instance."""
        if 'exam_schedule' not in self._repositories:
            # Import here to avoid circular imports
            from app.repositories.exam_schedule_repository import ExamScheduleRepository
            self._repositories['exam_schedule'] = ExamScheduleRepository(self.db_session)
        return self._repositories['exam_schedule']
    
    def get_exam_attempt_repository(self):
        """Get or create an ExamAttemptRepository instance."""
        if 'exam_attempt' not in self._repositories:
            # Import here to avoid circular imports
            from app.repositories.exam_attempt_history_repository import ExamAttemptHistoryRepository
            self._repositories['exam_attempt'] = ExamAttemptHistoryRepository(self.db_session)
        return self._repositories['exam_attempt']
    
    def get_score_review_repository(self):
        """Get or create a ScoreReviewRepository instance."""
        if 'score_review' not in self._repositories:
            # Import here to avoid circular imports
            from app.repositories.score_review_repository import ScoreReviewRepository
            self._repositories['score_review'] = ScoreReviewRepository(self.db_session)
        return self._repositories['score_review']
    
    def get_candidate_exam_repository(self):
        """Get or create a CandidateExamRepository instance."""
        if 'candidate_exam' not in self._repositories:
            # Import here to avoid circular imports
            from app.repositories.candidate_exam_repository import CandidateExamRepository
            self._repositories['candidate_exam'] = CandidateExamRepository(self.db_session)
        return self._repositories['candidate_exam']
    
    def get_school_major_repository(self):
        """Get or create a SchoolMajorRepository instance."""
        if 'school_major' not in self._repositories:
            # Import here to avoid circular imports
            from app.repositories.school_major_repository import SchoolMajorRepository
            self._repositories['school_major'] = SchoolMajorRepository(self.db_session)
        return self._repositories['school_major']
    
    def get_candidate_major_repository(self):
        """Get or create a CandidateMajorRepository instance."""
        if 'candidate_major' not in self._repositories:
            # Import here to avoid circular imports
            from app.repositories.candidate_major_repository import CandidateMajorRepository
            self._repositories['candidate_major'] = CandidateMajorRepository(self.db_session)
        return self._repositories['candidate_major']
    
    def get_education_history_repository(self):
        """Get or create an EducationHistoryRepository instance."""
        if 'education_history' not in self._repositories:
            # Import here to avoid circular imports
            from app.repositories.education_history_repository import EducationHistoryRepository
            self._repositories['education_history'] = EducationHistoryRepository(self.db_session)
        return self._repositories['education_history']
    
    def get_exam_subject_repository(self):
        """Get or create an ExamSubjectRepository instance."""
        if 'exam_subject' not in self._repositories:
            # Import here to avoid circular imports
            from app.repositories.exam_subject_repository import ExamSubjectRepository
            self._repositories['exam_subject'] = ExamSubjectRepository(self.db_session)
        return self._repositories['exam_subject']
    
    def get_personal_info_repository(self):
        """Get or create a PersonalInfoRepository instance."""
        if 'personal_info' not in self._repositories:
            # Import here to avoid circular imports
            from app.repositories.personal_info_repository import PersonalInfoRepository
            self._repositories['personal_info'] = PersonalInfoRepository(self.db_session)
        return self._repositories['personal_info']
    
    def get_exam_location_mapping_repository(self):
        """Get or create an ExamLocationMappingRepository instance."""
        if 'exam_location_mapping' not in self._repositories:
            # Import here to avoid circular imports
            from app.repositories.exam_location_mapping_repository import ExamLocationMappingRepository
            self._repositories['exam_location_mapping'] = ExamLocationMappingRepository(self.db_session)
        return self._repositories['exam_location_mapping'] 