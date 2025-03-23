"""
Ontology definition module.

This module defines the knowledge graph ontology structure for the candidate information system.
It includes class definitions and relationship types to model the domain knowledge.
"""

# ------------- CLASS DEFINITIONS -------------

# System classes for ontology
ONTOLOGY_INSTANCE = {
    "label": "OntologyInstance",
    "description": "Base class for all entity instances in the knowledge graph",
    "properties": {
        "created_at": "Creation timestamp",
        "updated_at": "Last update timestamp"
    },
    "create_query": """
    MERGE (i:OntologyInstance {id: $id})
    ON CREATE SET
        i.created_at = datetime(),
        i.updated_at = datetime()
    ON MATCH SET
        i.updated_at = datetime()
    RETURN i
    """
}

ONTOLOGY_CLASS = {
    "label": "OntologyClass",
    "description": "Base class for all class definitions in the knowledge graph",
    "properties": {
        "id": "Class identifier",
        "name": "Class name",
        "description": "Class description"
    },
    "create_query": """
    MERGE (c:OntologyClass {id: $id})
    ON CREATE SET
        c.name = $name,
        c.description = $description,
        c.created_at = datetime(),
        c.updated_at = datetime()
    ON MATCH SET
        c.name = $name,
        c.description = $description,
        c.updated_at = datetime()
    RETURN c
    """
}

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

