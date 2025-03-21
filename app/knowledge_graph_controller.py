"""
Knowledge Graph API controller module.

This module defines API endpoints for querying the knowledge graph.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from app.infrastructure.ontology.neo4j_connection import get_neo4j
import logging

router = APIRouter(prefix="/api/v1/knowledge-graph", tags=["Knowledge Graph"])

logger = logging.getLogger(__name__)

@router.get("/overview")
async def get_graph_overview(
    limit: int = Query(100, description="Maximum number of nodes to return"),
    neo4j = Depends(get_neo4j)
):
    """
    Get an overview of the knowledge graph.
    
    Returns nodes and relationships in the graph, limited to the specified number.
    """
    try:
        # Query to get nodes and relationships with limit
        query = """
        MATCH (n)
        OPTIONAL MATCH (n)-[r]->(m)
        RETURN n, r, m
        LIMIT $limit
        """
        
        # Execute the query
        result = await neo4j.execute_query(query, {"limit": limit})
        
        # Format the response
        nodes = {}
        relationships = []
        
        # Process results
        for record in result:
            # Process source node
            if record[0] and record[0].id not in nodes:
                node_data = dict(record[0].items())
                node_type = list(record[0].labels)[0]  # Get the first label
                nodes[record[0].id] = {
                    "id": record[0].id,
                    "type": node_type,
                    "properties": node_data
                }
            
            # Process relationship and target node
            if record[1] and record[2]:
                # Add target node if not already added
                if record[2].id not in nodes:
                    node_data = dict(record[2].items())
                    node_type = list(record[2].labels)[0]  # Get the first label
                    nodes[record[2].id] = {
                        "id": record[2].id,
                        "type": node_type,
                        "properties": node_data
                    }
                
                # Add relationship
                rel_data = dict(record[1].items())
                rel_type = record[1].type
                relationships.append({
                    "id": f"{record[0].id}-{rel_type}-{record[2].id}",
                    "source": record[0].id,
                    "target": record[2].id,
                    "type": rel_type,
                    "properties": rel_data
                })
        
        # Prepare final response
        response = {
            "nodes": list(nodes.values()),
            "relationships": relationships,
            "total_nodes": len(nodes),
            "total_relationships": len(relationships)
        }
        
        return response
    except Exception as e:
        logger.error(f"Error getting graph overview: {e}")
        raise HTTPException(status_code=500, detail="Error getting graph overview")

@router.get("/candidates/{candidate_id}")
async def get_candidate_graph(
    candidate_id: str,
    include_education: bool = Query(True, description="Include education history"),
    include_exams: bool = Query(True, description="Include exam history"),
    include_certificates: bool = Query(True, description="Include certificates"),
    include_achievements: bool = Query(True, description="Include achievements"),
    neo4j = Depends(get_neo4j)
):
    """
    Get a candidate's knowledge graph.
    
    Returns a subgraph centered around the specified candidate,
    including connected nodes and relationships.
    """
    try:
        # Build the query based on what to include
        parts = [
            "MATCH (c:Candidate {candidate_id: $candidate_id})",
            "OPTIONAL MATCH (c)-[r:IS_A]->(t:Thing)",
        ]
        
        if include_education:
            parts.append("OPTIONAL MATCH (c)-[r1:STUDIES_AT]->(s:School)")
            parts.append("OPTIONAL MATCH (c)-[r2:HOLDS_DEGREE]->(d:Degree)")
            parts.append("OPTIONAL MATCH (d)-[r3:RELATED_TO]->(m:Major)")
        
        if include_exams:
            parts.append("OPTIONAL MATCH (c)-[r4:ATTENDS_EXAM]->(e:Exam)")
            parts.append("OPTIONAL MATCH (c)-[r5:RECEIVES_SCORE]->(sc:Score)")
            parts.append("OPTIONAL MATCH (sc)-[r6:FOR_SUBJECT]->(sub:Subject)")
            parts.append("OPTIONAL MATCH (sc)-[r7:IN_EXAM]->(e2:Exam)")
        
        if include_certificates:
            parts.append("OPTIONAL MATCH (c)-[r8:EARNS_CERTIFICATE]->(cert:Certificate)")
        
        if include_achievements:
            parts.append("OPTIONAL MATCH (c)-[r9:EARNS_AWARD]->(a:Award)")
            parts.append("OPTIONAL MATCH (c)-[r10:ACHIEVES]->(ach:Achievement)")
        
        # Collect all nodes and relationships
        parts.append("RETURN c, t, r")
        
        if include_education:
            parts.append(", s, r1, d, r2, m, r3")
        
        if include_exams:
            parts.append(", e, r4, sc, r5, sub, r6, e2, r7")
        
        if include_certificates:
            parts.append(", cert, r8")
        
        if include_achievements:
            parts.append(", a, r9, ach, r10")
        
        query = "\n".join(parts)
        
        # Execute the query
        result = await neo4j.execute_query(query, {"candidate_id": candidate_id})
        
        if not result or not result[0][0]:
            raise HTTPException(status_code=404, detail=f"Candidate {candidate_id} not found")
        
        # Format the result into a graph structure
        candidate_node = result[0][0]
        
        # Format the response (simplified for this example)
        # In a real application, you'd transform the Neo4j result into a proper graph structure
        response = {
            "id": candidate_node.get("candidate_id"),
            "name": candidate_node.get("full_name"),
            "properties": {k: v for k, v in candidate_node.items() if k not in ["candidate_id", "full_name"]},
            "connected_nodes": []
        }
        
        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error querying knowledge graph: {e}")
        raise HTTPException(status_code=500, detail="Error querying knowledge graph")

@router.get("/search")
async def search_knowledge_graph(
    query: str = Query(..., description="Search query text"),
    node_types: str = Query(None, description="Comma-separated list of node types to search (e.g., 'Candidate,School,Exam')"),
    limit: int = Query(20, description="Maximum number of results to return"),
    neo4j = Depends(get_neo4j)
):
    """
    Search the knowledge graph.
    
    Performs a text search across nodes in the graph, optionally filtered by node type.
    """
    try:
        # Parse node types if provided
        node_labels = []
        if node_types:
            node_labels = [label.strip() for label in node_types.split(",")]
        
        # Build the query
        cypher_query = """
        MATCH (n)
        WHERE 
        """
        
        # Add node type filter if specified
        if node_labels:
            label_conditions = " OR ".join([f"n:{label}" for label in node_labels])
            cypher_query += f"({label_conditions}) AND "
        
        # Add text search condition - search in name, full_name, and any other relevant text properties
        cypher_query += """
            (
                toLower(toString(n.name)) CONTAINS toLower($search_text) OR
                toLower(toString(n.full_name)) CONTAINS toLower($search_text) OR
                toLower(toString(n.description)) CONTAINS toLower($search_text)
            )
        RETURN n
        LIMIT $limit
        """
        
        # Execute the query
        result = await neo4j.execute_query(
            cypher_query, 
            {
                "search_text": query,
                "limit": limit
            }
        )
        
        # Format the results
        nodes = []
        for record in result:
            if record[0]:
                node = record[0]
                node_data = dict(node.items())
                node_type = list(node.labels)[0]  # Get first label
                
                # Get name from appropriate field
                name = node_data.get("name") or node_data.get("full_name") or node_data.get(f"{node_type.lower()}_name")
                
                nodes.append({
                    "id": node.id,
                    "type": node_type,
                    "name": name,
                    "properties": node_data
                })
        
        return {
            "query": query,
            "node_types": node_labels if node_labels else "All",
            "count": len(nodes),
            "results": nodes
        }
    except Exception as e:
        logger.error(f"Error searching knowledge graph: {e}")
        raise HTTPException(status_code=500, detail="Error searching knowledge graph") 