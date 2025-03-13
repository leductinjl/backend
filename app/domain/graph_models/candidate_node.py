class CandidateNode:
    """
    Model cho thí sinh trong Neo4j Knowledge Graph
    """
    
    def __init__(self, candidate_id, full_name, birth_date=None, id_number=None, 
                 phone_number=None, email=None, primary_address=None):
        self.candidate_id = candidate_id
        self.full_name = full_name
        self.birth_date = birth_date
        self.id_number = id_number
        self.phone_number = phone_number
        self.email = email
        self.primary_address = primary_address
        
    @staticmethod
    def create_query():
        """
        Tạo Cypher query để tạo node Candidate
        """
        return """
        MERGE (c:Candidate {candidate_id: $candidate_id}) 
        ON CREATE SET 
            c.full_name = $full_name,
            c.birth_date = $birth_date,
            c.id_number = $id_number,
            c.phone_number = $phone_number,
            c.email = $email,
            c.primary_address = $primary_address
        ON MATCH SET 
            c.full_name = $full_name,
            c.birth_date = $birth_date,
            c.id_number = $id_number,
            c.phone_number = $phone_number,
            c.email = $email,
            c.primary_address = $primary_address
        RETURN c
        """
    
    def to_dict(self):
        """
        Chuyển đổi thành dictionary để sử dụng trong query
        """
        return {
            "candidate_id": self.candidate_id,
            "full_name": self.full_name,
            "birth_date": self.birth_date,
            "id_number": self.id_number,
            "phone_number": self.phone_number,
            "email": self.email,
            "primary_address": self.primary_address
        }
        
    @staticmethod
    def from_record(record):
        """
        Tạo đối tượng CandidateNode từ Neo4j record
        """
        node = record['c']
        return CandidateNode(
            candidate_id=node['candidate_id'],
            full_name=node['full_name'],
            birth_date=node.get('birth_date'),
            id_number=node.get('id_number'),
            phone_number=node.get('phone_number'),
            email=node.get('email'),
            primary_address=node.get('primary_address')
        ) 