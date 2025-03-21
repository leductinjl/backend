"""
Ontology definition module.

This module defines the knowledge graph ontology structure for the candidate information system.
It includes class definitions and relationship types to model the domain knowledge.
"""

# ------------- CLASS DEFINITIONS -------------

# Base class
THING = {
    "label": "Thing",
    "description": "Root class for all entities",
    "properties": {
        "id": "Global identifier for the entity",
        "name": "Name of the entity"
    },
    "create_query": """
    MERGE (t:Thing {id: $id})
    ON CREATE SET
        t.name = $name,
        t.created_at = datetime(),
        t.updated_at = datetime()
    ON MATCH SET
        t.name = $name,
        t.updated_at = datetime()
    RETURN t
    """
}

# Primary entities (all inherit from Thing)
CANDIDATE = {
    "label": "Candidate",
    "parent": "Thing",
    "description": "Student/candidate information",
    "properties": {
        "candidate_id": "Candidate unique identifier",
        "full_name": "Full name of the candidate",
        "birth_date": "Date of birth",
        "id_number": "National ID number",
        "phone_number": "Contact phone number",
        "email": "Email address",
        "address": "Primary address"
    },
    "create_query": """
    MERGE (c:Candidate {candidate_id: $candidate_id})
    ON CREATE SET
        c:Thing,
        c.full_name = $full_name,
        c.birth_date = $birth_date,
        c.id_number = $id_number,
        c.phone_number = $phone_number,
        c.email = $email,
        c.address = $address,
        c.created_at = datetime(),
        c.updated_at = datetime()
    ON MATCH SET
        c.full_name = $full_name,
        c.birth_date = $birth_date,
        c.id_number = $id_number,
        c.phone_number = $phone_number,
        c.email = $email,
        c.address = $address,
        c.updated_at = datetime()
    RETURN c
    """
}

SCHOOL = {
    "label": "School",
    "parent": "Thing",
    "description": "Educational institution",
    "properties": {
        "school_id": "School unique identifier",
        "school_name": "Name of the school",
        "address": "School address"
    },
    "create_query": """
    MERGE (s:School {school_id: $school_id})
    ON CREATE SET
        s:Thing,
        s.school_name = $school_name,
        s.address = $address,
        s.created_at = datetime(),
        s.updated_at = datetime()
    ON MATCH SET
        s.school_name = $school_name,
        s.address = $address,
        s.updated_at = datetime()
    RETURN s
    """
}

MAJOR = {
    "label": "Major",
    "parent": "Thing",
    "description": "Field of study",
    "properties": {
        "major_id": "Major unique identifier",
        "major_name": "Name of the major",
        "description": "Description of the major"
    },
    "create_query": """
    MERGE (m:Major {major_id: $major_id})
    ON CREATE SET
        m:Thing,
        m.major_name = $major_name,
        m.description = $description,
        m.created_at = datetime(),
        m.updated_at = datetime()
    ON MATCH SET
        m.major_name = $major_name,
        m.description = $description,
        m.updated_at = datetime()
    RETURN m
    """
}

SUBJECT = {
    "label": "Subject",
    "parent": "Thing",
    "description": "Academic subject",
    "properties": {
        "subject_id": "Subject unique identifier",
        "subject_name": "Name of the subject",
        "subject_code": "Code of the subject"
    },
    "create_query": """
    MERGE (s:Subject {subject_id: $subject_id})
    ON CREATE SET
        s:Thing,
        s.subject_name = $subject_name,
        s.subject_code = $subject_code,
        s.created_at = datetime(),
        s.updated_at = datetime()
    ON MATCH SET
        s.subject_name = $subject_name,
        s.subject_code = $subject_code,
        s.updated_at = datetime()
    RETURN s
    """
}

