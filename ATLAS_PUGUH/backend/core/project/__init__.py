"""
Project Module

Project management within tenants following Clean Architecture.
Provides resource isolation below tenant level.
"""

from .api.routes import router as project_router
from .api.dependencies import init_project_dependencies

__all__ = [
    "project_router",
    "init_project_dependencies",
]
