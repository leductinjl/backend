"""
Neo4j Ontology package.

This package provides functionality for working with the Neo4j knowledge graph,
including connection handling, ontology definition, and initialization.
"""

from app.infrastructure.ontology.neo4j_connection import neo4j_connection, get_neo4j
from app.infrastructure.ontology.initialization import initialize_ontology

__all__ = ['neo4j_connection', 'get_neo4j', 'initialize_ontology'] 