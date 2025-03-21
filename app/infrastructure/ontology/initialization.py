"""
Ontology initialization module.

This module provides functions to initialize the knowledge graph ontology in Neo4j.
It creates the base structure, constraints, and indexes needed for the application.
"""

from app.infrastructure.ontology.neo4j_connection import neo4j_connection
from app.infrastructure.ontology.ontology import CLASSES, RELATIONSHIPS
import logging

async def create_constraints_and_indexes():
    """
    Create Neo4j constraints and indexes for efficient queries.
    
    This creates unique constraints for primary identifiers and indexes
    for frequently queried properties.
    """
    try:
        # Create constraints for all node classes
        constraints_queries = [
            # Thing constraint
            """
            CREATE CONSTRAINT thing_id IF NOT EXISTS
            FOR (t:Thing) REQUIRE t.id IS UNIQUE
            """,
            
            # Class-specific constraints
            """
            CREATE CONSTRAINT candidate_id IF NOT EXISTS
            FOR (c:Candidate) REQUIRE c.candidate_id IS UNIQUE
            """,
            
            """
            CREATE CONSTRAINT school_id IF NOT EXISTS
            FOR (s:School) REQUIRE s.school_id IS UNIQUE
            """,
            
            """
            CREATE CONSTRAINT major_id IF NOT EXISTS
            FOR (m:Major) REQUIRE m.major_id IS UNIQUE
            """,
            
            """
            CREATE CONSTRAINT subject_id IF NOT EXISTS
            FOR (s:Subject) REQUIRE s.subject_id IS UNIQUE
            """,
            
            """
            CREATE CONSTRAINT exam_id IF NOT EXISTS
            FOR (e:Exam) REQUIRE e.exam_id IS UNIQUE
            """,
            
            """
            CREATE CONSTRAINT location_id IF NOT EXISTS
            FOR (l:ExamLocation) REQUIRE l.location_id IS UNIQUE
            """,
            
            """
            CREATE CONSTRAINT schedule_id IF NOT EXISTS
            FOR (s:ExamSchedule) REQUIRE s.schedule_id IS UNIQUE
            """,
            
            """
            CREATE CONSTRAINT attempt_id IF NOT EXISTS
            FOR (a:ExamAttempt) REQUIRE a.attempt_id IS UNIQUE
            """,
            
            """
            CREATE CONSTRAINT score_id IF NOT EXISTS
            FOR (s:Score) REQUIRE s.score_id IS UNIQUE
            """,
            
            """
            CREATE CONSTRAINT review_id IF NOT EXISTS
            FOR (r:ScoreReview) REQUIRE r.review_id IS UNIQUE
            """,
            
            """
            CREATE CONSTRAINT history_id IF NOT EXISTS
            FOR (h:ScoreHistory) REQUIRE h.history_id IS UNIQUE
            """,
            
            """
            CREATE CONSTRAINT certificate_id IF NOT EXISTS
            FOR (c:Certificate) REQUIRE c.certificate_id IS UNIQUE
            """,
            
            """
            CREATE CONSTRAINT recognition_id IF NOT EXISTS
            FOR (r:Recognition) REQUIRE r.recognition_id IS UNIQUE
            """,
            
            """
            CREATE CONSTRAINT award_id IF NOT EXISTS
            FOR (a:Award) REQUIRE a.award_id IS UNIQUE
            """,
            
            """
            CREATE CONSTRAINT achievement_id IF NOT EXISTS
            FOR (a:Achievement) REQUIRE a.achievement_id IS UNIQUE
            """,
            
            """
            CREATE CONSTRAINT degree_id IF NOT EXISTS
            FOR (d:Degree) REQUIRE d.degree_id IS UNIQUE
            """,
            
            """
            CREATE CONSTRAINT credential_id IF NOT EXISTS
            FOR (c:Credential) REQUIRE c.credential_id IS UNIQUE
            """,
            
            """
            CREATE CONSTRAINT unit_id IF NOT EXISTS
            FOR (u:ManagementUnit) REQUIRE u.unit_id IS UNIQUE
            """
        ]
        
        # Create indexes for frequently searched properties
        index_queries = [
            # Candidate indexes
            """
            CREATE INDEX candidate_name IF NOT EXISTS
            FOR (c:Candidate) ON (c.full_name)
            """,
            
            """
            CREATE INDEX candidate_email IF NOT EXISTS
            FOR (c:Candidate) ON (c.email)
            """,
            
            # School indexes
            """
            CREATE INDEX school_name IF NOT EXISTS
            FOR (s:School) ON (s.school_name)
            """,
            
            # Exam indexes
            """
            CREATE INDEX exam_name IF NOT EXISTS
            FOR (e:Exam) ON (e.exam_name)
            """,
            
            """
            CREATE INDEX exam_date IF NOT EXISTS
            FOR (e:Exam) ON (e.start_date)
            """
        ]
        
        # Execute all constraint queries
        for query in constraints_queries:
            await neo4j_connection.execute_query(query)
            
        # Execute all index queries
        for query in index_queries:
            await neo4j_connection.execute_query(query)
            
        logging.info("Neo4j constraints and indexes created successfully")
    except Exception as e:
        logging.error(f"Error creating Neo4j constraints and indexes: {e}")
        raise

