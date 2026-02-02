"""
Project API Layer

FastAPI routes and schemas.
"""

from .routes import router as project_router
from .dependencies import init_project_dependencies

__all__ = [
    "project_router",
    "init_project_dependencies",
]
