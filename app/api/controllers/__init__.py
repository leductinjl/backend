"""
Controllers initialization module.

This module imports all API routers to make them available for inclusion in main.py.
Each router handles a specific domain of endpoints such as candidates, exams, schools, etc.
"""

# Import all routers
from app.api.controllers import candidate_router
from app.api.controllers import admin_router
from app.api.controllers import admin_auth
from app.api.controllers import health_router

# TODO: Uncomment these imports when the modules are created
# from app.api.controllers import exam_router
# from app.api.controllers import school_router 