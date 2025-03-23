"""
Certificate Graph Repository module.

This module provides methods for interacting with Certificate nodes in Neo4j.
"""

from app.domain.graph_models.certificate_node import CertificateNode
from app.infrastructure.ontology.ontology import RELATIONSHIPS

# Import specific relationships
EARNS_CERTIFICATE_REL = RELATIONSHIPS["EARNS_CERTIFICATE"]["type"]
CERTIFICATE_FOR_EXAM_REL = RELATIONSHIPS["CERTIFICATE_FOR_EXAM"]["type"]
INSTANCE_OF_REL = RELATIONSHIPS["INSTANCE_OF"]["type"]

class CertificateGraphRepository:
    """
    Repository for managing Certificate nodes in Neo4j knowledge graph.
    
    This class provides methods to create, update, and query Certificate nodes
    and their relationships with other entities in the knowledge graph.
    """
    
    def __init__(self, neo4j_connection):
        """Initialize with Neo4j connection."""
        self.neo4j = neo4j_connection
    
    async def create_or_update(self, certificate):
        """
        Create or update a Certificate node in Neo4j.
        
        Args:
            certificate: CertificateNode object or dictionary with certificate data
            
        Returns:
            bool: True if operation successful, False otherwise
        """
        try:
            # Ensure we have a dictionary
            params = certificate.to_dict() if hasattr(certificate, 'to_dict') else certificate
            
            # Execute Cypher query to create/update certificate
            query = CertificateNode.create_query()
            result = await self.neo4j.execute_query(query, params)
            
            # Create relationships if possible
            if result and len(result) > 0:
                # Create INSTANCE_OF relationship with Certificate class
                await self._create_instance_of_relationship(params.get('certificate_id'))
                
                if hasattr(certificate, 'create_relationships_query'):
                    rel_query = certificate.create_relationships_query()
                    await self.neo4j.execute_query(rel_query, params)
                return True
            return False
        except Exception as e:
            print(f"Error creating/updating certificate in Neo4j: {e}")
            return False
    
    async def _create_instance_of_relationship(self, certificate_id):
        """
        Tạo mối quan hệ INSTANCE_OF giữa node instance và class node tương ứng.
        
        Args:
            certificate_id: ID của node instance
        """
        try:
            query = CertificateNode.create_instance_of_relationship_query()
            await self.neo4j.execute_query(query, {"certificate_id": certificate_id})
            print(f"Created INSTANCE_OF relationship for certificate {certificate_id}")
        except Exception as e:
            print(f"Error creating INSTANCE_OF relationship for certificate {certificate_id}: {e}")
            raise
    
    async def get_by_id(self, certificate_id):
        """
        Get a certificate by ID.
        
        Args:
            certificate_id: The ID of the certificate to retrieve
            
        Returns:
            CertificateNode or None if not found
        """
        query = """
        MATCH (c:Certificate {certificate_id: $certificate_id})
        RETURN c
        """
        params = {"certificate_id": certificate_id}
        
        result = await self.neo4j.execute_query(query, params)
        if result and len(result) > 0:
            return CertificateNode.from_record({"c": result[0][0]})
        return None
    
    async def delete(self, certificate_id):
        """
        Delete a certificate from Neo4j.
        
        Args:
            certificate_id: ID of the certificate to delete
            
        Returns:
            bool: True if successful, False otherwise
        """
        query = """
        MATCH (c:Certificate {certificate_id: $certificate_id})
        DETACH DELETE c
        """
        params = {"certificate_id": certificate_id}
        
        try:
            await self.neo4j.execute_query(query, params)
            return True
        except Exception as e:
            print(f"Error deleting certificate from Neo4j: {e}")
            return False
    
    async def get_by_candidate(self, candidate_id):
        """
        Get all certificates earned by a candidate.
        
        Args:
            candidate_id: ID of the candidate
            
        Returns:
            List of certificates
        """
        query = f"""
        MATCH (c:Candidate {{candidate_id: $candidate_id}})-[:{EARNS_CERTIFICATE_REL}]->(cert:Certificate)
        RETURN cert
        """
        params = {"candidate_id": candidate_id}
        
        try:
            result = await self.neo4j.execute_query(query, params)
            certificates = []
            
            for record in result:
                certificate = CertificateNode.from_record({"c": record[0]})
                certificates.append(certificate.to_dict())
            
            return certificates
        except Exception as e:
            print(f"Error getting certificates for candidate: {e}")
            return []
    
    async def get_by_exam(self, exam_id):
        """
        Get all certificates awarded in a specific exam.
        
        Args:
            exam_id: ID of the exam
            
        Returns:
            List of certificates
        """
        query = f"""
        MATCH (cert:Certificate)-[:{CERTIFICATE_FOR_EXAM_REL}]->(e:Exam {{exam_id: $exam_id}})
        RETURN cert
        """
        params = {"exam_id": exam_id}
        
        try:
            result = await self.neo4j.execute_query(query, params)
            certificates = []
            
            for record in result:
                certificate = CertificateNode.from_record({"c": record[0]})
                certificates.append(certificate.to_dict())
            
            return certificates
        except Exception as e:
            print(f"Error getting certificates for exam: {e}")
            return []
    
    async def get_by_certificate_number(self, certificate_number):
        """
        Get a certificate by its unique certificate number.
        
        Args:
            certificate_number: Unique certificate number
            
        Returns:
            CertificateNode or None if not found
        """
        query = """
        MATCH (c:Certificate {certificate_number: $certificate_number})
        RETURN c
        """
        params = {"certificate_number": certificate_number}
        
        try:
            result = await self.neo4j.execute_query(query, params)
            if result and len(result) > 0:
                return CertificateNode.from_record({"c": result[0][0]})
            return None
        except Exception as e:
            print(f"Error getting certificate by number: {e}")
            return None
    
    async def get_by_organization(self, organization):
        """
        Get all certificates issued by a specific organization.
        
        Args:
            organization: Name of the issuing organization
            
        Returns:
            List of certificates
        """
        query = """
        MATCH (c:Certificate)
        WHERE c.issuing_organization = $organization
        RETURN c
        """
        params = {"organization": organization}
        
        try:
            result = await self.neo4j.execute_query(query, params)
            certificates = []
            
            for record in result:
                certificate = CertificateNode.from_record({"c": record[0]})
                certificates.append(certificate.to_dict())
            
            return certificates
        except Exception as e:
            print(f"Error getting certificates by organization: {e}")
            return []
    
    async def get_all_certificates(self, limit=100):
        """
        Get all certificates in the knowledge graph.
        
        Args:
            limit: Maximum number of certificates to return
            
        Returns:
            List of certificates
        """
        query = """
        MATCH (c:Certificate)
        RETURN c
        LIMIT $limit
        """
        params = {"limit": limit}
        
        try:
            result = await self.neo4j.execute_query(query, params)
            certificates = []
            
            for record in result:
                certificate = CertificateNode.from_record({"c": record[0]})
                certificates.append(certificate.to_dict())
            
            return certificates
        except Exception as e:
            print(f"Error getting all certificates: {e}")
            return [] 