EXAM = {
    "label": "Exam",
    "parent": "Thing",
    "description": "Examination event",
    "properties": {
        "exam_id": "Exam unique identifier",
        "exam_name": "Name of the exam",
        "name": "Name of the exam (for consistent naming across entities)",
        "exam_type": "Type of exam",
        "start_date": "Start date",
        "end_date": "End date",
        "scope": "Geographic/administrative scope"
    },
    "create_query": """
    MERGE (e:Exam {exam_id: $exam_id})
    ON CREATE SET
        e:Thing,
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
}

EXAM_LOCATION = {
    "label": "ExamLocation",
    "parent": "Thing",
    "description": "Location where exams are held",
    "properties": {
        "location_id": "Location unique identifier",
        "location_name": "Name of the location",
        "address": "Address of the location",
        "capacity": "Maximum capacity"
    },
    "create_query": """
    MERGE (l:ExamLocation {location_id: $location_id})
    ON CREATE SET
        l:Thing,
        l.location_name = $location_name,
        l.address = $address,
        l.capacity = $capacity,
        l.created_at = datetime(),
        l.updated_at = datetime()
    ON MATCH SET
        l.location_name = $location_name,
        l.address = $address,
        l.capacity = $capacity,
        l.updated_at = datetime()
    RETURN l
    """
}

EXAM_SCHEDULE = {
    "label": "ExamSchedule",
    "parent": "Thing",
    "description": "Schedule for an exam",
    "properties": {
        "schedule_id": "Schedule unique identifier",
        "start_time": "Start time",
        "end_time": "End time",
        "description": "Description of the schedule",
        "status": "Status of the schedule"
    },
    "create_query": """
    MERGE (s:ExamSchedule {schedule_id: $schedule_id})
    ON CREATE SET
        s:Thing,
        s.start_time = $start_time,
        s.end_time = $end_time,
        s.description = $description,
        s.status = $status,
        s.created_at = datetime(),
        s.updated_at = datetime()
    ON MATCH SET
        s.start_time = $start_time,
        s.end_time = $end_time,
        s.description = $description,
        s.status = $status,
        s.updated_at = datetime()
    RETURN s
    """
}

EXAM_ATTEMPT = {
    "label": "ExamAttempt",
    "parent": "Thing",
    "description": "Candidate's attempt at an exam",
    "properties": {
        "attempt_id": "Attempt unique identifier",
        "attempt_number": "Attempt number",
        "registration_number": "Registration number",
        "registration_date": "Registration date",
        "status": "Status of the attempt"
    },
    "create_query": """
    MERGE (a:ExamAttempt {attempt_id: $attempt_id})
    ON CREATE SET
        a:Thing,
        a.attempt_number = $attempt_number,
        a.registration_number = $registration_number,
        a.registration_date = $registration_date,
        a.status = $status,
        a.created_at = datetime(),
        a.updated_at = datetime()
    ON MATCH SET
        a.attempt_number = $attempt_number,
        a.registration_number = $registration_number,
        a.registration_date = $registration_date,
        a.status = $status,
        a.updated_at = datetime()
    RETURN a
    """
}

SCORE = {
    "label": "Score",
    "parent": "Thing",
    "description": "Exam score for a subject",
    "properties": {
        "score_id": "Score unique identifier",
        "score_value": "Numeric score value",
        "status": "Score status",
        "graded_by": "Person who graded",
        "graded_at": "When it was graded"
    },
    "create_query": """
    MERGE (s:Score {score_id: $score_id})
    ON CREATE SET
        s:Thing,
        s.score_value = $score_value,
        s.status = $status,
        s.graded_by = $graded_by,
        s.graded_at = $graded_at,
        s.created_at = datetime(),
        s.updated_at = datetime()
    ON MATCH SET
        s.score_value = $score_value,
        s.status = $status,
        s.graded_by = $graded_by,
        s.graded_at = $graded_at,
        s.updated_at = datetime()
    RETURN s
    """
}

SCORE_REVIEW = {
    "label": "ScoreReview",
    "parent": "Thing",
    "description": "Review of an exam score",
    "properties": {
        "review_id": "Review unique identifier",
        "request_date": "Date of review request",
        "review_status": "Status of the review",
        "original_score": "Original score",
        "reviewed_score": "Score after review",
        "review_date": "Date of review completion"
    },
    "create_query": """
    MERGE (r:ScoreReview {review_id: $review_id})
    ON CREATE SET
        r:Thing,
        r.request_date = $request_date,
        r.review_status = $review_status,
        r.original_score = $original_score,
        r.reviewed_score = $reviewed_score,
        r.review_date = $review_date,
        r.created_at = datetime(),
        r.updated_at = datetime()
    ON MATCH SET
        r.request_date = $request_date,
        r.review_status = $review_status,
        r.original_score = $original_score,
        r.reviewed_score = $reviewed_score,
        r.review_date = $review_date,
        r.updated_at = datetime()
    RETURN r
    """
}

SCORE_HISTORY = {
    "label": "ScoreHistory",
    "parent": "Thing",
    "description": "History of score changes",
    "properties": {
        "history_id": "History unique identifier",
        "previous_score": "Previous score value",
        "new_score": "New score value",
        "change_date": "Date of change",
        "change_reason": "Reason for change",
        "changed_by": "Person who made the change"
    },
    "create_query": """
    MERGE (h:ScoreHistory {history_id: $history_id})
    ON CREATE SET
        h:Thing,
        h.previous_score = $previous_score,
        h.new_score = $new_score,
        h.change_date = $change_date,
        h.change_reason = $change_reason,
        h.changed_by = $changed_by,
        h.created_at = datetime(),
        h.updated_at = datetime()
    ON MATCH SET
        h.previous_score = $previous_score,
        h.new_score = $new_score,
        h.change_date = $change_date,
        h.change_reason = $change_reason,
        h.changed_by = $changed_by,
        h.updated_at = datetime()
    RETURN h
    """
}

CERTIFICATE = {
    "label": "Certificate",
    "parent": "Thing",
    "description": "Certificate earned by candidate",
    "properties": {
        "certificate_id": "Certificate unique identifier",
        "certificate_number": "Certificate number",
        "issue_date": "Date of issue",
        "expiry_date": "Date of expiry"
    },
    "create_query": """
    MERGE (c:Certificate {certificate_id: $certificate_id})
    ON CREATE SET
        c:Thing,
        c.certificate_number = $certificate_number,
        c.issue_date = $issue_date,
        c.expiry_date = $expiry_date,
        c.created_at = datetime(),
        c.updated_at = datetime()
    ON MATCH SET
        c.certificate_number = $certificate_number,
        c.issue_date = $issue_date,
        c.expiry_date = $expiry_date,
        c.updated_at = datetime()
    RETURN c
    """
}

RECOGNITION = {
    "label": "Recognition",
    "parent": "Thing",
    "description": "Formal acknowledgment of achievement",
    "properties": {
        "recognition_id": "Recognition unique identifier",
        "title": "Title of the recognition",
        "issuing_organization": "Organization issuing the recognition",
        "issue_date": "Date of issue",
        "recognition_type": "Type of recognition"
    },
    "create_query": """
    MERGE (r:Recognition {recognition_id: $recognition_id})
    ON CREATE SET
        r:Thing,
        r.title = $title,
        r.issuing_organization = $issuing_organization,
        r.issue_date = $issue_date,
        r.recognition_type = $recognition_type,
        r.created_at = datetime(),
        r.updated_at = datetime()
    ON MATCH SET
        r.title = $title,
        r.issuing_organization = $issuing_organization,
        r.issue_date = $issue_date,
        r.recognition_type = $recognition_type,
        r.updated_at = datetime()
    RETURN r
    """
}

AWARD = {
    "label": "Award",
    "parent": "Thing",
    "description": "Award received in competition",
    "properties": {
        "award_id": "Award unique identifier",
        "award_type": "Type of award",
        "achievement": "Specific achievement",
        "award_date": "Date of award"
    },
    "create_query": """
    MERGE (a:Award {award_id: $award_id})
    ON CREATE SET
        a:Thing,
        a.award_type = $award_type,
        a.achievement = $achievement,
        a.award_date = $award_date,
        a.created_at = datetime(),
        a.updated_at = datetime()
    ON MATCH SET
        a.award_type = $award_type,
        a.achievement = $achievement,
        a.award_date = $award_date,
        a.updated_at = datetime()
    RETURN a
    """
}

ACHIEVEMENT = {
    "label": "Achievement",
    "parent": "Thing",
    "description": "General achievement outside exams",
    "properties": {
        "achievement_id": "Achievement unique identifier",
        "achievement_name": "Name of the achievement",
        "achievement_type": "Type of achievement",
        "achievement_date": "Date of achievement",
        "organization": "Organization recognizing the achievement"
    },
    "create_query": """
    MERGE (a:Achievement {achievement_id: $achievement_id})
    ON CREATE SET
        a:Thing,
        a.achievement_name = $achievement_name,
        a.achievement_type = $achievement_type,
        a.achievement_date = $achievement_date,
        a.organization = $organization,
        a.created_at = datetime(),
        a.updated_at = datetime()
    ON MATCH SET
        a.achievement_name = $achievement_name,
        a.achievement_type = $achievement_type,
        a.achievement_date = $achievement_date,
        a.organization = $organization,
        a.updated_at = datetime()
    RETURN a
    """
}

DEGREE = {
    "label": "Degree",
    "parent": "Thing",
    "description": "Higher education degree",
    "properties": {
        "degree_id": "Degree unique identifier",
        "start_year": "Starting year",
        "end_year": "Ending year",
        "academic_performance": "Academic performance",
        "degree_image_url": "URL to degree image"
    },
    "create_query": """
    MERGE (d:Degree {degree_id: $degree_id})
    ON CREATE SET
        d:Thing,
        d.start_year = $start_year,
        d.end_year = $end_year,
        d.academic_performance = $academic_performance,
        d.degree_image_url = $degree_image_url,
        d.created_at = datetime(),
        d.updated_at = datetime()
    ON MATCH SET
        d.start_year = $start_year,
        d.end_year = $end_year,
        d.academic_performance = $academic_performance,
        d.degree_image_url = $degree_image_url,
        d.updated_at = datetime()
    RETURN d
    """
}

CREDENTIAL = {
    "label": "Credential",
    "parent": "Thing",
    "description": "External credential provided by candidate",
    "properties": {
        "credential_id": "Credential unique identifier",
        "credential_type": "Type of credential",
        "title": "Title of the credential",
        "issuing_organization": "Organization issuing the credential",
        "issue_date": "Date of issue"
    },
    "create_query": """
    MERGE (c:Credential {credential_id: $credential_id})
    ON CREATE SET
        c:Thing,
        c.credential_type = $credential_type,
        c.title = $title,
        c.issuing_organization = $issuing_organization,
        c.issue_date = $issue_date,
        c.created_at = datetime(),
        c.updated_at = datetime()
    ON MATCH SET
        c.credential_type = $credential_type,
        c.title = $title,
        c.issuing_organization = $issuing_organization,
        c.issue_date = $issue_date,
        c.updated_at = datetime()
    RETURN c
    """
}

EXAM_ROOM = {
    "label": "ExamRoom",
    "parent": "Thing",
    "description": "Room within an exam location where exams are conducted",
    "properties": {
        "room_id": "Room unique identifier",
        "room_name": "Name of the room",
        "location_id": "ID of the location containing this room",
        "capacity": "Maximum capacity",
        "floor": "Floor number",
        "room_number": "Room identifier within the location"
    },
    "create_query": """
    MERGE (r:ExamRoom {room_id: $room_id})
    ON CREATE SET
        r:Thing,
        r.name = $room_name,
        r.room_name = $room_name,
        r.location_id = $location_id,
        r.capacity = $capacity,
        r.floor = $floor,
        r.room_number = $room_number,
        r.created_at = datetime(),
        r.updated_at = datetime()
    ON MATCH SET
        r.name = $room_name,
        r.room_name = $room_name,
        r.location_id = $location_id,
        r.capacity = $capacity,
        r.floor = $floor,
        r.room_number = $room_number,
        r.updated_at = datetime()
    RETURN r
    """
}

MANAGEMENT_UNIT = {
    "label": "ManagementUnit",
    "parent": "Thing",
    "description": "Administrative unit",
    "properties": {
        "unit_id": "Unit unique identifier",
        "unit_name": "Name of the unit",
        "unit_type": "Type of unit"
    },
    "create_query": """
    MERGE (u:ManagementUnit {unit_id: $unit_id})
    ON CREATE SET
        u:Thing,
        u.unit_name = $unit_name,
        u.unit_type = $unit_type,
        u.created_at = datetime(),
        u.updated_at = datetime()
    ON MATCH SET
        u.unit_name = $unit_name,
        u.unit_type = $unit_type,
        u.updated_at = datetime()
    RETURN u
    """
}

# ------------- RELATIONSHIP DEFINITIONS -------------

# 1. Inheritance relationship
IS_A = {
    "type": "IS_A",
    "description": "Inheritance relationship from child to parent class",
    "create_query": """
    MATCH (child {id: $child_id})
    MATCH (parent:Thing {id: $parent_id})
    MERGE (child)-[r:IS_A]->(parent)
    RETURN r
    """
}

# 2. Functional relationships between entities
STUDIES_AT = {
    "type": "STUDIES_AT",
    "description": "Relationship between a Candidate and a School",
    "properties": {
        "start_year": "Starting year of study",
        "end_year": "Ending year of study",
        "education_level": "Level of education"
    },
    "create_query": """
    MATCH (c:Candidate {candidate_id: $candidate_id})
    MATCH (s:School {school_id: $school_id})
    MERGE (c)-[r:STUDIES_AT {
        start_year: $start_year,
        end_year: $end_year,
        education_level: $education_level
    }]->(s)
    RETURN r
    """
}

ATTENDS_EXAM = {
    "type": "ATTENDS_EXAM",
    "description": "Relationship between a Candidate and an Exam",
    "properties": {
        "registration_number": "Registration number",
        "registration_date": "Registration date",
        "status": "Status of attendance"
    },
    "create_query": """
    MATCH (c:Candidate {candidate_id: $candidate_id})
    MATCH (e:Exam {exam_id: $exam_id})
    MERGE (c)-[r:ATTENDS_EXAM {
        registration_number: $registration_number,
        registration_date: $registration_date,
        status: $status
    }]->(e)
    RETURN r
    """
}

HAS_ATTEMPT = {
    "type": "HAS_ATTEMPT",
    "description": "Relationship between a Candidate and an ExamAttempt",
    "create_query": """
    MATCH (c:Candidate {candidate_id: $candidate_id})
    MATCH (a:ExamAttempt {attempt_id: $attempt_id})
    MERGE (c)-[r:HAS_ATTEMPT]->(a)
    RETURN r
    """
}

RECEIVES_SCORE = {
    "type": "RECEIVES_SCORE",
    "description": "Relationship between a Candidate and a Score",
    "create_query": """
    MATCH (c:Candidate {candidate_id: $candidate_id})
    MATCH (s:Score {score_id: $score_id})
    MERGE (c)-[r:RECEIVES_SCORE]->(s)
    RETURN r
    """
}

REQUESTS_REVIEW = {
    "type": "REQUESTS_REVIEW",
    "description": "Relationship between a Candidate and a ScoreReview",
    "create_query": """
    MATCH (c:Candidate {candidate_id: $candidate_id})
    MATCH (r:ScoreReview {review_id: $review_id})
    MERGE (c)-[rel:REQUESTS_REVIEW]->(r)
    RETURN rel
    """
}

HOLDS_DEGREE = {
    "type": "HOLDS_DEGREE",
    "description": "Relationship between a Candidate and a Degree",
    "create_query": """
    MATCH (c:Candidate {candidate_id: $candidate_id})
    MATCH (d:Degree {degree_id: $degree_id})
    MERGE (c)-[r:HOLDS_DEGREE]->(d)
    RETURN r
    """
}

PROVIDES_CREDENTIAL = {
    "type": "PROVIDES_CREDENTIAL",
    "description": "Relationship between a Candidate and a Credential",
    "create_query": """
    MATCH (c:Candidate {candidate_id: $candidate_id})
    MATCH (cr:Credential {credential_id: $credential_id})
    MERGE (c)-[r:PROVIDES_CREDENTIAL]->(cr)
    RETURN r
    """
}

EARNS_CERTIFICATE = {
    "type": "EARNS_CERTIFICATE",
    "description": "Relationship between a Candidate and a Certificate",
    "create_query": """
    MATCH (c:Candidate {candidate_id: $candidate_id})
    MATCH (cert:Certificate {certificate_id: $certificate_id})
    MERGE (c)-[r:EARNS_CERTIFICATE]->(cert)
    RETURN r
    """
}

RECEIVES_RECOGNITION = {
    "type": "RECEIVES_RECOGNITION",
    "description": "Relationship between a Candidate and a Recognition",
    "create_query": """
    MATCH (c:Candidate {candidate_id: $candidate_id})
    MATCH (r:Recognition {recognition_id: $recognition_id})
    MERGE (c)-[rel:RECEIVES_RECOGNITION]->(r)
    RETURN rel
    """
}

EARNS_AWARD = {
    "type": "EARNS_AWARD",
    "description": "Relationship between a Candidate and an Award",
    "create_query": """
    MATCH (c:Candidate {candidate_id: $candidate_id})
    MATCH (a:Award {award_id: $award_id})
    MERGE (c)-[r:EARNS_AWARD]->(a)
    RETURN r
    """
}

ACHIEVES = {
    "type": "ACHIEVES",
    "description": "Relationship between a Candidate and an Achievement",
    "create_query": """
    MATCH (c:Candidate {candidate_id: $candidate_id})
    MATCH (a:Achievement {achievement_id: $achievement_id})
    MERGE (c)-[r:ACHIEVES]->(a)
    RETURN r
    """
}

OFFERS_MAJOR = {
    "type": "OFFERS_MAJOR",
    "description": "Relationship between a School and a Major",
    "properties": {
        "start_year": "Year when the school started offering the major"
    },
    "create_query": """
    MATCH (s:School {school_id: $school_id})
    MATCH (m:Major {major_id: $major_id})
    MERGE (s)-[r:OFFERS_MAJOR {
        start_year: $start_year
    }]->(m)
    RETURN r
    """
}

FOR_SUBJECT = {
    "type": "FOR_SUBJECT",
    "description": "Relationship between a Score and a Subject",
    "create_query": """
    MATCH (score:Score {score_id: $score_id})
    MATCH (subject:Subject {subject_id: $subject_id})
    MERGE (score)-[r:FOR_SUBJECT]->(subject)
    RETURN r
    """
}

IN_EXAM = {
    "type": "IN_EXAM",
    "description": "Relationship between a Score and an Exam",
    "create_query": """
    MATCH (score:Score {score_id: $score_id})
    MATCH (exam:Exam {exam_id: $exam_id})
    MERGE (score)-[r:IN_EXAM]->(exam)
    RETURN r
    """
}

FOR_ATTEMPT = {
    "type": "FOR_ATTEMPT",
    "description": "Relationship between a Score and an ExamAttempt",
    "create_query": """
    MATCH (score:Score {score_id: $score_id})
    MATCH (attempt:ExamAttempt {attempt_id: $attempt_id})
    MERGE (score)-[r:FOR_ATTEMPT]->(attempt)
    RETURN r
    """
}

TEACHES_SUBJECT = {
    "type": "TEACHES_SUBJECT",
    "description": "Relationship between a Major and a Subject",
    "properties": {
        "is_mandatory": "Whether the subject is mandatory",
        "credits": "Number of credits"
    },
    "create_query": """
    MATCH (m:Major {major_id: $major_id})
    MATCH (s:Subject {subject_id: $subject_id})
    MERGE (m)-[r:TEACHES_SUBJECT {
        is_mandatory: $is_mandatory,
        credits: $credits
    }]->(s)
    RETURN r
    """
}

INCLUDES_SUBJECT = {
    "type": "INCLUDES_SUBJECT",
    "description": "Relationship between an Exam and a Subject",
    "properties": {
        "exam_date": "Date of the subject exam",
        "duration_minutes": "Duration of the exam in minutes"
    },
    "create_query": """
    MATCH (e:Exam {exam_id: $exam_id})
    MATCH (s:Subject {subject_id: $subject_id})
    MERGE (e)-[r:INCLUDES_SUBJECT {
        exam_date: $exam_date,
        duration_minutes: $duration_minutes
    }]->(s)
    RETURN r
    """
}

FOLLOWS_SCHEDULE = {
    "type": "FOLLOWS_SCHEDULE",
    "description": "Relationship between an Exam and an ExamSchedule",
    "create_query": """
    MATCH (e:Exam {exam_id: $exam_id})
    MATCH (s:ExamSchedule {schedule_id: $schedule_id})
    MERGE (e)-[r:FOLLOWS_SCHEDULE]->(s)
    RETURN r
    """
}

HELD_AT = {
    "type": "HELD_AT",
    "description": "Relationship between an Exam and an ExamLocation",
    "create_query": """
    MATCH (e:Exam {exam_id: $exam_id})
    MATCH (l:ExamLocation {location_id: $location_id})
    MERGE (e)-[r:HELD_AT]->(l)
    RETURN r
    """
}

LOCATED_IN = {
    "type": "LOCATED_IN",
    "description": "Relationship between an ExamRoom and an ExamLocation",
    "create_query": """
    MATCH (r:ExamRoom {room_id: $room_id})
    MATCH (l:ExamLocation {location_id: $location_id})
    MERGE (r)-[rel:LOCATED_IN]->(l)
    RETURN rel
    """
}

RELATED_TO = {
    "type": "RELATED_TO",
    "description": "Relationship between a Degree and a Major",
    "create_query": """
    MATCH (d:Degree {degree_id: $degree_id})
    MATCH (m:Major {major_id: $major_id})
    MERGE (d)-[r:RELATED_TO]->(m)
    RETURN r
    """
}

FOR_EXAM = {
    "type": "FOR_EXAM",
    "description": "Relationship between an ExamAttempt and an Exam",
    "create_query": """
    MATCH (a:ExamAttempt {attempt_id: $attempt_id})
    MATCH (e:Exam {exam_id: $exam_id})
    MERGE (a)-[r:FOR_EXAM]->(e)
    RETURN r
    """
}

ATTEMPT_FOLLOWS_SCHEDULE = {
    "type": "FOLLOWS_SCHEDULE",
    "description": "Relationship between an ExamAttempt and an ExamSchedule",
    "create_query": """
    MATCH (a:ExamAttempt {attempt_id: $attempt_id})
    MATCH (s:ExamSchedule {schedule_id: $schedule_id})
    MERGE (a)-[r:FOLLOWS_SCHEDULE]->(s)
    RETURN r
    """
}

HAS_HISTORY = {
    "type": "HAS_HISTORY",
    "description": "Relationship between a Score and a ScoreHistory",
    "create_query": """
    MATCH (s:Score {score_id: $score_id})
    MATCH (h:ScoreHistory {history_id: $history_id})
    MERGE (s)-[r:HAS_HISTORY]->(h)
    RETURN r
    """
}

HAS_REVIEW = {
    "type": "HAS_REVIEW",
    "description": "Relationship between a Score and a ScoreReview",
    "create_query": """
    MATCH (s:Score {score_id: $score_id})
    MATCH (r:ScoreReview {review_id: $review_id})
    MERGE (s)-[r:HAS_REVIEW]->(r)
    RETURN r
    """
}

# Dictionary of all classes
CLASSES = {
    "Thing": THING,
    "Candidate": CANDIDATE,
    "School": SCHOOL,
    "Major": MAJOR,
    "Subject": SUBJECT,
    "Exam": EXAM,
    "ExamLocation": EXAM_LOCATION,
    "ExamSchedule": EXAM_SCHEDULE,
    "ExamAttempt": EXAM_ATTEMPT,
    "Score": SCORE,
    "ScoreReview": SCORE_REVIEW,
    "ScoreHistory": SCORE_HISTORY,
    "Certificate": CERTIFICATE,
    "Recognition": RECOGNITION,
    "Award": AWARD,
    "Achievement": ACHIEVEMENT,
    "Degree": DEGREE,
    "Credential": CREDENTIAL,
    "ExamRoom": EXAM_ROOM,
    "ManagementUnit": MANAGEMENT_UNIT
}

# Dictionary of all relationships
RELATIONSHIPS = {
    "IS_A": IS_A,
    "STUDIES_AT": STUDIES_AT,
    "ATTENDS_EXAM": ATTENDS_EXAM,
    "HAS_ATTEMPT": HAS_ATTEMPT,
    "RECEIVES_SCORE": RECEIVES_SCORE,
    "REQUESTS_REVIEW": REQUESTS_REVIEW,
    "HOLDS_DEGREE": HOLDS_DEGREE,
    "PROVIDES_CREDENTIAL": PROVIDES_CREDENTIAL,
    "EARNS_CERTIFICATE": EARNS_CERTIFICATE,
    "RECEIVES_RECOGNITION": RECEIVES_RECOGNITION,
    "EARNS_AWARD": EARNS_AWARD,
    "ACHIEVES": ACHIEVES,
    "OFFERS_MAJOR": OFFERS_MAJOR,
    "FOR_SUBJECT": FOR_SUBJECT,
    "IN_EXAM": IN_EXAM,
    "FOR_ATTEMPT": FOR_ATTEMPT,
    "TEACHES_SUBJECT": TEACHES_SUBJECT,
    "INCLUDES_SUBJECT": INCLUDES_SUBJECT,
    "FOLLOWS_SCHEDULE": FOLLOWS_SCHEDULE,
    "HELD_AT": HELD_AT,
    "LOCATED_IN": LOCATED_IN,
    "RELATED_TO": RELATED_TO,
    "FOR_EXAM": FOR_EXAM,
    "ATTEMPT_FOLLOWS_SCHEDULE": ATTEMPT_FOLLOWS_SCHEDULE,
    "HAS_HISTORY": HAS_HISTORY,
    "HAS_REVIEW": HAS_REVIEW
} 