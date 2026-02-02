"""
Decision API Module

FastAPI routes for rules and decisions.
"""

from .routes import router as decision_router
from .dependencies import init_decision_dependencies

__all__ = ["decision_router", "init_decision_dependencies"]
