"""
Tenant Module

Multi-tenant management for ARSAKA_PUGUH SaaS platform.

Structure:
- domain/: Domain entities (Tenant, TenantMembership, Invitation)
- interfaces/: Abstract contracts
- adapters/: PostgreSQL implementations
- use_cases/: Business logic
- api/: FastAPI routes and schemas

Source: INFRA-DEC-007-identity-model.md
"""

from .api.routes import router as tenant_router
from .api.dependencies import init_tenant_dependencies

__all__ = [
    "tenant_router",
    "init_tenant_dependencies",
]
