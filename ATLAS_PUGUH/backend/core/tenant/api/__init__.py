"""
Tenant API Module

FastAPI routes and schemas for tenant management.
"""

from .routes import router
from .dependencies import init_tenant_dependencies

__all__ = [
    "router",
    "init_tenant_dependencies",
]
