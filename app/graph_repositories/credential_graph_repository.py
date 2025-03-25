"""
Credential Graph Repository module.

This module provides methods for interacting with Credential nodes in Neo4j.
"""

from app.domain.graph_models.credential_node import CredentialNode, PROVIDES_CREDENTIAL_REL, INSTANCE_OF_REL
from app.infrastructure.ontology.ontology import RELATIONSHIPS

class CredentialGraphRepository:
    """
    Repository for managing Credential nodes in Neo4j knowledge graph.
    
    This class provides methods to create, update, and query Credential nodes
    and their relationships with other entities in the knowledge graph.
    """
    
    def __init__(self, neo4j_connection):
        """Initialize with Neo4j connection."""
        self.neo4j = neo4j_connection
    
    async def create_or_update(self, credential):
        """
        Create or update a Credential node in Neo4j.
        
        Args:
            credential: CredentialNode object or dictionary with credential data
            
        Returns:
            bool: True if operation successful, False otherwise
        """
        try:
            # Ensure we have a dictionary
            params = credential.to_dict() if hasattr(credential, 'to_dict') else credential
            
            # Execute Cypher query to create/update credential
            query = CredentialNode.create_query()
            result = await self.neo4j.execute_query(query, params)
            
            # Create INSTANCE_OF relationship only
            if result and len(result) > 0:
                # Create INSTANCE_OF relationship with Credential class
                await self._create_instance_of_relationship(params.get('credential_id'))
                return True
            return False
        except Exception as e:
            print(f"Error creating/updating credential in Neo4j: {e}")
            return False
    
    async def _create_instance_of_relationship(self, credential_id):
        """
        Tạo mối quan hệ INSTANCE_OF giữa node instance và class node tương ứng.
        
        Args:
            credential_id: ID của node instance
        """
        try:
            query = CredentialNode.create_instance_of_relationship_query()
            await self.neo4j.execute_query(query, {"credential_id": credential_id})
            print(f"Created INSTANCE_OF relationship for credential {credential_id}")
        except Exception as e:
            print(f"Error creating INSTANCE_OF relationship for credential {credential_id}: {e}")
            raise
    
    async def get_by_id(self, credential_id):
        """
        Get a credential by ID.
        
        Args:
            credential_id: The ID of the credential to retrieve
            
        Returns:
            CredentialNode or None if not found
        """
        query = """
        MATCH (c:Credential {credential_id: $credential_id})
        RETURN c
        """
        params = {"credential_id": credential_id}
        
        result = await self.neo4j.execute_query(query, params)
        if result and len(result) > 0:
            return CredentialNode.from_record({"c": result[0][0]})
        return None
    
    async def delete(self, credential_id):
        """
        Delete a credential from Neo4j.
        
        Args:
            credential_id: ID of the credential to delete
            
        Returns:
            bool: True if successful, False otherwise
        """
        query = """
        MATCH (c:Credential {credential_id: $credential_id})
        DETACH DELETE c
        """
        params = {"credential_id": credential_id}
        
        try:
            await self.neo4j.execute_query(query, params)
            return True
        except Exception as e:
            print(f"Error deleting credential from Neo4j: {e}")
            return False
    
    async def get_by_candidate(self, candidate_id):
        """
        Get all credentials for a candidate.
        
        Args:
            candidate_id: ID of the candidate
            
        Returns:
            List of credentials
        """
        query = f"""
        MATCH (ca:Candidate {{candidate_id: $candidate_id}})-[:{PROVIDES_CREDENTIAL_REL}]->(c:Credential)
        RETURN c
        """
        params = {"candidate_id": candidate_id}
        
        try:
            result = await self.neo4j.execute_query(query, params)
            credentials = []
            
            for record in result:
                credential = CredentialNode.from_record({"c": record[0]})
                credentials.append(credential.to_dict())
            
            return credentials
        except Exception as e:
            print(f"Error getting credentials for candidate: {e}")
            return []
    
    async def get_by_credential_type(self, credential_type):
        """
        Get all credentials of a specific type.
        
        Args:
            credential_type: Type of credentials to retrieve
            
        Returns:
            List of credentials
        """
        query = """
        MATCH (c:Credential)
        WHERE c.credential_type = $credential_type
        RETURN c
        """
        params = {"credential_type": credential_type}
        
        try:
            result = await self.neo4j.execute_query(query, params)
            credentials = []
            
            for record in result:
                credential = CredentialNode.from_record({"c": record[0]})
                credentials.append(credential.to_dict())
            
            return credentials
        except Exception as e:
            print(f"Error getting credentials by type: {e}")
            return []
    
    async def get_by_organization(self, organization):
        """
        Get all credentials issued by a specific organization.
        
        Args:
            organization: Name of the issuing organization
            
        Returns:
            List of credentials
        """
        query = """
        MATCH (c:Credential)
        WHERE c.issuing_organization = $organization
        RETURN c
        """
        params = {"organization": organization}
        
        try:
            result = await self.neo4j.execute_query(query, params)
            credentials = []
            
            for record in result:
                credential = CredentialNode.from_record({"c": record[0]})
                credentials.append(credential.to_dict())
            
            return credentials
        except Exception as e:
            print(f"Error getting credentials by organization: {e}")
            return []
    
    async def get_all_credentials(self, limit=100):
        """
        Get all credentials in the knowledge graph.
        
        Args:
            limit: Maximum number of credentials to return
            
        Returns:
            List of credentials
        """
        query = """
        MATCH (c:Credential)
        RETURN c
        LIMIT $limit
        """
        params = {"limit": limit}
        
        try:
            result = await self.neo4j.execute_query(query, params)
            credentials = []
            
            for record in result:
                credential = CredentialNode.from_record({"c": record[0]})
                credentials.append(credential.to_dict())
            
            return credentials
        except Exception as e:
            print(f"Error getting all credentials: {e}")
            return []

    async def add_belongs_to_relationship(self, credential_id, candidate_id):
        """
        Create a relationship between a credential and a candidate.
        
        Args:
            credential_id: ID of the credential
            candidate_id: ID of the candidate
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            query = """
            MATCH (cred:Credential {credential_id: $credential_id})
            MATCH (cand:Candidate {candidate_id: $candidate_id})
            MERGE (cand)-[r:PROVIDES_CREDENTIAL]->(cred)
            RETURN r
            """
            
            params = {
                "credential_id": credential_id,
                "candidate_id": candidate_id
            }
            
            await self.neo4j.execute_query(query, params)
            print(f"Added PROVIDES_CREDENTIAL relationship between Candidate {candidate_id} and Credential {credential_id}")
            return True
        except Exception as e:
            print(f"Error adding PROVIDES_CREDENTIAL relationship: {e}")
            return False

    async def add_issued_by_relationship(self, credential_id, organization_id):
        """
        Create a relationship between a credential and an organization.
        
        Args:
            credential_id: ID of the credential
            organization_id: ID of the organization
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            query = """
            MATCH (cred:Credential {credential_id: $credential_id})
            MATCH (org:Organization {organization_id: $organization_id})
            MERGE (cred)-[r:ISSUED_BY]->(org)
            RETURN r
            """
            
            params = {
                "credential_id": credential_id,
                "organization_id": organization_id
            }
            
            await self.neo4j.execute_query(query, params)
            print(f"Added ISSUED_BY relationship between Credential {credential_id} and Organization {organization_id}")
            return True
        except Exception as e:
            print(f"Error adding ISSUED_BY relationship: {e}")
            return False 