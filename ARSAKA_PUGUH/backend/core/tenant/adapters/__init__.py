"""
Tenant Module Adapters

PostgreSQL implementations of repository interfaces.
"""

from .tenant_repository import PostgresTenantRepository
from .membership_repository import PostgresMembershipRepository
from .invitation_repository import PostgresInvitationRepository

__all__ = [
    "PostgresTenantRepository",
    "PostgresMembershipRepository",
    "PostgresInvitationRepository",
]
