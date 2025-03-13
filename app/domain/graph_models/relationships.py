# Định nghĩa các relationship trong đồ thị tri thức Neo4j

# Thí sinh - Trường học
STUDIES_AT = {
    "type": "STUDIES_AT",
    "create_query": """
    MATCH (c:Candidate {candidate_id: $candidate_id})
    MATCH (s:School {school_id: $school_id})
    MERGE (c)-[r:STUDIES_AT {
        start_year: $start_year,
        end_year: $end_year,
        education_level: $education_level,
        academic_performance: $academic_performance,
        major_id: $major_id
    }]->(s)
    RETURN r
    """
}

# Thí sinh - Kỳ thi
ATTENDS_EXAM = {
    "type": "ATTENDS_EXAM",
    "create_query": """
    MATCH (c:Candidate {candidate_id: $candidate_id})
    MATCH (e:Exam {exam_id: $exam_id})
    MERGE (c)-[r:ATTENDS_EXAM {
        registration_number: $registration_number,
        registration_date: $registration_date,
        status: $status,
        attempt_number: $attempt_number
    }]->(e)
    RETURN r
    """
}

# Thí sinh - Điểm thi
HAS_SCORE = {
    "type": "HAS_SCORE",
    "create_query": """
    MATCH (c:Candidate {candidate_id: $candidate_id})
    MATCH (s:Subject {subject_id: $subject_id})
    MATCH (e:Exam {exam_id: $exam_id})
    MERGE (c)-[r:HAS_SCORE {
        exam_id: $exam_id,
        score: $score
    }]->(s)
    RETURN r
    """
}

# Thí sinh - Chứng chỉ
ACHIEVES_CERTIFICATE = {
    "type": "ACHIEVES_CERTIFICATE",
    "create_query": """
    MATCH (c:Candidate {candidate_id: $candidate_id})
    MATCH (cert:Certificate {certificate_id: $certificate_id})
    MERGE (c)-[r:ACHIEVES_CERTIFICATE {
        issue_date: $issue_date,
        expiry_date: $expiry_date
    }]->(cert)
    RETURN r
    """
}

# Thí sinh - Giải thưởng
EARNS_AWARD = {
    "type": "EARNS_AWARD",
    "create_query": """
    MATCH (c:Candidate {candidate_id: $candidate_id})
    MATCH (a:Award {award_id: $award_id})
    MERGE (c)-[r:EARNS_AWARD {
        exam_id: $exam_id,
        award_type: $award_type,
        award_date: $award_date
    }]->(a)
    RETURN r
    """
}

# Trường - Đơn vị quản lý
BELONGS_TO = {
    "type": "BELONGS_TO",
    "create_query": """
    MATCH (s:School {school_id: $school_id})
    MATCH (u:ManagementUnit {unit_id: $unit_id})
    MERGE (s)-[r:BELONGS_TO]->(u)
    RETURN r
    """
}

# Trường - Ngành học
OFFERS_MAJOR = {
    "type": "OFFERS_MAJOR",
    "create_query": """
    MATCH (s:School {school_id: $school_id})
    MATCH (m:Major {major_id: $major_id})
    MERGE (s)-[r:OFFERS_MAJOR {
        start_year: $start_year
    }]->(m)
    RETURN r
    """
}

# Ngành học - Môn học
TEACHES_SUBJECT = {
    "type": "TEACHES_SUBJECT",
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

# Đơn vị - Kỳ thi
ORGANIZES_EXAM = {
    "type": "ORGANIZES_EXAM",
    "create_query": """
    MATCH (u:ManagementUnit {unit_id: $unit_id})
    MATCH (e:Exam {exam_id: $exam_id})
    MERGE (u)-[r:ORGANIZES_EXAM {
        start_date: $start_date,
        end_date: $end_date
    }]->(e)
    RETURN r
    """
}

# Kỳ thi - Môn thi
INCLUDES_SUBJECT = {
    "type": "INCLUDES_SUBJECT",
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

# Kỳ thi - Địa điểm
LOCATED_AT = {
    "type": "LOCATED_AT",
    "create_query": """
    MATCH (e:Exam {exam_id: $exam_id})
    MATCH (l:ExamLocation {location_id: $location_id})
    MERGE (e)-[r:LOCATED_AT]->(l)
    RETURN r
    """
} 