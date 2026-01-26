"""
ATLAS_PUGUH Backend - Centralized API Routes Definition
Follows PANDAWA Clean Architecture standards (CORE-STD-01)
"""


class APIRoutes:
    """Centralized API route definitions"""

    # API prefix
    PREFIX = "/api/v1"

    # Governance module routes (Control Plane)
    GOVERNANCE = f"{PREFIX}/governance"
    GOVERNANCE_DECISIONS = f"{GOVERNANCE}/decisions"
    GOVERNANCE_RULES = f"{GOVERNANCE}/rules"
    GOVERNANCE_WORKFLOWS = f"{GOVERNANCE}/workflows"
    GOVERNANCE_EVENTS = f"{GOVERNANCE}/events"


routes = APIRoutes()
