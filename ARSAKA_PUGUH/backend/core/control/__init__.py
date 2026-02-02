"""
Control Module - Audit, Events, and Metrics

Source: PUGUH UI_API_MAPPING.md - Control Domain
All endpoints are READ-ONLY.
"""

from .api.routes import router as control_router
from .api.dependencies import init_control_dependencies

__all__ = ["control_router", "init_control_dependencies"]
