from pydantic import BaseModel

class DashboardStats(BaseModel):
    total_candidates: int
    total_exams: int
    total_schools: int 