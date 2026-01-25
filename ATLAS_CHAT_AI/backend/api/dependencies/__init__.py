"""
FastAPI Dependencies.
"""

from .context import get_context, get_tenant_config

__all__ = [
    "get_context",
    "get_tenant_config",
]
