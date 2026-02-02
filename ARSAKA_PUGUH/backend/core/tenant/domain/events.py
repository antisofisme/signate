"""
Tenant Domain Events

Domain events for tenant operations.
Used for audit logging and cross-module notifications.

Source: INFRA-DEC-007-identity-model.md
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4


@dataclass(kw_only=True)
class DomainEvent:
    """Base domain event."""
    event_id: UUID = field(default_factory=uuid4)
    occurred_at: datetime = field(default_factory=datetime.utcnow)
    actor_user_id: Optional[UUID] = None  # Who triggered the event


# Tenant Events

@dataclass
class TenantCreatedEvent(DomainEvent):
    """Tenant was created."""
    tenant_id: UUID = None
    name: str = ""
    owner_user_id: UUID = None
    plan: str = "free"


@dataclass
class TenantUpdatedEvent(DomainEvent):
    """Tenant was updated."""
    tenant_id: UUID = None
    changes: dict = field(default_factory=dict)  # {field: {old, new}}


@dataclass
class TenantDeletedEvent(DomainEvent):
    """Tenant was deleted (soft delete)."""
    tenant_id: UUID = None
    deleted_by_user_id: UUID = None


@dataclass
class TenantPlanChangedEvent(DomainEvent):
    """Tenant subscription plan changed."""
    tenant_id: UUID = None
    old_plan: str = ""
    new_plan: str = ""


@dataclass
class TenantSuspendedEvent(DomainEvent):
    """Tenant was suspended."""
    tenant_id: UUID = None
    reason: Optional[str] = None


# Membership Events

@dataclass
class MemberAddedEvent(DomainEvent):
    """Member was added to tenant."""
    tenant_id: UUID = None
    user_id: UUID = None
    role: str = ""
    added_via: str = "direct"  # direct | invitation


@dataclass
class MemberRemovedEvent(DomainEvent):
    """Member was removed from tenant."""
    tenant_id: UUID = None
    user_id: UUID = None
    removed_by_user_id: UUID = None
    reason: Optional[str] = None


@dataclass
class MemberRoleChangedEvent(DomainEvent):
    """Member's role was changed."""
    tenant_id: UUID = None
    user_id: UUID = None
    old_role: str = ""
    new_role: str = ""


@dataclass
class MemberSuspendedEvent(DomainEvent):
    """Member was suspended."""
    tenant_id: UUID = None
    user_id: UUID = None
    reason: Optional[str] = None


# Invitation Events

@dataclass
class InvitationSentEvent(DomainEvent):
    """Invitation was sent."""
    invitation_id: UUID = None
    tenant_id: UUID = None
    email: str = ""
    role: str = ""


@dataclass
class InvitationAcceptedEvent(DomainEvent):
    """Invitation was accepted."""
    invitation_id: UUID = None
    tenant_id: UUID = None
    user_id: UUID = None


@dataclass
class InvitationRejectedEvent(DomainEvent):
    """Invitation was rejected."""
    invitation_id: UUID = None
    tenant_id: UUID = None
    email: str = ""


@dataclass
class InvitationCancelledEvent(DomainEvent):
    """Invitation was cancelled by admin."""
    invitation_id: UUID = None
    tenant_id: UUID = None
    cancelled_by_user_id: UUID = None


@dataclass
class InvitationExpiredEvent(DomainEvent):
    """Invitation expired."""
    invitation_id: UUID = None
    tenant_id: UUID = None
    email: str = ""