async def create_base_nodes():
    """
    Create all base nodes representing the ontology classes.
    """
    try:
        # Create Thing node with name (root of the ontology)
        thing_query = """
        MERGE (t:Thing {id: $id})
        ON CREATE SET
            t.name = $name,
            t.description = $description,
            t.created_at = datetime(),
            t.updated_at = datetime()
        ON MATCH SET
            t.name = $name,
            t.description = $description,
            t.updated_at = datetime()
        RETURN t
        """
        
        thing_params = {
            "id": "thing-root",
            "name": "Thing",
            "description": "Root node representing any entity in the ontology"
        }
        
        await neo4j_connection.execute_query(thing_query, thing_params)
        logging.info("Created Thing node")
        
        # Define class nodes to create
        class_nodes = [
            {
                "id": "candidate-class",
                "name": "Candidate",
                "description": "Class representing candidate/student information"
            },
            {
                "id": "school-class",
                "name": "School",
                "description": "Educational institution"
            },
            {
                "id": "major-class",
                "name": "Major",
                "description": "Field of study"
            },
            {
                "id": "subject-class",
                "name": "Subject",
                "description": "Academic subject"
            },
            {
                "id": "exam-class",
                "name": "Exam",
                "description": "Examination"
            },
            {
                "id": "examlocation-class",
                "name": "ExamLocation",
                "description": "Location where exams are held"
            },
            {
                "id": "examroom-class",
                "name": "ExamRoom",
                "description": "Room within an exam location"
            },
            {
                "id": "examschedule-class",
                "name": "ExamSchedule",
                "description": "Schedule for an exam and subject"
            },
            {
                "id": "score-class",
                "name": "Score",
                "description": "Exam score for a subject"
            },
            {
                "id": "certificate-class",
                "name": "Certificate",
                "description": "Certificate earned by candidate"
            },
            {
                "id": "award-class",
                "name": "Award",
                "description": "Award received in competition"
            },
            {
                "id": "degree-class",
                "name": "Degree",
                "description": "Higher education degree"
            },
            {
                "id": "achievement-class",
                "name": "Achievement",
                "description": "Achievement or accomplishment by a candidate"
            },
            {
                "id": "credential-class",
                "name": "Credential",
                "description": "Authentication credential for a candidate"
            },
            {
                "id": "examattempt-class",
                "name": "ExamAttempt",
                "description": "An attempt by a candidate to take an exam"
            },
            {
                "id": "managementunit-class",
                "name": "ManagementUnit",
                "description": "Organization unit managing educational entities"
            },
            {
                "id": "recognition-class",
                "name": "Recognition",
                "description": "Formal acknowledgment of accomplishment"
            },
            {
                "id": "scorehistory-class",
                "name": "ScoreHistory",
                "description": "History of changes to a score"
            },
            {
                "id": "scorereview-class",
                "name": "ScoreReview",
                "description": "Review process for a contested score"
            }
        ]
        
        # Generic class node creation query - now using specific label directly in the query
        # And consistently applying both the class-specific label and a common 'OntologyClass' label
        # Using positional parameter $1, $2, etc. to avoid confusion with $ label syntax
        for node in class_nodes:
            # Create class node
            class_query = f"""
            MERGE (c:{node['name']}:OntologyClass {{id: $id}})
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
            
            class_params = {
                "id": node["id"],
                "name": node["name"],
                "description": node["description"]
            }
            
            await neo4j_connection.execute_query(class_query, class_params)
            logging.info(f"Created {node['name']} class node")
            
            # Create relationship to Thing - finding node by id to ensure consistency
            is_a_query = """
            MATCH (c:OntologyClass {id: $child_id})
            MATCH (t:Thing {id: $parent_id})
            MERGE (c)-[r:IS_A]->(t)
            RETURN r
            """
            
            is_a_params = {
                "child_id": node["id"],
                "parent_id": "thing-root"
            }
            
            await neo4j_connection.execute_query(is_a_query, is_a_params)
            logging.info(f"Created IS_A relationship for {node['name']}")
        
        logging.info("Created all base ontology nodes")
    except Exception as e:
        logging.error(f"Error creating base nodes: {e}")
        raise

async def initialize_ontology():
    """
    Initialize the complete ontology structure.
    
    This function is called during application startup to ensure
    the Neo4j database has the correct ontology structure.
    """
    try:
        logging.info("Initializing Neo4j ontology...")
        await create_constraints_and_indexes()
        await create_base_nodes()
        logging.info("Neo4j ontology initialized successfully")
    except Exception as e:
        logging.error(f"Error initializing Neo4j ontology: {e}")
        raise 