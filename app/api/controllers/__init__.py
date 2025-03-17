"""
Controllers initialization module.

This module imports all API routers to make them available for inclusion in main.py.
Each router handles a specific domain of endpoints such as candidates, exams, schools, etc.
"""

# Import all routers
from app.api.controllers.candidate_router import router as candidate_router
from app.api.controllers.admin_router import router as admin_router
from app.api.controllers.health_router import router as health_router
from app.api.controllers.management_unit_router import router as management_unit_router
from app.api.controllers.school_router import router as school_router
from app.api.controllers.major_router import router as major_router
from app.api.controllers.subject_router import router as subject_router
from app.api.controllers.exam_type_router import router as exam_type_router
from app.api.controllers.school_major_router import router as school_major_router
from app.api.controllers.exam_router import router as exam_router
from app.api.controllers.exam_location_router import router as exam_location_router
from app.api.controllers.exam_room_router import router as exam_room_router
from app.api.controllers.exam_location_mapping_router import router as exam_location_mapping_router
from app.api.controllers.exam_subject_router import router as exam_subject_router
from app.api.controllers.exam_schedule_router import router as exam_schedule_router
from app.api.controllers.candidate_exam_router import router as candidate_exam_router
from app.api.controllers.candidate_credential_router import router as candidate_credential_router
from app.api.controllers.exam_score_router import router as exam_score_router
from app.api.controllers.score_review_router import router as score_review_router
from app.api.controllers.exam_score_history_router import router as exam_score_history_router
from app.api.controllers.certificate_router import router as certificate_router
from app.api.controllers.exam_attempt_history_router import router as exam_attempt_history_router
from app.api.controllers.degree_router import router as degree_router
from app.api.controllers.education_history_router import router as education_history_router
from app.api.controllers.education_level_router import router as education_level_router
from app.api.controllers.recognition_router import router as recognition_router
from app.api.controllers.award_router import router as award_router
from app.api.controllers.achievement_router import router as achievement_router

# Special imports
from app.api.controllers.admin_auth import router as admin_auth_router

# Export all routers
__all__ = [
    'candidate_router',
    'admin_router',
    'admin_auth_router',
    'health_router',
    'management_unit_router',
    'school_router',
    'major_router',
    'subject_router',
    'exam_type_router',
    'school_major_router',
    'exam_router',
    'exam_location_router',
    'exam_room_router',
    'exam_location_mapping_router',
    'exam_subject_router',
    'exam_schedule_router',
    'candidate_exam_router',
    'candidate_credential_router',
    'exam_score_router',
    'score_review_router',
    'exam_score_history_router',
    'certificate_router',
    'exam_attempt_history_router',
    'degree_router',
    'education_history_router',
    'education_level_router',
    'recognition_router',
    'award_router',
    'achievement_router'
]