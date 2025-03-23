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
        constraints_queries = []
        
        # Thing constraint (root class)
        constraints_queries.append("""
        CREATE CONSTRAINT thing_id IF NOT EXISTS
        FOR (t:Thing) REQUIRE t.id IS UNIQUE
        """)
        
        # Generate class-specific constraints from CLASSES dictionary
        for class_name, class_def in CLASSES.items():
            if class_name == "Thing":
                continue  # Already handled above
                
            # Extract id property name (usually class_name_id)
            id_property = None
            for prop_name in class_def.get("properties", {}).keys():
                if prop_name.endswith("_id") and (prop_name == f"{class_name.lower()}_id" or prop_name == "id"):
                    id_property = prop_name
                    break
            
            if id_property:
                constraints_queries.append(f"""
                CREATE CONSTRAINT {class_name.lower()}_id IF NOT EXISTS
                FOR (c:{class_name}) REQUIRE c.{id_property} IS UNIQUE
                """)
        
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
        
        # Define class nodes based on CLASSES dictionary
        class_nodes = []
        for class_name, class_def in CLASSES.items():
            if class_name == "Thing":
                continue  # Already handled above
                
            class_nodes.append({
                "id": f"{class_name.lower()}-class",
                "name": class_name,
                "description": class_def.get("description", f"Class representing {class_name}")
            })
        
        # Generic class node creation query - using specific label directly in the query
        # And consistently applying both the class-specific label and a common 'OntologyClass' label
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