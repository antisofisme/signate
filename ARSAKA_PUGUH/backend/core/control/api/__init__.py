"""
Control API Module
"""

from .routes import router as control_router
from .dependencies import init_control_dependencies

__all__ = ["control_router", "init_control_dependencies"]
