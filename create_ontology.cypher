// Create base classes
CREATE (:Thing {id: 'Thing', name: 'Thing', description: 'Root class for all entities'});
CREATE (:OntologyInstance {id: 'OntologyInstance', name: 'OntologyInstance', description: 'Base class for all entity instances in the knowledge graph'});
CREATE (:OntologyClass {id: 'OntologyClass', name: 'OntologyClass', description: 'Base class for all class definitions in the knowledge graph'});

// Create primary entity classes
CREATE (:Candidate {id: 'Candidate', name: 'Candidate', description: 'Student/candidate information'});
CREATE (:School {id: 'School', name: 'School', description: 'Educational institution'});
CREATE (:Major {id: 'Major', name: 'Major', description: 'Field of study'});
CREATE (:Subject {id: 'Subject', name: 'Subject', description: 'Academic subject'});
CREATE (:Exam {id: 'Exam', name: 'Exam', description: 'Examination event'});
CREATE (:ExamLocation {id: 'ExamLocation', name: 'ExamLocation', description: 'Location where exams are held'});
CREATE (:ExamSchedule {id: 'ExamSchedule', name: 'ExamSchedule', description: 'Schedule for an exam'});
CREATE (:Score {id: 'Score', name: 'Score', description: 'Exam score for a subject'});
CREATE (:ScoreReview {id: 'ScoreReview', name: 'ScoreReview', description: 'Review of an exam score'});
CREATE (:Certificate {id: 'Certificate', name: 'Certificate', description: 'Certificate earned by candidate'});
CREATE (:Recognition {id: 'Recognition', name: 'Recognition', description: 'Formal acknowledgment of achievement'});
CREATE (:Award {id: 'Award', name: 'Award', description: 'Award received in competition'});
CREATE (:Achievement {id: 'Achievement', name: 'Achievement', description: 'General achievement outside exams'});
CREATE (:Degree {id: 'Degree', name: 'Degree', description: 'Higher education degree'});
CREATE (:Credential {id: 'Credential', name: 'Credential', description: 'External credential provided by candidate'});
CREATE (:ExamRoom {id: 'ExamRoom', name: 'ExamRoom', description: 'Room within an exam location where exams are conducted'});
CREATE (:ManagementUnit {id: 'ManagementUnit', name: 'ManagementUnit', description: 'Administrative unit'});

// Create inheritance relationships
MATCH (child:Candidate)
MATCH (parent:Thing)
CREATE (child)-[:IS_A]->(parent);

MATCH (child:School)
MATCH (parent:Thing)
CREATE (child)-[:IS_A]->(parent);

MATCH (child:Major)
MATCH (parent:Thing)
CREATE (child)-[:IS_A]->(parent);

MATCH (child:Subject)
MATCH (parent:Thing)
CREATE (child)-[:IS_A]->(parent);

MATCH (child:Exam)
MATCH (parent:Thing)
CREATE (child)-[:IS_A]->(parent);

MATCH (child:ExamLocation)
MATCH (parent:Thing)
CREATE (child)-[:IS_A]->(parent);

MATCH (child:ExamSchedule)
MATCH (parent:Thing)
CREATE (child)-[:IS_A]->(parent);

MATCH (child:Score)
MATCH (parent:Thing)
CREATE (child)-[:IS_A]->(parent);

MATCH (child:ScoreReview)
MATCH (parent:Thing)
CREATE (child)-[:IS_A]->(parent);

MATCH (child:Certificate)
MATCH (parent:Thing)
CREATE (child)-[:IS_A]->(parent);

MATCH (child:Recognition)
MATCH (parent:Thing)
CREATE (child)-[:IS_A]->(parent);

MATCH (child:Award)
MATCH (parent:Thing)
CREATE (child)-[:IS_A]->(parent);

MATCH (child:Achievement)
MATCH (parent:Thing)
CREATE (child)-[:IS_A]->(parent);

MATCH (child:Degree)
MATCH (parent:Thing)
CREATE (child)-[:IS_A]->(parent);

MATCH (child:Credential)
MATCH (parent:Thing)
CREATE (child)-[:IS_A]->(parent);

MATCH (child:ExamRoom)
MATCH (parent:Thing)
CREATE (child)-[:IS_A]->(parent);

MATCH (child:ManagementUnit)
MATCH (parent:Thing)
CREATE (child)-[:IS_A]->(parent);

// Create relationships between classes
MATCH (c:Candidate), (s:School)
CREATE (c)-[:STUDIES_AT]->(s);

MATCH (c:Candidate), (e:Exam)
CREATE (c)-[:ATTENDS_EXAM]->(e);

MATCH (c:Candidate), (s:Score)
CREATE (c)-[:RECEIVES_SCORE]->(s);

MATCH (c:Candidate), (r:ScoreReview)
CREATE (c)-[:REQUESTS_REVIEW]->(r);

MATCH (c:Candidate), (d:Degree)
CREATE (c)-[:HOLDS_DEGREE]->(d);

MATCH (c:Candidate), (cr:Credential)
CREATE (c)-[:PROVIDES_CREDENTIAL]->(cr);

MATCH (c:Candidate), (cert:Certificate)
CREATE (c)-[:EARNS_CERTIFICATE]->(cert);

MATCH (c:Candidate), (r:Recognition)
CREATE (c)-[:RECEIVES_RECOGNITION]->(r);

MATCH (c:Candidate), (a:Award)
CREATE (c)-[:EARNS_AWARD]->(a);

MATCH (c:Candidate), (a:Achievement)
CREATE (c)-[:ACHIEVES]->(a);

MATCH (s:School), (m:Major)
CREATE (s)-[:OFFERS_MAJOR]->(m);

MATCH (score:Score), (subject:Subject)
CREATE (score)-[:FOR_SUBJECT]->(subject);

MATCH (score:Score), (exam:Exam)
CREATE (score)-[:IN_EXAM]->(exam);

MATCH (e:Exam), (s:Subject)
CREATE (e)-[:INCLUDES_SUBJECT]->(s);

MATCH (e:Exam), (s:ExamSchedule)
CREATE (e)-[:FOLLOWS_SCHEDULE]->(s);

MATCH (e:Exam), (l:ExamLocation)
CREATE (e)-[:HELD_AT]->(l);

MATCH (r:ExamRoom), (l:ExamLocation)
CREATE (r)-[:LOCATED_IN]->(l);

MATCH (d:Degree), (m:Major)
CREATE (d)-[:RELATED_TO]->(m);

MATCH (e:Exam), (m:ManagementUnit)
CREATE (e)-[:ORGANIZED_BY]->(m);

MATCH (d:Degree), (s:School)
CREATE (d)-[:ISSUED_BY]->(s);

MATCH (s:ExamSchedule), (r:ExamRoom)
CREATE (s)-[:ASSIGNED_TO]->(r);

MATCH (s:ExamSchedule), (l:ExamLocation)
CREATE (s)-[:SCHEDULE_AT]->(l);

MATCH (r:ScoreReview), (s:Score)
CREATE (r)-[:REVIEWS]->(s);

// Create relationships between achievement-related classes and Exam
MATCH (a:Award), (e:Exam)
CREATE (a)-[:AWARD_FOR_EXAM]->(e);

MATCH (r:Recognition), (e:Exam)
CREATE (r)-[:RECOGNITION_FOR_EXAM]->(e);

MATCH (a:Achievement), (e:Exam)
CREATE (a)-[:ACHIEVEMENT_FOR_EXAM]->(e);

MATCH (c:Certificate), (e:Exam)
CREATE (c)-[:CERTIFICATE_FOR_EXAM]->(e); 