SCORE = {
    "label": "Score",
    "parent": "Thing",
    "description": "Exam score for a subject",
    "properties": {
        "score_id": "Score unique identifier",
        "score_value": "Numeric score value",
        "status": "Score status",
        "graded_by": "Person who graded",
        "graded_at": "When it was graded",
        "score_history": "Array of previous score values with change dates and reasons"
    },
    "create_query": """
    MERGE (s:Score {score_id: $score_id})
    ON CREATE SET
        s:Thing,
        s.score_value = $score_value,
        s.status = $status,
        s.graded_by = $graded_by,
        s.graded_at = $graded_at,
        s.score_history = $score_history,
        s.created_at = datetime(),
        s.updated_at = datetime()
    ON MATCH SET
        s.score_value = $score_value,
        s.status = $status,
        s.graded_by = $graded_by,
        s.graded_at = $graded_at,
        s.score_history = $score_history,
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

# Instance-class relationship
INSTANCE_OF = {
    "type": "INSTANCE_OF",
    "description": "Relationship between an instance and its class definition",
    "create_query": """
    MATCH (instance:OntologyInstance {id: $instance_id})
    MATCH (class:OntologyClass {id: $class_id})
    MERGE (instance)-[r:INSTANCE_OF]->(class)
    RETURN r
    """
}

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
        "education_level": "Level of education",
        "academic_performance": "Academic performance (Good, Excellent, etc.)",
        "additional_info": "Additional information about the education"
    },
    "create_query": """
    MATCH (c:Candidate {candidate_id: $candidate_id})
    MATCH (s:School {school_id: $school_id})
    MERGE (c)-[r:STUDIES_AT {
        start_year: $start_year,
        end_year: $end_year,
        education_level: $education_level,
        academic_performance: $academic_performance,
        additional_info: $additional_info
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
        "status": "Status of attendance",
        "attempt_number": "Attempt number for this exam",
        "attempt_date": "Date of the latest attempt",
        "attempts": "Array of previous attempts with dates and results",
        "result": "Result of the exam (pass/fail)"
    },
    "create_query": """
    MATCH (c:Candidate {candidate_id: $candidate_id})
    MATCH (e:Exam {exam_id: $exam_id})
    MERGE (c)-[r:ATTENDS_EXAM {
        registration_number: $registration_number,
        registration_date: $registration_date,
        status: $status,
        attempt_number: $attempt_number,
        attempt_date: $attempt_date,
        attempts: $attempts,
        result: $result
    }]->(e)
    RETURN r
    """
}

RECEIVES_SCORE = {
    "type": "RECEIVES_SCORE",
    "description": "Relationship between a Candidate and a Score",
    "properties": {
        "exam_id": "ID of the exam",
        "exam_name": "Name of the exam",
        "subject_id": "ID of the subject",
        "subject_name": "Name of the subject",
        "registration_status": "Status of the subject registration",
        "registration_date": "Date of registration for the subject",
        "is_required": "Whether this subject is mandatory for the candidate",
        "exam_date": "Date of the exam for this subject"
    },
    "create_query": """
    MATCH (c:Candidate {candidate_id: $candidate_id})
    MATCH (s:Score {score_id: $score_id})
    MERGE (c)-[r:RECEIVES_SCORE {
        exam_id: $exam_id,
        exam_name: $exam_name,
        subject_id: $subject_id,
        subject_name: $subject_name,
        registration_status: $registration_status,
        registration_date: $registration_date,
        is_required: $is_required,
        exam_date: $exam_date
    }]->(s)
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
    "properties": {
        "start_year": "Starting year of degree",
        "end_year": "Ending year of degree",
        "academic_performance": "Academic performance (Good, Excellent)",
        "education_level": "Level of education",
        "school_id": "ID of the school where degree was earned",
        "school_name": "Name of the school where degree was earned",
        "additional_info": "Additional information about the degree"
    },
    "create_query": """
    MATCH (c:Candidate {candidate_id: $candidate_id})
    MATCH (d:Degree {degree_id: $degree_id})
    MERGE (c)-[r:HOLDS_DEGREE {
        start_year: $start_year,
        end_year: $end_year,
        academic_performance: $academic_performance,
        education_level: $education_level,
        school_id: $school_id,
        school_name: $school_name,
        additional_info: $additional_info
    }]->(d)
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
        "start_year": "Year when the school started offering the major",
        "is_active": "Whether the major is still offered by the school",
        "additional_info": "Additional information about the major offering"
    },
    "create_query": """
    MATCH (s:School {school_id: $school_id})
    MATCH (m:Major {major_id: $major_id})
    MERGE (s)-[r:OFFERS_MAJOR {
        start_year: $start_year,
        is_active: $is_active,
        additional_info: $additional_info
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
        "duration_minutes": "Duration of the exam in minutes",
        "weight": "Weight of the subject in the exam (default 1.0)",
        "passing_score": "Minimum score to pass the subject",
        "max_score": "Maximum possible score (default 100.0)",
        "is_required": "Whether this subject is mandatory in the exam",
        "additional_info": "Additional information about the subject in the exam",
        "subject_metadata": "Metadata for the subject in the exam"
    },
    "create_query": """
    MATCH (e:Exam {exam_id: $exam_id})
    MATCH (s:Subject {subject_id: $subject_id})
    MERGE (e)-[r:INCLUDES_SUBJECT {
        exam_date: $exam_date,
        duration_minutes: $duration_minutes,
        weight: $weight,
        passing_score: $passing_score,
        max_score: $max_score,
        is_required: $is_required,
        additional_info: $additional_info,
        subject_metadata: $subject_metadata
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
    "properties": {
        "is_primary": "Whether this is the primary location for the exam",
        "is_active": "Whether this location mapping is active",
        "mapping_metadata": "Additional metadata for the location mapping"
    },
    "create_query": """
    MATCH (e:Exam {exam_id: $exam_id})
    MATCH (l:ExamLocation {location_id: $location_id})
    MERGE (e)-[r:HELD_AT {
        is_primary: $is_primary,
        is_active: $is_active,
        mapping_metadata: $mapping_metadata
    }]->(l)
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

REGISTERS_FOR_SUBJECT = {
    "type": "REGISTERS_FOR_SUBJECT",
    "description": "Relationship between a Candidate and an ExamSubject",
    "properties": {
        "registration_date": "Date of registration",
        "status": "Registration status (REGISTERED, CONFIRMED, WITHDRAWN, ABSENT, COMPLETED)",
        "is_required": "Whether this subject is mandatory for the candidate",
        "notes": "Additional notes about the registration"
    },
    "create_query": """
    MATCH (c:Candidate {candidate_id: $candidate_id})
    MATCH (es:ExamSubject {exam_subject_id: $exam_subject_id})
    MERGE (c)-[r:REGISTERS_FOR_SUBJECT {
        registration_date: $registration_date,
        status: $status,
        is_required: $is_required,
        notes: $notes
    }]->(es)
    RETURN r
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

RELATED_TO_EXAM = {
    "type": "RELATED_TO_EXAM",
    "description": "Relationship between a Certificate/Recognition/Award/Achievement and an Exam",
    "properties": {
        "issue_date": "Date when the relationship was established"
    },
    "create_query": """
    MATCH (a) WHERE a:Certificate OR a:Recognition OR a:Award OR a:Achievement
    MATCH (e:Exam {exam_id: $exam_id})
    MERGE (a)-[r:RELATED_TO_EXAM {
        issue_date: $issue_date
    }]->(e)
    RETURN r
    """
}

CERTIFICATE_FOR_EXAM = {
    "type": "CERTIFICATE_FOR_EXAM",
    "description": "Relationship between a Certificate and an Exam",
    "properties": {
        "issue_date": "Date when the certificate was issued",
        "certificate_type": "Type of certificate issued for the exam"
    },
    "create_query": """
    MATCH (c:Certificate {certificate_id: $certificate_id})
    MATCH (e:Exam {exam_id: $exam_id})
    MERGE (c)-[r:CERTIFICATE_FOR_EXAM {
        issue_date: $issue_date,
        certificate_type: $certificate_type
    }]->(e)
    RETURN r
    """
}

RECOGNITION_FOR_EXAM = {
    "type": "RECOGNITION_FOR_EXAM",
    "description": "Relationship between a Recognition and an Exam",
    "properties": {
        "issue_date": "Date when the recognition was issued",
        "recognition_type": "Type of recognition issued for the exam"
    },
    "create_query": """
    MATCH (r:Recognition {recognition_id: $recognition_id})
    MATCH (e:Exam {exam_id: $exam_id})
    MERGE (r)-[rel:RECOGNITION_FOR_EXAM {
        issue_date: $issue_date,
        recognition_type: $recognition_type
    }]->(e)
    RETURN rel
    """
}

AWARD_FOR_EXAM = {
    "type": "AWARD_FOR_EXAM",
    "description": "Relationship between an Award and an Exam",
    "properties": {
        "issue_date": "Date when the award was issued",
        "award_type": "Type of award issued for the exam"
    },
    "create_query": """
    MATCH (a:Award {award_id: $award_id})
    MATCH (e:Exam {exam_id: $exam_id})
    MERGE (a)-[r:AWARD_FOR_EXAM {
        issue_date: $issue_date,
        award_type: $award_type
    }]->(e)
    RETURN r
    """
}

ACHIEVEMENT_FOR_EXAM = {
    "type": "ACHIEVEMENT_FOR_EXAM",
    "description": "Relationship between an Achievement and an Exam",
    "properties": {
        "issue_date": "Date when the achievement was recorded",
        "achievement_type": "Type of achievement for the exam"
    },
    "create_query": """
    MATCH (a:Achievement {achievement_id: $achievement_id})
    MATCH (e:Exam {exam_id: $exam_id})
    MERGE (a)-[r:ACHIEVEMENT_FOR_EXAM {
        issue_date: $issue_date,
        achievement_type: $achievement_type
    }]->(e)
    RETURN r
    """
}

ISSUED_BY = {
    "type": "ISSUED_BY",
    "description": "Relationship between a Degree and the School that issued it",
    "properties": {
        "issue_date": "Date when the degree was issued",
        "education_level": "Level of education for this degree (Bachelor's, Master's, Ph.D, etc.)",
        "program_name": "Name of the educational program",
        "is_verified": "Whether the degree has been verified by the system"
    },
    "create_query": """
    MATCH (d:Degree {degree_id: $degree_id})
    MATCH (s:School {school_id: $school_id})
    MERGE (d)-[r:ISSUED_BY {
        issue_date: $issue_date,
        education_level: $education_level,
        program_name: $program_name,
        is_verified: $is_verified
    }]->(s)
    RETURN r
    """
}

STUDIES_MAJOR = {
    "type": "STUDIES_MAJOR",
    "description": "Relationship between a Candidate and a Major",
    "properties": {
        "start_year": "Starting year of study",
        "end_year": "Ending year of study",
        "education_level": "Level of education",
        "academic_performance": "Academic performance (Good, Excellent, etc.)",
        "school_id": "ID of the school where the major was studied",
        "school_name": "Name of the school where the major was studied",
        "additional_info": "Additional information about the study"
    },
    "create_query": """
    MATCH (c:Candidate {candidate_id: $candidate_id})
    MATCH (m:Major {major_id: $major_id})
    MERGE (c)-[r:STUDIES_MAJOR {
        start_year: $start_year,
        end_year: $end_year,
        education_level: $education_level,
        academic_performance: $academic_performance,
        school_id: $school_id,
        school_name: $school_name,
        additional_info: $additional_info
    }]->(m)
    RETURN r
    """
}

HAS_EXAM_SCHEDULE = {
    "type": "HAS_EXAM_SCHEDULE",
    "description": "Relationship between a Candidate and an ExamSchedule, representing a candidate's exam schedule",
    "properties": {
        "exam_id": "ID of the exam",
        "exam_name": "Name of the exam",
        "subject_id": "ID of the subject being tested",
        "subject_name": "Name of the subject being tested",
        "registration_status": "Status of the registration for this exam schedule",
        "registration_date": "Date of registration for this exam schedule",
        "is_required": "Whether this exam schedule is mandatory for the candidate",
        "room_id": "ID of the assigned exam room",
        "room_name": "Name of the assigned exam room",
        "seat_number": "Assigned seat number in the room",
        "assignment_date": "Date when the room assignment was made"
    },
    "create_query": """
    MATCH (c:Candidate {candidate_id: $candidate_id})
    MATCH (s:ExamSchedule {schedule_id: $schedule_id})
    MERGE (c)-[r:HAS_EXAM_SCHEDULE {
        exam_id: $exam_id,
        exam_name: $exam_name,
        subject_id: $subject_id,
        subject_name: $subject_name,
        registration_status: $registration_status,
        registration_date: $registration_date,
        is_required: $is_required,
        room_id: $room_id,
        room_name: $room_name,
        seat_number: $seat_number,
        assignment_date: $assignment_date
    }]->(s)
    RETURN r
    """
}

# Relationship between Exam and ManagementUnit
ORGANIZED_BY = {
    "type": "ORGANIZED_BY",
    "description": "Relationship between an Exam and a ManagementUnit, representing which unit organizes the exam",
    "properties": {
        "is_primary": "Whether this is the primary organizing unit for the exam",
        "organization_date": "Date when the unit was assigned to organize the exam",
        "role": "Role of the management unit in organizing the exam (Primary, Supporting, Administrative, etc.)",
        "status": "Status of the organization (Planning, In Progress, Completed, etc.)"
    },
    "create_query": """
    MATCH (e:Exam {exam_id: $exam_id})
    MATCH (m:ManagementUnit {unit_id: $unit_id})
    MERGE (e)-[r:ORGANIZED_BY {
        is_primary: $is_primary,
        organization_date: $organization_date,
        role: $role,
        status: $status
    }]->(m)
    RETURN r
    """
}

# Relationship between ExamSchedule and ExamRoom
ASSIGNED_TO = {
    "type": "ASSIGNED_TO",
    "description": "Relationship between an ExamSchedule and an ExamRoom, representing the room where the schedule takes place",
    "properties": {
        "assigned_date": "Date when the room was assigned",
        "is_confirmed": "Whether the room assignment is confirmed",
        "status": "Status of the assignment (Planned, Confirmed, Cancelled)",
        "capacity": "Assigned capacity for this schedule (might differ from room capacity)",
        "assignment_notes": "Additional notes about the room assignment"
    },
    "create_query": """
    MATCH (s:ExamSchedule {schedule_id: $schedule_id})
    MATCH (r:ExamRoom {room_id: $room_id})
    MERGE (s)-[rel:ASSIGNED_TO {
        assigned_date: $assigned_date,
        is_confirmed: $is_confirmed,
        status: $status,
        capacity: $capacity,
        assignment_notes: $assignment_notes
    }]->(r)
    RETURN rel
    """
}

# Relationship between ExamSchedule and ExamSubject
SCHEDULES_SUBJECT = {
    "type": "SCHEDULES_SUBJECT",
    "description": "Relationship between an ExamSchedule and an ExamSubject, representing a subject scheduled for examination",
    "properties": {
        "duration_minutes": "Duration of the exam for this subject",
        "max_score": "Maximum possible score",
        "passing_score": "Minimum score required to pass",
        "weight": "Weight of this subject in the overall exam",
        "is_required": "Whether this subject is mandatory"
    },
    "create_query": """
    MATCH (s:ExamSchedule {schedule_id: $schedule_id})
    MATCH (es:ExamSubject {exam_subject_id: $exam_subject_id})
    MERGE (s)-[rel:SCHEDULES_SUBJECT {
        duration_minutes: $duration_minutes,
        max_score: $max_score,
        passing_score: $passing_score,
        weight: $weight,
        is_required: $is_required
    }]->(es)
    RETURN rel
    """
}

# Relationship between ExamSchedule and ExamLocation
SCHEDULE_AT = {
    "type": "SCHEDULE_AT",
    "description": "Relationship between an ExamSchedule and an ExamLocation, representing the location where the schedule takes place",
    "properties": {
        "is_primary": "Whether this is the primary location for this schedule",
        "is_active": "Whether this location assignment is active",
        "assignment_date": "Date when the location was assigned",
        "notes": "Additional notes about the location assignment"
    },
    "create_query": """
    MATCH (s:ExamSchedule {schedule_id: $schedule_id})
    MATCH (l:ExamLocation {location_id: $location_id})
    MERGE (s)-[rel:SCHEDULE_AT {
        is_primary: $is_primary,
        is_active: $is_active,
        assignment_date: $assignment_date,
        notes: $notes
    }]->(l)
    RETURN rel
    """
}

# Relationship between ScoreReview and Score
REVIEWS = {
    "type": "REVIEWS",
    "description": "Relationship between a ScoreReview and a Score, representing a review of a score",
    "properties": {
        "review_date": "Date of the review request",
        "review_status": "Status of the review",
        "reviewer": "Person who reviewed the score"
    },
    "create_query": """
    MATCH (r:ScoreReview {review_id: $review_id})
    MATCH (s:Score {score_id: $score_id})
    MERGE (r)-[rel:REVIEWS {
        review_date: $review_date,
        review_status: $review_status,
        reviewer: $reviewer
    }]->(s)
    RETURN rel
    """
}

# Dictionary of all classes
CLASSES = {
    "Thing": THING,
    "OntologyInstance": ONTOLOGY_INSTANCE,
    "OntologyClass": ONTOLOGY_CLASS,
    "Candidate": CANDIDATE,
    "School": SCHOOL,
    "Major": MAJOR,
    "Subject": SUBJECT,
    "Exam": EXAM,
    "ExamLocation": EXAM_LOCATION,
    "ExamSchedule": EXAM_SCHEDULE,
    "Score": SCORE,
    "ScoreReview": SCORE_REVIEW,
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
    "INSTANCE_OF": INSTANCE_OF,
    "STUDIES_AT": STUDIES_AT,
    "ATTENDS_EXAM": ATTENDS_EXAM,
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
    "TEACHES_SUBJECT": TEACHES_SUBJECT,
    "INCLUDES_SUBJECT": INCLUDES_SUBJECT,
    "FOLLOWS_SCHEDULE": FOLLOWS_SCHEDULE,
    "HELD_AT": HELD_AT,
    "LOCATED_IN": LOCATED_IN,
    "RELATED_TO": RELATED_TO,
    "REGISTERS_FOR_SUBJECT": REGISTERS_FOR_SUBJECT,
    "RELATED_TO_EXAM": RELATED_TO_EXAM,
    "CERTIFICATE_FOR_EXAM": CERTIFICATE_FOR_EXAM,
    "RECOGNITION_FOR_EXAM": RECOGNITION_FOR_EXAM,
    "AWARD_FOR_EXAM": AWARD_FOR_EXAM,
    "ACHIEVEMENT_FOR_EXAM": ACHIEVEMENT_FOR_EXAM,
    "STUDIES_MAJOR": STUDIES_MAJOR,
    "HAS_EXAM_SCHEDULE": HAS_EXAM_SCHEDULE,
    "ORGANIZED_BY": ORGANIZED_BY,
    "ISSUED_BY": ISSUED_BY,
    "ASSIGNED_TO": ASSIGNED_TO,
    "SCHEDULES_SUBJECT": SCHEDULES_SUBJECT,
    "SCHEDULE_AT": SCHEDULE_AT,
    "REVIEWS": REVIEWS
} 