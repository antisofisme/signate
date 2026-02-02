"""
Decision Module - Rules and Decisions Management

This module handles rules and decisions for ARSAKA_PUGUH SaaS platform:
- Rule CRUD (create draft, view, activate)
- Rule version history
- Decision history (read-only)
- Decision events

Source: PUGUH UI_API_MAPPING.md - Decision Domain
"""

from .api.routes import router as decision_router
from .api.dependencies import init_decision_dependencies

__all__ = [
    "decision_router",
    "init_decision_dependencies",
]
