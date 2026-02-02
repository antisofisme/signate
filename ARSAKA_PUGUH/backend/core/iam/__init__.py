"""
IAM Module - Identity and Access Management

This module handles IAM for ARSAKA_PUGUH SaaS platform:
- User listing and roles (via existing users/tenant_members tables)
- Role management (custom roles per tenant)
- Permission matrix
- Service account management

Source: PUGUH UI_API_MAPPING.md - IAM Domain
"""

from .api.routes import router as iam_router
from .api.dependencies import init_iam_dependencies

__all__ = [
    "iam_router",
    "init_iam_dependencies",
]
