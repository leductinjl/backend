// Query to visualize ontology graph excluding Thing node
MATCH (n)
WHERE NOT n:Thing
MATCH (n)-[r]->(m)
WHERE NOT m:Thing
RETURN n, r, m;

// Alternative query with more details
MATCH (n)
WHERE NOT n:Thing
MATCH (n)-[r]->(m)
WHERE NOT m:Thing
RETURN n.id as Source, type(r) as Relationship, m.id as Target;

// Query to see all nodes and their properties
MATCH (n)
WHERE NOT n:Thing
RETURN n.id as Node, n.name as Name, n.description as Description;

// Query to see all relationship types
MATCH (n)-[r]->(m)
WHERE NOT n:Thing AND NOT m:Thing
RETURN DISTINCT type(r) as RelationshipType; 