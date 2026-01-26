"""
Tenant Module Interfaces

Abstract contracts for tenant data access.
"""

from .tenant_repository import ITenantRepository
from .membership_repository import IMembershipRepository
from .invitation_repository import IInvitationRepository

__all__ = [
    "ITenantRepository",
    "IMembershipRepository",
    "IInvitationRepository",
]
