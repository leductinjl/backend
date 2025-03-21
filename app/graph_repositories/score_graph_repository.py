"""
Score Graph Repository module.

This module provides methods for interacting with Score nodes in Neo4j.
"""

from app.domain.graph_models.score_node import ScoreNode
from app.infrastructure.ontology.ontology import RELATIONSHIPS

class ScoreGraphRepository:
    """
    Repository for managing Score nodes in Neo4j knowledge graph.
    
    This class provides methods to create, update, and query Score nodes
    and their relationships with other entities in the knowledge graph.
    """
    
    def __init__(self, neo4j_connection):
        """Initialize with Neo4j connection."""
        self.neo4j = neo4j_connection
    
    async def create_or_update(self, score):
        """
        Create or update a Score node in Neo4j.
        
        Args:
            score: ScoreNode object or dictionary with score data
            
        Returns:
            bool: True if operation successful, False otherwise
        """
        try:
            # Ensure we have a dictionary
            params = score.to_dict() if hasattr(score, 'to_dict') else score
            
            # Execute Cypher query to create/update score
            query = ScoreNode.create_query()
            result = await self.neo4j.execute_query(query, params)
            
            if result and len(result) > 0:
                # Create relationships
                rel_query = ScoreNode.create_relationships_query()
                await self.neo4j.execute_query(rel_query, params)
                return True
            return False
        except Exception as e:
            print(f"Error creating/updating score in Neo4j: {e}")
            return False
    
    async def get_by_id(self, score_id):
        """
        Get a score by ID.
        
        Args:
            score_id: The ID of the score to retrieve
            
        Returns:
            ScoreNode or None if not found
        """
        query = """
        MATCH (s:Score {score_id: $score_id})
        RETURN s
        """
        params = {"score_id": score_id}
        
        result = await self.neo4j.execute_query(query, params)
        if result and len(result) > 0:
            return ScoreNode.from_record({"s": result[0][0]})
        return None
    
    async def delete(self, score_id):
        """
        Delete a score from Neo4j.
        
        Args:
            score_id: ID of the score to delete
            
        Returns:
            bool: True if successful, False otherwise
        """
        query = """
        MATCH (s:Score {score_id: $score_id})
        DETACH DELETE s
        """
        params = {"score_id": score_id}
        
        try:
            await self.neo4j.execute_query(query, params)
            return True
        except Exception as e:
            print(f"Error deleting score from Neo4j: {e}")
            return False
    
    async def get_candidate_scores(self, candidate_id):
        """
        Get all scores for a specific candidate.
        
        Args:
            candidate_id: ID of the candidate
            
        Returns:
            List of scores with subject and exam details
        """
        query = """
        MATCH (c:Candidate {candidate_id: $candidate_id})-[:HAS_SCORE]->(s:Score)
        MATCH (s)-[:FOR_SUBJECT]->(subj:Subject)
        MATCH (s)-[:IN_EXAM]->(e:Exam)
        RETURN s, subj, e
        """
        params = {"candidate_id": candidate_id}
        
        try:
            result = await self.neo4j.execute_query(query, params)
            scores = []
            
            for record in result:
                score = record[0]
                subject = record[1]
                exam = record[2]
                
                scores.append({
                    "score_id": score["score_id"],
                    "score_value": score["score_value"],
                    "score_date": score.get("score_date"),
                    "status": score.get("status"),
                    "subject_id": subject["subject_id"],
                    "subject_name": subject["subject_name"],
                    "exam_id": exam["exam_id"],
                    "exam_name": exam["exam_name"]
                })
            
            return scores
        except Exception as e:
            print(f"Error getting scores for candidate: {e}")
            return []
    
    async def get_exam_scores(self, exam_id):
        """
        Get all scores for a specific exam.
        
        Args:
            exam_id: ID of the exam
            
        Returns:
            List of scores with candidate and subject details
        """
        query = """
        MATCH (e:Exam {exam_id: $exam_id})<-[:IN_EXAM]-(s:Score)
        MATCH (c:Candidate)-[:HAS_SCORE]->(s)
        MATCH (s)-[:FOR_SUBJECT]->(subj:Subject)
        RETURN s, c, subj
        """
        params = {"exam_id": exam_id}
        
        try:
            result = await self.neo4j.execute_query(query, params)
            scores = []
            
            for record in result:
                score = record[0]
                candidate = record[1]
                subject = record[2]
                
                scores.append({
                    "score_id": score["score_id"],
                    "score_value": score["score_value"],
                    "score_date": score.get("score_date"),
                    "status": score.get("status"),
                    "candidate_id": candidate["candidate_id"],
                    "candidate_name": candidate["full_name"],
                    "subject_id": subject["subject_id"],
                    "subject_name": subject["subject_name"]
                })
            
            return scores
        except Exception as e:
            print(f"Error getting scores for exam: {e}")
            return []
    
    async def get_subject_scores(self, subject_id):
        """
        Get all scores for a specific subject.
        
        Args:
            subject_id: ID of the subject
            
        Returns:
            List of scores with candidate and exam details
        """
        query = """
        MATCH (subj:Subject {subject_id: $subject_id})<-[:FOR_SUBJECT]-(s:Score)
        MATCH (c:Candidate)-[:HAS_SCORE]->(s)
        MATCH (s)-[:IN_EXAM]->(e:Exam)
        RETURN s, c, e
        """
        params = {"subject_id": subject_id}
        
        try:
            result = await self.neo4j.execute_query(query, params)
            scores = []
            
            for record in result:
                score = record[0]
                candidate = record[1]
                exam = record[2]
                
                scores.append({
                    "score_id": score["score_id"],
                    "score_value": score["score_value"],
                    "score_date": score.get("score_date"),
                    "status": score.get("status"),
                    "candidate_id": candidate["candidate_id"],
                    "candidate_name": candidate["full_name"],
                    "exam_id": exam["exam_id"],
                    "exam_name": exam["exam_name"]
                })
            
            return scores
        except Exception as e:
            print(f"Error getting scores for subject: {e}")
            return []
    
    async def get_school_average_scores(self, school_id, exam_id=None):
        """
        Get average scores for students from a specific school.
        
        Args:
            school_id: ID of the school
            exam_id: Optional ID of a specific exam to filter by
            
        Returns:
            Dictionary with subject IDs as keys and average scores as values
        """
        query_params = """
        MATCH (school:School {school_id: $school_id})
        MATCH (school)<-[:STUDIES_AT]-(c:Candidate)
        MATCH (c)-[:HAS_SCORE]->(s:Score)
        MATCH (s)-[:FOR_SUBJECT]->(subj:Subject)
        """
        
        if exam_id:
            query_params += """
            MATCH (s)-[:IN_EXAM]->(e:Exam {exam_id: $exam_id})
            """
        
        query_params += """
        RETURN subj.subject_id as subject_id, subj.subject_name as subject_name, 
               AVG(s.score_value) as avg_score,
               COUNT(c) as student_count
        """
        
        params = {"school_id": school_id}
        if exam_id:
            params["exam_id"] = exam_id
        
        try:
            result = await self.neo4j.execute_query(query_params, params)
            averages = []
            
            for record in result:
                subject_id = record[0]
                subject_name = record[1]
                avg_score = record[2]
                student_count = record[3]
                
                averages.append({
                    "subject_id": subject_id,
                    "subject_name": subject_name,
                    "average_score": round(avg_score, 2),
                    "student_count": student_count
                })
            
            return averages
        except Exception as e:
            print(f"Error getting average scores for school: {e}")
            return [] 